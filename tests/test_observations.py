import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import Handler
from observations import export_observation, readonly_connection, ObservationError
from contracts.task_contract_v1.orchard_bridge import validate_observation
from crew import snapshot

ROOT=Path(__file__).resolve().parents[1]
TID="12345678-1234-4234-9234-123456789abc"

class ObservationExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.base=Path(self.temp.name);self.db=self.base/"fixture.sqlite3"
        with sqlite3.connect(self.db) as c:
            c.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, request TEXT, status TEXT, evidence TEXT, receipt TEXT)")
            c.execute("CREATE TABLE reviews (task_id TEXT PRIMARY KEY, status TEXT)")
            c.execute("INSERT INTO tasks VALUES (?,?,?,?,?)",(TID,"PRIVATE-SENTINEL","DONE","PRIVATE-SENTINEL","not-json:PRIVATE-SENTINEL"))
    def tearDown(self):
        self.temp.cleanup()
    def get(self,tid=TID,origin=None,host="127.0.0.1:8765",enabled=True):
        h=Handler.__new__(Handler);h.crew=SimpleNamespace(db=self.db) if enabled else None
        h.server=SimpleNamespace(server_port=8765);h.path="/api/tasks/"+tid+"/observation"
        h.headers={"Host":host}
        if origin is not None:h.headers["Origin"]=origin
        output=[];h._json=lambda status,obj:output.append((status,obj))
        h.do_GET();return output[0]
    def test_actual_handler_validates_without_promoting_or_reading_payload(self):
        before=self.db.read_bytes()
        with patch("crew.Crew.list",side_effect=AssertionError("payload path forbidden")),patch("crew.Crew.start",side_effect=AssertionError("worker forbidden")):
            status,body=self.get()
        self.assertEqual(status,200);value=body["observation"];validate_observation(value)
        self.assertEqual(value["reported_execution"],"completed")
        self.assertEqual(value["acceptance"],"unverified")
        self.assertNotIn("PRIVATE-SENTINEL",json.dumps(body))
        self.assertEqual(before,self.db.read_bytes())
    def test_application_claim_and_unknown_states(self):
        with sqlite3.connect(self.db) as c:c.execute("INSERT INTO reviews VALUES (?,?)",(TID,"APPLIED"))
        value=self.get()[1]["observation"]
        self.assertEqual(value["reported_application"],"APPLIED")
        self.assertEqual(value["application"],"unverified")
        with sqlite3.connect(self.db) as c:c.execute("UPDATE tasks SET status='CANCELLED'")
        status,body=self.get();self.assertEqual(status,409)
        self.assertNotIn("PRIVATE-SENTINEL",json.dumps(body))
    def test_missing_disabled_and_invalid_identity(self):
        self.assertEqual(self.get(enabled=False)[0],409)
        self.assertEqual(self.get("22345678-1234-4234-9234-123456789abc")[0],404)
        with self.assertRaises(ObservationError):export_observation(self.db,"../fixture.sqlite3")
    def test_host_origin_and_no_cli_origin(self):
        self.assertEqual(self.get(origin="https://foreign.example")[0],403)
        self.assertEqual(self.get(host="foreign.example")[0],403)
        self.assertEqual(self.get(origin="http://127.0.0.1:8765")[0],200)
        self.assertEqual(self.get()[0],200)
    def test_sqlite_is_readonly_missing_database_not_created(self):
        with closing(readonly_connection(self.db)) as connection:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute("DELETE FROM tasks")
        missing=self.base/"missing.sqlite3"
        with self.assertRaises(ObservationError):export_observation(missing,TID)
        self.assertFalse(missing.exists())
    def test_database_failure_is_generic_and_no_success(self):
        with sqlite3.connect(self.db) as c:c.execute("DROP TABLE reviews")
        status,body=self.get()
        self.assertEqual(status,409)
        self.assertEqual(set(body),{"error"})
        self.assertNotIn(str(self.db),json.dumps(body))
    def test_distribution_manifest_and_export_validation_failure(self):
        package=ROOT/"contracts/task_contract_v1"
        manifest=json.loads((package/"manifest.json").read_text())
        for name,digest in manifest["sha256"].items():
            self.assertEqual(hashlib.sha256((package/name).read_bytes()).hexdigest(),digest)
        with patch("contracts.task_contract_v1.orchard_bridge.validate_observation",side_effect=__import__("contracts.task_contract_v1.validate",fromlist=["ContractError"]).ContractError("bad")):
            self.assertEqual(self.get()[0],409)
    def test_disposable_worker_snapshot_contains_export_dependencies(self):
        destination=self.base/"snapshot"
        snapshot(ROOT,destination)
        checked=subprocess.run([sys.executable,"-B","-c","import app; from observations import export_observation; from contracts.task_contract_v1.orchard_bridge import inspect_row; inspect_row(dict(id='12345678-1234-4234-9234-123456789abc',status='DONE',application_status=None))"],
                               cwd=destination,capture_output=True,text=True,timeout=5)
        self.assertEqual(checked.returncode,0,checked.stderr)

if __name__=="__main__":unittest.main()
