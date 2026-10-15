"""Disposable real-GET fixture. Stdin controls only; never a production launcher."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import Handler, init_db
from crew import Crew

def emit(value):
    print(json.dumps(value),flush=True)

def main():
    writes=[]
    class NoWorker(Crew):
        def start(self,*args):
            writes.append("worker-start")
            raise AssertionError("fixture forbids worker starts")
    with tempfile.TemporaryDirectory(prefix="orchard-http-e2e.") as temporary:
        base=Path(temporary);source=base/"source";source.mkdir()
        db=base/"fixture.sqlite3";init_db(db)
        crew=NoWorker(db,base/"runs",source,None)
        tid=crew.submit("Synthetic observation fixture")
        with crew.connect() as connection:
            connection.execute("UPDATE tasks SET status=?, evidence=?, receipt=? WHERE id=?",
                               ("DONE","PRIVATE-SENTINEL",json.dumps({"started":True,"private":"PRIVATE-SENTINEL"}),tid))
            connection.execute("INSERT INTO reviews(task_id,review_id,status,payload) VALUES (?,?,?,?)",
                               (tid,"fixture-only","APPLIED","PRIVATE-SENTINEL"))
        expected=hashlib.sha256(db.read_bytes()).hexdigest()
        requests=[]
        class FixtureHandler(Handler):
            def do_GET(self):
                requests.append(("GET",self.path))
                return super().do_GET()
            def do_POST(self):
                writes.append("HTTP-POST")
                return self._json(405,{"error":"Fixture permits GET only"})
        FixtureHandler.db_path=db;FixtureHandler.crew=crew
        server=ThreadingHTTPServer(("127.0.0.1",0),FixtureHandler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def check():
            assert hashlib.sha256(db.read_bytes()).hexdigest()==expected,"GET changed fixture database"
            assert not writes,"forbidden write/worker action attempted"
        emit({"event":"ready","origin":"http://127.0.0.1:"+str(server.server_port),"task_id":tid})
        try:
            while True:
                line=sys.stdin.readline(4097)
                if not line:break
                assert len(line)<=4096
                message=json.loads(line)
                assert set(message)=={"command"}
                command=message["command"]
                assert command in {"check","unsupported","restore","stop"}
                check()
                if command in {"unsupported","restore"}:
                    with crew.connect() as connection:
                        connection.execute("UPDATE tasks SET status=? WHERE id=?",
                                           ("UNSUPPORTED" if command=="unsupported" else "DONE",tid))
                    expected=hashlib.sha256(db.read_bytes()).hexdigest()
                emit({"event":command,"database_unchanged_by_reads":True,
                      "get_requests":len(requests),"forbidden_actions":len(writes)})
                if command=="stop":break
        finally:
            server.shutdown();server.server_close();thread.join(timeout=3)
            assert not thread.is_alive(),"fixture server did not stop"
    assert not base.exists(),"fixture data retained"
    emit({"event":"cleaned","server_stopped":True,"fixture_removed":True})

if __name__=="__main__":main()
