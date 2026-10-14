"""One bounded worker. No shell interpolation, automatic approvals, or host test execution."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

FILES = ('app.py', 'crew.py', 'review.py', 'index.html', 'tests/test_app.py', 'tests/test_crew.py', 'tests/test_review.py')
LIMITS = dict(seconds=180, turns=1, retries=0, wire_bytes=1048576, snapshot_bytes=2097152)
SECRET = re.compile(r'sk-[A-Za-z0-9_-]{12,}|(?i:bearer)\s+[A-Za-z0-9._-]{12,}|(?i:(?:api_key|password|secret)\s*[=:]\s*[\"\'])[A-Za-z0-9_-]{12,}')

def scrub(text):
    return SECRET.sub('[REDACTED]', str(text))[:12000]

class CrewError(ValueError):
    pass

class OwnerDecision(Exception):
    pass

class BoundedRPC:
    """Bounded JSONL transport; any server request ends this run without approval."""
    def __init__(self, argv, cwd, home, deadline, byte_limit):
        env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT', 'LANG') if k in os.environ}
        env.update(HOME=str(home), CODEX_HOME=str(home), TMPDIR=str(cwd / '.tmp'))
        (cwd / '.tmp').mkdir(exist_ok=True)
        self.process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=True)
        self.deadline, self.limit, self.used, self.next_id = deadline, byte_limit, 0, 0
        self.messages = queue.Queue(maxsize=64)
        self.log = []
        self.diagnostic = ""
        self.closed = threading.Event()
        self.lock = threading.Lock()
        def reader(stream, is_error):
            try:
                while not self.closed.is_set():
                    line = stream.readline(byte_limit + 1)
                    if not line:
                        if not is_error:
                            self.put(None)
                        break
                    with self.lock:
                        self.used += len(line)
                        overflow = self.used > self.limit
                    if overflow:
                        self.put(CrewError('Worker output budget exhausted.'))
                        break
                    if is_error:
                        self.diagnostic = scrub(line.decode("utf-8", errors="replace"))[:2000]
                        continue
                    try:
                        self.put(json.loads(line))
                    except (ValueError, UnicodeError):
                        self.put(CrewError('Invalid Codex protocol output.'))
                        break
            except OSError:
                self.put(None)
        for stream, err in ((self.process.stdout, False), (self.process.stderr, True)):
            threading.Thread(target=reader, args=(stream, err), daemon=True).start()

    def put(self, msg):
        while not self.closed.is_set():
            try:
                self.messages.put(msg, timeout=.1)
                return
            except queue.Full:
                pass

    def send(self, obj):
        self.process.stdin.write((json.dumps(obj)+'\n').encode())
        self.process.stdin.flush()

    def receive(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise CrewError('Total time budget exhausted; worker stopped.')
        try:
            msg = self.messages.get(timeout=remaining)
        except queue.Empty:
            raise CrewError('Total time budget exhausted; worker stopped.')
        if isinstance(msg, Exception):
            raise msg
        if msg is None:
            raise CrewError('Codex exited before verified completion. '+self.diagnostic)
        if not isinstance(msg, dict):
            raise CrewError('Invalid Codex message.')
        method = msg.get('method')
        if method:
            self.log.append(method)
        if method and 'id' in msg:
            # Never approve, answer user questions, or grant a broader sandbox.
            raise OwnerDecision('Codex requires human input: '+method+'. Proposed action: '+scrub(json.dumps(msg.get('params', {})))+'. Run stopped; no permission granted.')
        return msg

    def call(self, method, params):
        self.next_id += 1
        rid = self.next_id
        self.send(dict(id=rid, method=method, params=params))
        while True:
            msg = self.receive()
            if msg.get('id') == rid:
                if 'error' in msg:
                    raise CrewError('Codex rejected '+method+': '+scrub(msg['error'].get('message', 'protocol error')))
                if not isinstance(msg.get('result'), dict):
                    raise CrewError('Missing Codex result for '+method)
                return msg['result']

    def close(self):
        self.closed.set()
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()

def sqlite_runtime_grants(candidates=None):
    """Allow existing Homebrew SQLite files and their canonical library directories.

    Python's framework prefix does not include Homebrew's separately installed
    SQLite library. Do not grant the Homebrew prefix or unrelated packages.
    Other runtimes use their existing Python/minimal-platform read permissions.
    """
    if candidates is None:
        candidates = (Path('/opt/homebrew/opt/sqlite/lib/libsqlite3.dylib'),
                      Path('/usr/local/opt/sqlite/lib/libsqlite3.dylib')) if sys.platform == 'darwin' else ()
    grants = {}
    for candidate in candidates:
        candidate = Path(candidate)
        try:
            available = candidate.is_file()
        except OSError:
            # A caller already inside a sandbox must not inspect denied aliases.
            continue
        if available:
            grants[str(candidate.absolute())] = 'read'
            grants[str(candidate.resolve())] = 'read'
            # dyld can load the same installed runtime from its canonical directory.
            grants[str(candidate.resolve().parent)] = 'read'
    return grants


class CodexAdapter:
    def __init__(self, executable, home):
        self.executable, self.home = str(executable), Path(home).resolve()

    def run(self, workspace, request, deadline, record):
        if not (self.home / 'auth.json').is_file():
            raise OwnerDecision('Sign in to Codex using the dedicated Orchard profile before running. No credentials were copied.')
        # A named native permission profile replaces legacy full-read sandbox modes.
        argv = [self.executable, 'app-server', '--listen', 'stdio://']
        overrides = {
            'default_permissions': 'orchard', 'approval_policy': 'on-request',
            'approvals_reviewer': 'user', 'web_search': 'disabled',
            'features.multi_agent': False, 'features.apps': False,
        }
        for key, value in overrides.items():
            argv.extend(['-c', key + '=' + json.dumps(value)])
        grants = {':minimal': 'read', str(workspace): 'write',
                  str(workspace / 'tests/test_app.py'): 'read',
                  str(workspace / 'tests/test_crew.py'): 'read', str(self.home): 'deny',
                  str(Path(sys.base_prefix).resolve()): 'read',
                  str(Path(sys.executable).parent): 'read',
                  str(Path(sys.executable).resolve().parent): 'read'}
        grants.update({str(workspace / file): 'read' for file in FILES if file.startswith('tests/')})
        sqlite_grants = sqlite_runtime_grants()
        grants.update(sqlite_grants)
        sqlite_dirs = sorted(path for path in sqlite_grants if Path(path).is_dir())
        def python_command(*arguments):
            runtime = str(Path(sys.executable).resolve())
            if not sqlite_dirs:
                return [runtime, *arguments]
            # sandbox-exec (a platform binary) strips DYLD_* on macOS. Set the
            # vetted runtime path inside the sandbox, then exec the same Python.
            bootstrap = ("import os,sys; env=dict(os.environ); "
                         "env['DYLD_LIBRARY_PATH']=sys.argv[1]; env['PYTHONEXECUTABLE']=sys.argv[2]; "
                         "os.execve(sys.argv[2],[sys.argv[2],*sys.argv[3:]],env)")
            return [runtime, '-c', bootstrap, os.pathsep.join(sqlite_dirs), runtime, *arguments]
        filesystem = ', '.join(json.dumps(k)+'='+json.dumps(v) for k,v in grants.items())
        argv.extend(['-c', 'permissions.orchard={filesystem={'+filesystem+'},network={enabled=false}}'])
        rpc = BoundedRPC(argv, workspace, self.home, deadline, LIMITS['wire_bytes'])
        try:
            rpc.call('initialize', dict(clientInfo=dict(name='rikuri_orchard', title='Rikuri Orchard', version='0.2'), capabilities=dict(experimentalApi=True)))
            rpc.send(dict(method='initialized', params={}))
            # Test executable itself validates the sandbox before any model request.
            probe_code = """import pathlib, socket, sys, sqlite3
with sqlite3.connect(':memory:') as database:
    assert database.execute('SELECT 1').fetchone() == (1,)
for path in sys.argv[1:3]:
    try:
        pathlib.Path(path).read_bytes()
    except PermissionError:
        pass
    else:
        raise SystemExit('Sandbox boundary failed: outside read permitted')
try:
    open('tests/test_app.py', 'a').close()
except PermissionError:
    pass
else:
    raise SystemExit('Sandbox boundary failed: baseline test edits permitted')
try:
    socket.create_connection(('127.0.0.1', 9), timeout=1)
except PermissionError:
    pass
except OSError:
    raise SystemExit('Sandbox boundary failed: network socket permitted')
else:
    raise SystemExit('Sandbox boundary failed: network permitted')
print('ORCHARD_SANDBOX_READY')
"""
            probe = rpc.call('command/exec', dict(command=python_command('-c', probe_code,
                                                  str(self.home / 'auth.json'), str(Path(__file__).resolve())),
                                                  cwd=str(workspace), permissionProfile='orchard', timeoutMs=10000))
            if probe.get('exitCode') != 0 or 'ORCHARD_SANDBOX_READY' not in probe.get('stdout', ''):
                record('Native sandbox preflight output:\n'+scrub(probe.get('stdout', '')+'\n'+probe.get('stderr', '')))
                raise CrewError('Native sandbox preflight failed. No model task started.')
            record('Native sandbox preflight passed: Python and a SQLite query run; outside reads, baseline test edits and worker network are denied.')
            th = rpc.call('thread/start', dict(cwd=str(workspace), approvalPolicy='on-request', approvalsReviewer='user',
                                                permissions='orchard', ephemeral=True))
            if th.get('activePermissionProfile', {}).get('id') != 'orchard' or th.get('approvalsReviewer') != 'user' or th.get('approvalPolicy') != 'on-request':
                raise CrewError('Native server did not confirm the requested permission and human approval settings.')
            record('Native settings confirmed: Orchard profile, human approvals, model '+str(th.get('model', 'unknown'))+'.')
            tid = th['thread']['id']
            prompt = ('Work on exactly this task in this disposable project. No git operations, networking, '
                      'extra tasks, agent delegation, credentials, or changes outside this directory. '
                      'One turn, zero retries. Stop if permission is required. Implement and explain evidence.\n'+request)
            started = rpc.call('turn/start', dict(threadId=tid, cwd=str(workspace), approvalPolicy='on-request', approvalsReviewer='user',
                                                  permissions='orchard', input=[dict(type='text', text=prompt)]))
            turn_id = started['turn']['id']
            summary = ''
            while True:
                msg = rpc.receive()
                p = msg.get('params', {})
                if msg.get('method') == 'item/completed' and p.get('threadId') == tid:
                    item = p.get('item', {})
                    if item.get('type') == 'agentMessage':
                        summary = scrub(item.get('text', ''))
                if msg.get('method') == 'turn/completed' and p.get('threadId') == tid and p.get('turn', {}).get('id') == turn_id:
                    if p['turn'].get('status') != 'completed':
                        raise CrewError('Codex turn did not complete successfully.')
                    break
            # A zero-test or failed suite never produces DONE. Test process is sandboxed too.
            tested = rpc.call('command/exec', dict(command=python_command('-m', 'unittest', 'discover', '-s', 'tests', '-v'),
                                                   cwd=str(workspace), permissionProfile='orchard',
                                                   timeoutMs=min(60000, max(1, int((deadline-time.monotonic())*1000)))))
            output = scrub(tested.get('stdout', '')+'\n'+tested.get('stderr', ''))
            record('Project test output:\n'+output)
            if tested.get('exitCode') != 0 or not re.search(r'Ran [1-9][0-9]* tests?\b', output) or not re.search(r'^OK$', output, re.M):
                raise CrewError('Project tests failed, timed out, or ran no tests; no repair was started.')
            return summary
        finally:
            record('Protocol events: '+', '.join(rpc.log[-80:]))
            rpc.close()

def snapshot(source, target):
    source = source.resolve()
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=False)
    total = 0
    hashes = {}
    for relative in FILES:
        path = source / relative
        # Every component must be an ordinary path, not a symlink.
        if any(p.is_symlink() for p in [path, *path.parents]):
            raise CrewError('Snapshot refuses symlinks: '+relative)
        if not path.is_file():
            raise CrewError('Missing selected project file: '+relative)
        content = path.read_bytes()
        total += len(content)
        if total > LIMITS['snapshot_bytes']:
            raise CrewError('Snapshot size budget exceeded.')
        if SECRET.search(content.decode('utf-8')):
            raise OwnerDecision('Selected source may contain a secret: '+relative+'. Remove it before transmission.')
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        hashes[relative] = hashlib.sha256(content).hexdigest()
    return hashes

class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()

class Crew:
    def __init__(self, db, root, source, adapter):
        self.db, self.root, self.source, self.adapter = Path(db), Path(root).resolve(), Path(source).resolve(), adapter
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        with self.connect() as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, request TEXT NOT NULL, status TEXT NOT NULL, evidence TEXT NOT NULL, receipt TEXT NOT NULL)')
            conn.execute("UPDATE tasks SET status='BLOCKED', evidence=evidence || '\nApplication restarted during execution; no automatic retry.' WHERE status='RUNNING'")
        from review import ReviewStore
        self.reviews = ReviewStore(self.db, self.root, self.source, FILES, self.lock)

    def connect(self):
        conn = sqlite3.connect(self.db, timeout=5, factory=ClosingConnection)
        conn.row_factory = sqlite3.Row
        return conn

    def list(self):
        with self.connect() as conn:
            tasks = [dict(r) | {'receipt': json.loads(r['receipt'])} for r in conn.execute('SELECT * FROM tasks ORDER BY rowid DESC')]
            states = {r['task_id']: r['status'] for r in conn.execute('SELECT task_id,status FROM reviews')}
        for task in tasks:
            task['application_status'] = states.get(task['id'])
        return tasks

    def submit(self, request):
        if not isinstance(request, str) or not request.strip() or len(request) > 3000:
            raise CrewError('Describe one task in 1–3000 characters.')
        if SECRET.search(request):
            raise CrewError('Task appears to contain a secret; remove it first.')
        tid = str(uuid.uuid4())
        with self.connect() as conn:
            conn.execute('INSERT INTO tasks VALUES (?,?,?,?,?)', (tid, request.strip(), 'NEEDS_OWNER_DECISION',
                'Awaiting explicit permission for a disposable source copy, Codex transmission, edits and sandboxed tests.', json.dumps(dict(limits=LIMITS, files=FILES))))
        return tid

    def record(self, tid, text):
        with self.connect() as conn:
            conn.execute("UPDATE tasks SET evidence=evidence || ? WHERE id=?", ('\n'+scrub(text), tid))

    def start(self, tid, consent):
        if consent is not True:
            raise CrewError('Explicit permission is required.')
        if not self.lock.acquire(blocking=False):
            raise CrewError('The single worker is busy.')
        try:
            with self.connect() as conn:
                row = conn.execute('SELECT * FROM tasks WHERE id=?', (tid,)).fetchone()
                if row is None or row['status'] != 'NEEDS_OWNER_DECISION' or json.loads(row['receipt']).get('started'):
                    raise CrewError('Task missing or already attempted. No automatic retries.')
                receipt = json.loads(row['receipt']) | dict(started=True, consent=True)
                conn.execute("UPDATE tasks SET status='RUNNING', receipt=? WHERE id=?", (json.dumps(receipt), tid))
            thread = threading.Thread(target=self.execute, args=(tid, row['request']), daemon=True)
            thread.start()
        except Exception:
            self.lock.release()
            raise

    def execute(self, tid, request):
        state = 'BLOCKED'
        receipt = None
        try:
            workspace = self.root / tid / 'workspace'
            hashes = snapshot(self.source, workspace)
            receipt = dict(limits=LIMITS, files=FILES, started=True, consent=True, input_sha256=hashes,
                           workspace=str(workspace), backend=type(self.adapter).__name__)
            with self.connect() as conn:
                conn.execute('UPDATE tasks SET receipt=? WHERE id=?', (json.dumps(receipt), tid))
            self.record(tid, 'Permission recorded. Snapshot created; original Seed Box and database were not copied or modified.')
            summary = self.adapter.run(workspace, request, time.monotonic()+LIMITS['seconds'], lambda text: self.record(tid, text))
            # Recheck source and snapshot test integrity; worker cannot make existing tests pass by weakening them.
            for file, digest in hashes.items():
                if hashlib.sha256((self.source/file).read_bytes()).hexdigest() != digest:
                    raise CrewError('Original source changed during execution; result requires review.')
                if file.startswith('tests/'):
                    p = workspace/file
                    if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
                        raise CrewError('Existing tests were changed; passing tests are insufficient evidence.')
            if not summary:
                raise CrewError('Codex returned no explanation of its work.')
            receipt['changed_files'] = [file for file, digest in hashes.items()
                                        if not (workspace/file).is_file() or (workspace/file).is_symlink()
                                        or hashlib.sha256((workspace/file).read_bytes()).hexdigest() != digest]
            with self.connect() as conn:
                conn.execute('UPDATE tasks SET receipt=? WHERE id=?', (json.dumps(receipt), tid))
            self.record(tid, 'Codex explanation (model claim, inspect against task acceptance conditions):\n'+summary)
            from review import ReviewError
            try:
                evidence = next(task['evidence'] for task in self.list() if task['id'] == tid)
                self.reviews.capture(tid, hashes, workspace, evidence)
            except (ReviewError, OSError, UnicodeError) as exc:
                raise OwnerDecision('Review capture needs owner attention: '+str(exc)) from exc
            self.record(tid, 'Ready for review: Codex completed and project tests passed. Inspect the changes and explicitly approve Apply to update your working project.')
            state = 'DONE'
        except OwnerDecision as exc:
            state = 'NEEDS_OWNER_DECISION'
            self.record(tid, str(exc))
        except Exception as exc:
            self.record(tid, 'BLOCKED: '+scrub(str(exc)))
        finally:
            with self.connect() as conn:
                conn.execute('UPDATE tasks SET status=? WHERE id=?', (state, tid))
            self.lock.release()
