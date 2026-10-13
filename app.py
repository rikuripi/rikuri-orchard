"""Rikuri Orchard: local Seed Box with an optional permission-gated Codex worker."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlparse
import uuid
from crew import Crew, CrewError, CodexAdapter, ClosingConnection

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
DB_DEFAULT = Path.cwd() / "orchard.sqlite3"
STATES = {"NEW", "EXPLORING", "PLANNED", "PARKED"}
TRANSITIONS = {
    "NEW": {"EXPLORING", "PARKED"},
    "EXPLORING": {"PLANNED", "PARKED"},
    "PLANNED": {"EXPLORING", "PARKED"},
    "PARKED": {"NEW"},
}

class SeedError(ValueError):
    pass


def connect(db_path: Path):
    db = sqlite3.connect(str(db_path), timeout=5, factory=ClosingConnection)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=5000")
    return db


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS seeds (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            detail TEXT NOT NULL DEFAULT '',
            state TEXT NOT NULL CHECK(state IN ('NEW','EXPLORING','PLANNED','PARKED')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1
        )""")


def _validate_text(value, field, max_len, required=False):
    if not isinstance(value, str):
        raise SeedError(f"{field} must be text")
    clean = value.strip()
    if required and not clean:
        raise SeedError(f"{field} is required")
    if len(clean) > max_len:
        raise SeedError(f"{field} must be {max_len} characters or fewer")
    if any(ord(c) < 32 and c not in "\n\t" for c in clean):
        raise SeedError(f"{field} contains unsupported control characters")
    return clean


def add_seed(db_path: Path, title, detail=""):
    title = _validate_text(title, "Title", 120, True)
    detail = _validate_text(detail, "Description", 3000)
    now = datetime.now(timezone.utc).isoformat()
    sid = str(uuid.uuid4())
    with connect(db_path) as db:
        db.execute("INSERT INTO seeds(id,title,detail,state,created_at,updated_at,version) VALUES (?,?,?,?,?,?,1)",
                   (sid, title, detail, "NEW", now, now))
    return {"id": sid, "title": title, "detail": detail, "state": "NEW", "created_at": now, "updated_at": now, "version": 1}


def list_seeds(db_path: Path):
    with connect(db_path) as db:
        rows = db.execute("SELECT id,title,detail,state,created_at,updated_at,version FROM seeds ORDER BY created_at DESC, id DESC").fetchall()
    return [dict(row) for row in rows]


def update_seed_state(db_path: Path, seed_id: str, state: str, version: int):
    if state not in STATES:
        raise SeedError("Unknown status")
    if type(version) is not int or version < 1:
        raise SeedError("Expected version must be a positive integer")
    with connect(db_path) as db:
        row = db.execute("SELECT * FROM seeds WHERE id=?", (seed_id,)).fetchone()
        if row is None:
            raise SeedError("Seed not found")
        if row["version"] != version:
            raise SeedError("This seed changed since you last viewed it; refresh first")
        if state not in TRANSITIONS[row["state"]]:
            raise SeedError(f"Can't move from {row['state']} to {state}")
        now = datetime.now(timezone.utc).isoformat()
        changed = db.execute("UPDATE seeds SET state=?, updated_at=?, version=version+1 WHERE id=? AND version=?",
                             (state, now, seed_id, version))
        if changed.rowcount != 1:
            raise SeedError("Update conflict; refresh first")
        row = db.execute("SELECT * FROM seeds WHERE id=?", (seed_id,)).fetchone()
    return dict(row)


class Handler(BaseHTTPRequestHandler):
    db_path = DB_DEFAULT
    crew = None
    server_version = "RikuriOrchard/0.2"
    sys_version = ""

    def _reply(self, status: int, content: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, status, obj):
        self._reply(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _allowed_host(self):
        host = self.headers.get("Host", "")
        return host in {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}

    def _allowed_origin(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True  # supports local CLI requests without Origin
        return origin in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}

    def do_GET(self):
        if not self._allowed_host():
            return self._json(403, {"error": "Invalid host"})
        if self.path in ("/", "/index.html"):
            return self._reply(200, INDEX.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/tasks":
            return self._json(200, {"tasks": self.crew.list() if self.crew else [], "enabled": self.crew is not None})
        if self.path == "/api/seeds":
            return self._json(200, {"seeds": list_seeds(self.db_path)})
        if self.path == "/api/health":
            return self._json(200, {"status": "ok", "prototype": True, "agent_execution": self.crew is not None})
        return self._json(404, {"error": "Not found"})

    def do_POST(self):
        if not self._allowed_host() or not self._allowed_origin():
            return self._json(403, {"error": "Request origin not permitted"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self._json(415, {"error": "Expected application/json"})
        size_raw = self.headers.get("Content-Length", "")
        if not size_raw.isdigit() or int(size_raw) > 16384:
            return self._json(413, {"error": "Invalid or oversized request"})
        try:
            data = json.loads(self.rfile.read(int(size_raw)))
            if not isinstance(data, dict):
                raise SeedError("Expected a JSON object")
            if self.path == "/api/tasks":
                if self.crew is None:
                    raise CrewError("Codex adapter is disabled; start with --codex and --codex-home.")
                if set(data) != {"request"}:
                    raise CrewError("Expected one request field")
                return self._json(201, {"id": self.crew.submit(data["request"])})
            task_match = re.fullmatch(r"/api/tasks/([0-9a-f-]{36})/approve", self.path)
            if task_match:
                if self.crew is None or set(data) != {"consent"}:
                    raise CrewError("Expected explicit consent for enabled adapter")
                self.crew.start(task_match.group(1), data["consent"])
                return self._json(202, {"status": "RUNNING"})
            if self.path == "/api/seeds":
                if set(data) - {"title", "detail"}:
                    raise SeedError("Unknown fields")
                return self._json(201, {"seed": add_seed(self.db_path, data.get("title"), data.get("detail", ""))})
            match = re.fullmatch(r"/api/seeds/([0-9a-f-]{36})/state", self.path)
            if match:
                if set(data) != {"state", "version"}:
                    raise SeedError("Expected state and version")
                return self._json(200, {"seed": update_seed_state(self.db_path, match.group(1), data["state"], data["version"])})
            return self._json(404, {"error": "Not found"})
        except (SeedError, CrewError, json.JSONDecodeError) as exc:
            return self._json(400, {"error": str(exc)})
        except sqlite3.Error:
            return self._json(500, {"error": "Database operation failed; no success claimed"})

    def log_message(self, fmt, *args):
        pass  # prototype avoids recording sensitive seed text or HTTP access metadata


def main():
    parser = argparse.ArgumentParser(description="Rikuri Orchard O0 local Seed Box")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    parser.add_argument("--codex", type=Path, help="Explicit path to native Codex executable; disabled by default")
    parser.add_argument("--codex-home", type=Path, help="Dedicated empty Codex profile; sign in separately")
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    args = parser.parse_args()
    if bool(args.codex) != bool(args.codex_home):
        parser.error("Provide both --codex and --codex-home")
    if args.codex:
        if not args.codex.is_file() or not args.codex_home.is_dir():
            parser.error("Codex executable and dedicated profile must exist")
        if (args.codex_home / "config.toml").exists():
            parser.error("Dedicated profile must have no config.toml; inherited tools/configuration are not allowed")
    init_db(args.db)
    worker = Crew(args.db, args.runs, ROOT, CodexAdapter(args.codex, args.codex_home)) if args.codex else None
    init_db(args.db)
    class LocalHandler(Handler):
        db_path = args.db
        crew = worker
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), LocalHandler)
    print(f"Rikuri Orchard v0.2 · http://127.0.0.1:{httpd.server_port}")
    print("Local only. Codex requires task-specific permission. Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    main()
