"""Local review/apply journal. Candidate code is never executed here.

Per-file replacements are atomic, but there is no filesystem-wide transaction
or external-writer lock. Rechecks narrow (do not eliminate) the final-write race.
"""
from __future__ import annotations
import base64
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import stat
import threading
import uuid
from contextlib import contextmanager

MAX_BYTES = 2 * 1024 * 1024

class ReviewError(ValueError):
    pass

class Connection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def encode(data):
    return base64.b64encode(data).decode('ascii')

def decode(data):
    return base64.b64decode(data, validate=True)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

@contextmanager
def directory(path):
    """Reject symlink ancestors and anchor an explicitly permitted directory.

    Opening each filesystem ancestor would require broader sandbox read access.
    Metadata checks and final no-follow opens preserve static path protections;
    the separate inode/rechecks narrow the documented external-writer race.
    """
    path = Path(path)
    if not path.is_absolute():
        raise ReviewError('Expected an absolute project path.')
    for node in (path, *path.parents):
        if stat.S_ISLNK(os.lstat(node).st_mode):
            raise ReviewError('Symlink directory paths are not supported.')
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        yield fd
    finally:
        os.close(fd)

def relative_path(relative):
    path = PurePosixPath(relative)
    if not relative or path.is_absolute() or any(p in ('.', '..') for p in relative.split('/')) or str(path) != relative:
        raise ReviewError('Unsupported project path.')
    return path

@contextmanager
def parent(root, relative):
    path = relative_path(relative)
    with directory(Path(root) / Path(*path.parts[:-1])) as fd:
        yield fd, path.name

def read_file(root, relative):
    with parent(root, relative) as (fd, name):
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        try:
            info = os.fstat(file_fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise ReviewError('Unsupported or oversized file: '+relative)
            with os.fdopen(file_fd, 'rb', closefd=False) as stream:
                data = stream.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ReviewError('Oversized file: '+relative)
            return data, stat.S_IMODE(info.st_mode)
        finally:
            os.close(file_fd)

class ReviewStore:
    def __init__(self, db, root, source, files, lock=None):
        self.db = Path(db)
        self.root = Path(root).resolve()
        self.source = Path(source).resolve()
        self.files = tuple(files)
        self.lock = lock or threading.Lock()
        with directory(self.source) as fd:
            info = os.fstat(fd)
            self.source_identity = (info.st_dev, info.st_ino)
        with self.connect() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
                task_id TEXT PRIMARY KEY, review_id TEXT NOT NULL,
                status TEXT NOT NULL, payload TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '', written TEXT NOT NULL DEFAULT '[]'
            )''')
            conn.execute("UPDATE reviews SET status='INTERRUPTED', note='Application interrupted during file changes. Review recovery; nothing resumed automatically.' WHERE status IN ('APPLYING','RESTORING')")

    def connect(self):
        conn = sqlite3.connect(self.db, timeout=5, factory=Connection)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA synchronous=FULL')
        return conn

    def check_project(self):
        with directory(self.source) as fd:
            info = os.fstat(fd)
            if (info.st_dev, info.st_ino) != self.source_identity:
                raise ReviewError('The project directory changed; review required.')

    def capture(self, tid, hashes, workspace, evidence):
        """Called only after the worker completion and test gates have passed."""
        if str(uuid.UUID(tid)) != tid:
            raise ReviewError('Invalid task identifier.')
        if set(hashes) != set(self.files):
            raise ReviewError('Result manifest does not match the approved project.')
        self.check_project()
        workspace = Path(workspace)
        # No caller-controlled path comes from the browser or model receipt.
        if workspace != self.root / tid / 'workspace':
            raise ReviewError('Unexpected result workspace.')
        total = 0
        originals, results, modes = {}, {}, {}
        for relative in self.files:
            before, mode = read_file(self.source, relative)
            after, _ = read_file(workspace, relative)
            total += len(before) + len(after)
            if total > MAX_BYTES:
                raise ReviewError('Review size limit exceeded.')
            before.decode('utf-8'); after.decode('utf-8')
            from crew import SECRET
            if SECRET.search(after.decode('utf-8')):
                raise ReviewError('Result may contain a secret; owner review required before any application.')
            if b'\x00' in before or b'\x00' in after:
                raise ReviewError('Binary files require an owner decision.')
            if digest(before) != hashes[relative]:
                raise ReviewError('Original project changed; result cannot be reviewed safely.')
            if relative.startswith('tests/') and before != after:
                raise ReviewError('Protected existing tests changed.')
            originals[relative], results[relative], modes[relative] = encode(before), encode(after), mode
        self.check_workspace(workspace)
        changed = [p for p in self.files if originals[p] != results[p]]
        payload = dict(task_id=tid, files=list(self.files), originals=originals, results=results,
                       modes=modes, changed=changed, test_evidence=evidence,
                       verification='Worker completed and project tests passed. Owner must inspect task acceptance.',
                       result_sha256={p: digest(decode(results[p])) for p in self.files})
        rid = digest(canonical(payload).encode())
        with self.connect() as conn:
            conn.execute('INSERT INTO reviews(task_id,review_id,status,payload) VALUES (?,?,?,?)',
                         (tid, rid, 'READY', canonical(payload)))
        return rid

    def check_workspace(self, workspace):
        for current, dirs, names in os.walk(workspace, followlinks=False):
            for name in list(dirs):
                p = Path(current) / name
                if p.is_symlink():
                    raise ReviewError('Result contains a symlink; owner decision required.')
                if name in ('.tmp', '__pycache__'):
                    dirs.remove(name)
            for name in names:
                p = Path(current) / name
                if p.is_symlink():
                    raise ReviewError('Result contains a symlink; owner decision required.')
                if p.relative_to(workspace).as_posix() not in self.files:
                    raise ReviewError('New files are not supported by this apply flow; owner decision required.')
    def row(self, tid):
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM reviews WHERE task_id=?', (tid,)).fetchone()
        if row is None:
            raise ReviewError('This task has no captured review. Historical runs need a new verified task.')
        row = dict(row)
        payload = json.loads(row['payload'])
        if digest(canonical(payload).encode()) != row['review_id'] or set(payload['files']) != set(self.files):
            raise ReviewError('Review integrity check failed.')
        row['data'] = payload
        return row

    def get(self, tid):
        row = self.row(tid)
        data = row['data']
        changes = []
        for path in data['changed']:
            before, after = decode(data['originals'][path]), decode(data['results'][path])
            old_text, new_text = before.decode(), after.decode()
            prefix = len(os.path.commonprefix((old_text, new_text)))
            suffix = len(os.path.commonprefix((old_text[prefix:][::-1], new_text[prefix:][::-1])))
            old_excerpt = old_text[prefix:len(old_text)-suffix if suffix else len(old_text)]
            new_excerpt = new_text[prefix:len(new_text)-suffix if suffix else len(new_text)]
            changes.append(dict(path=path, before_sha256=digest(before), after_sha256=digest(after),
                before_excerpt=old_excerpt[:600], after_excerpt=new_excerpt[:600],
                excerpt_truncated=len(old_excerpt)>600 or len(new_excerpt)>600,
                diff=''.join(difflib.unified_diff(before.decode().splitlines(keepends=True),
                    after.decode().splitlines(keepends=True), fromfile=path+' (working)', tofile=path+' (result)')),
                recovery_diff=''.join(difflib.unified_diff(after.decode().splitlines(keepends=True),
                    before.decode().splitlines(keepends=True), fromfile=path+' (applied)', tofile=path+' (backup)'))))
        return dict(task_id=tid, review_id=row['review_id'], status=row['status'], note=row['note'],
                    changes=changes, test_evidence=data['test_evidence'], verification=data['verification'],
                    recovery_available=row['status'] in ('APPLIED','INTERRUPTED','RECOVERY_NEEDED'),
                    backup='Original bytes retained in the local review database.',
                    restart_required=any(p.endswith('.py') for p in data['changed']))

    def set_state(self, tid, state, note, written=()):
        with self.connect() as conn:
            conn.execute('UPDATE reviews SET status=?, note=?, written=? WHERE task_id=?',
                         (state, note, json.dumps(list(written)), tid))

    def replace(self, relative, expected, content, mode):
        self.check_project()
        with parent(self.source, relative) as (fd, name):
            staged = '.orchard-stage-'+uuid.uuid4().hex+'.tmp'
            stage_fd = os.open(staged, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, mode, dir_fd=fd)
            try:
                os.fchmod(stage_fd, mode)
                with os.fdopen(stage_fd, 'wb', closefd=False) as stream:
                    stream.write(content); stream.flush(); os.fsync(stage_fd)
                current, current_mode = read_file(self.source, relative)
                if current != expected or current_mode != mode:
                    raise ReviewError('Working file changed before replacement: '+relative)
                # The directory must still be reachable at the selected project path.
                with parent(self.source, relative) as (check_fd, _):
                    a, b = os.fstat(fd), os.fstat(check_fd)
                    if (a.st_dev,a.st_ino) != (b.st_dev,b.st_ino):
                        raise ReviewError('Working directory changed before replacement.')
                os.replace(staged, name, src_dir_fd=fd, dst_dir_fd=fd)
            finally:
                os.close(stage_fd)
                try:
                    os.unlink(staged, dir_fd=fd)
                except FileNotFoundError:
                    pass
            os.fsync(fd)

    def operate(self, tid, rid, consent, restore=False):
        if consent is not True:
            raise ReviewError('Explicit owner permission is required for this exact review.')
        if not self.lock.acquire(blocking=False):
            raise ReviewError('The worker or another file operation is busy.')
        try:
            row = self.row(tid); data = row['data']
            if rid != row['review_id']:
                raise ReviewError('Review changed or approval is stale; inspect the current review.')
            if (not restore and row['status']=='APPLIED') or (restore and row['status']=='RESTORED'):
                return self.get(tid)  # Idempotent even if newer owner edits now exist.
            allowed = ('APPLIED','INTERRUPTED','RECOVERY_NEEDED') if restore else ('READY','FAILED')
            if row['status'] not in allowed:
                raise ReviewError('This result is not available for the requested action.')
            self.check_project()
            if not restore:
                self.check_workspace(self.root / tid / 'workspace')
            expected, desired = {}, {}
            for path in data['files']:
                original, result = decode(data['originals'][path]), decode(data['results'][path])
                current, mode = read_file(self.source, path)
                if restore:
                    if path not in data['changed']:
                        continue
                    # Interrupted transactions can leave a mixture of before/after.
                    options = (original,result) if row['status'] != 'APPLIED' else (result,)
                    if current not in options or mode != data['modes'][path]:
                        raise ReviewError('Applied file has changed; recovery requires review: '+path)
                    expected[path], desired[path] = current, original
                else:
                    candidate, _ = read_file(self.root/tid/'workspace', path)
                    if candidate != result:
                        raise ReviewError('Saved result changed after review: '+path)
                    if current != original or mode != data['modes'][path]:
                        raise ReviewError('Working project changed since this task: '+path)
                    if path in data['changed']:
                        expected[path], desired[path] = original, result
            # Backups are already durably stored in the immutable review payload.
            started = 'RESTORING' if restore else 'APPLYING'
            self.set_state(tid, started, 'Owner permission recorded; original bytes retained.')
            planned = [p for p in expected if expected[p]!=desired[p]]
            try:
                for index,path in enumerate(planned):
                    self.replace(path, expected[path], desired[path], data['modes'][path])
                    self.set_state(tid, started, 'Replacing reviewed files.', planned[:index+1])
                for path in planned:
                    current, mode = read_file(self.source, path)
                    if current != desired[path] or mode != data['modes'][path]:
                        raise ReviewError('File changed before the application receipt was completed: '+path)
                self.set_state(tid,'RESTORED' if restore else 'APPLIED',
                               'Previous source restored with owner permission.' if restore else 'Reviewed changes applied with owner permission. Backup retained.')
            except Exception as exc:
                conflicts = []
                # Inspect all planned paths: replacement may have succeeded before an error.
                for path in reversed(planned):
                    try:
                        current, _ = read_file(self.source,path)
                        if current == expected[path]:
                            continue
                        if current != desired[path]:
                            conflicts.append(path); continue
                        self.replace(path, desired[path], expected[path], data['modes'][path])
                    except Exception:
                        conflicts.append(path)
                state = 'RECOVERY_NEEDED' if conflicts else (row['status'] if restore else 'FAILED')
                note = ('File operation failed. '+('Recovery requires owner review: '+', '.join(conflicts) if conflicts else 'Previous bytes restored; no partial update remains.'))
                self.set_state(tid,state,note)
                raise ReviewError(note) from exc
            return self.get(tid)
        except (OSError, UnicodeError, ValueError) as exc:
            if isinstance(exc, ReviewError):
                raise
            raise ReviewError('File operation could not be verified; no success claimed.') from exc
        finally:
            self.lock.release()
