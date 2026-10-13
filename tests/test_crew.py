import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crew import Crew, CrewError, OwnerDecision, CodexAdapter, BoundedRPC, FILES, snapshot
SERVER = r'''
import json, sys, time
mode=sys.argv[1]
for line in sys.stdin:
 m=json.loads(line); method=m['method']; rid=m.get('id')
 if rid is None: continue
 if method=='initialize': result={}
 elif method=='command/exec':
  if 'ORCHARD_SANDBOX_READY' in str(m): result={'exitCode':71 if mode=='sandbox' else 0,'stdout':'ORCHARD_SANDBOX_READY','stderr':''}
  else: result={'exitCode':1 if mode=='fail' else 0,'stdout':'','stderr':'Ran 0 tests\nOK' if mode=='zero' else 'Ran 4 tests\nOK'}
 elif method=='thread/start': result={'thread':{'id':'thread'},'activePermissionProfile':{'id':'orchard'},'approvalsReviewer':'user','approvalPolicy':'on-request'}
 elif method=='turn/start':
  if mode=='edit':
   from pathlib import Path
   Path('app.py').write_text('# implemented fixture change\n')
  print(json.dumps({'id':rid,'result':{'turn':{'id':'turn'}}}),flush=True)
  if mode=='approval': print(json.dumps({'id':90,'method':'item/commandExecution/requestApproval','params':{}}),flush=True)
  elif mode=='timeout': time.sleep(5)
  elif mode=='overflow': print('x'*100000,flush=True)
  else:
   print(json.dumps({'method':'item/completed','params':{'threadId':'thread','item':{'type':'agentMessage','text':'Implemented requested behavior.'}}}),flush=True)
   print(json.dumps({'method':'turn/completed','params':{'threadId':'thread','turn':{'id':'turn','status':'failed' if mode=='turnfail' else 'completed'}}}),flush=True)
  continue
 else: result={}
 print(json.dumps({'id':rid,'result':result}),flush=True)
'''
class CrewTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir()
  for file in FILES:
   p=self.source/file;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# safe project file\n')
  self.script=self.root/'server.py';self.script.write_text(SERVER)
  self.home=self.root/'home';self.home.mkdir();(self.home/'auth.json').write_text('{}')
 def tearDown(self):self.temp.cleanup()
 def adapter_run(self,mode,seconds=2,budget=1048576):
  work=self.root/'workspace';snapshot(self.source,work);original=BoundedRPC;instances=[]
  def factory(argv,cwd,home,deadline,byte_limit):
   rpc=original([sys.executable,str(self.script),mode],cwd,home,deadline,budget);instances.append(rpc);return rpc
  with patch('crew.BoundedRPC',factory):
   try:return CodexAdapter(sys.executable,self.home).run(work,'Change one behavior',time.monotonic()+seconds,lambda t:None)
   finally:
    for rpc in instances:self.assertIsNotNone(rpc.process.poll(),'child leaked')
 def test_protocol_completed_and_tests_pass(self):self.assertIn('Implemented',self.adapter_run('ok'))
 def test_failed_tests(self):
  with self.assertRaisesRegex(CrewError,'tests failed'):self.adapter_run('fail')
 def test_zero_tests(self):
  with self.assertRaisesRegex(CrewError,'no tests'):self.adapter_run('zero')
 def test_failed_turn(self):
  with self.assertRaisesRegex(CrewError,'did not complete'):self.adapter_run('turnfail')
 def test_approval_stops(self):
  with self.assertRaisesRegex(OwnerDecision,'no permission granted'):self.adapter_run('approval')
 def test_sandbox_failure_before_turn(self):
  with self.assertRaisesRegex(CrewError,'No model task started'):self.adapter_run('sandbox')
 def test_timeout_kills_child(self):
  with self.assertRaisesRegex(CrewError,'time budget'):self.adapter_run('timeout',seconds=.2)
 def test_output_budget(self):
  with self.assertRaisesRegex(CrewError,'output budget'):self.adapter_run('overflow',budget=4096)
 def test_snapshot_excludes_db_and_refuses_symlink(self):
  (self.source/'orchard.sqlite3').write_text('private seed data');target=self.root/'snapshot';snapshot(self.source,target)
  self.assertFalse((target/'orchard.sqlite3').exists());(self.source/'app.py').unlink();(self.source/'app.py').symlink_to(self.script)
  with self.assertRaisesRegex(CrewError,'symlinks'):snapshot(self.source,self.root/'second')
 def test_secret_guard(self):
  (self.source/'app.py').write_text('sk-'+'A'*30)
  with self.assertRaises(OwnerDecision):snapshot(self.source,self.root/'blocked')
  crew=Crew(self.root/'db',self.root/'runs',self.source,None)
  with self.assertRaises(CrewError):crew.submit('sk-'+'A'*30)
 def test_permission_single_worker_no_retry_and_persistence(self):
  ready=threading.Event();release=threading.Event()
  class Fake:
   def run(self,workspace,request,deadline,record):ready.set();release.wait(2);record('Fixture tests passed.');return 'Fixture completion'
  crew=Crew(self.root/'db',self.root/'runs',self.source,Fake());first=crew.submit('One task');second=crew.submit('Another')
  with self.assertRaises(CrewError):crew.start(first,False)
  crew.start(first,True);self.assertTrue(ready.wait(2))
  try:
   with self.assertRaisesRegex(CrewError,'busy'):crew.start(second,True)
  finally:release.set()
  self.assertTrue(crew.lock.acquire(timeout=2));crew.lock.release()
  with self.assertRaisesRegex(CrewError,'already attempted'):crew.start(first,True)
  restored=Crew(self.root/'db',self.root/'runs',self.source,Fake());results={t['id']:t for t in restored.list()}
  self.assertEqual(results[first]['status'],'DONE');self.assertEqual(results[second]['status'],'NEEDS_OWNER_DECISION')
 def test_restart_and_exception_block(self):
  class Fail:
   def run(self,*args):raise RuntimeError('Missing integration')
  crew=Crew(self.root/'db',self.root/'runs',self.source,Fail());tid=crew.submit('Task');crew.start(tid,True)
  self.assertTrue(crew.lock.acquire(timeout=2));crew.lock.release();self.assertEqual(crew.list()[0]['status'],'BLOCKED')
  with crew.connect() as conn:conn.execute("UPDATE tasks SET status='RUNNING'")
  self.assertIn('restarted',Crew(self.root/'db',self.root/'runs',self.source,Fail()).list()[0]['evidence'])
 def test_weakened_tests_block(self):
  class Weaken:
   def run(self,workspace,*args):(workspace/'tests/test_app.py').write_text('# disabled');return 'done'
  crew=Crew(self.root/'db',self.root/'runs',self.source,Weaken());tid=crew.submit('Task');crew.start(tid,True)
  self.assertTrue(crew.lock.acquire(timeout=2));crew.lock.release();self.assertEqual(crew.list()[0]['status'],'BLOCKED');self.assertIn('Existing tests',crew.list()[0]['evidence'])

 def test_end_to_end_adapter_receipt_and_original_preserved(self):
  real=BoundedRPC
  def factory(argv,cwd,home,deadline,byte_limit):
   return real([sys.executable,str(self.script),'edit'],cwd,home,deadline,byte_limit)
  crew=Crew(self.root/'db',self.root/'runs',self.source,CodexAdapter(sys.executable,self.home))
  original=(self.source/'app.py').read_bytes()
  with patch('crew.BoundedRPC',factory):
   tid=crew.submit('Fixture: implement bounded change');crew.start(tid,True)
   self.assertTrue(crew.lock.acquire(timeout=3));crew.lock.release()
  result=crew.list()[0]
  self.assertEqual(result['status'],'DONE')
  self.assertEqual(result['receipt']['changed_files'],['app.py'])
  self.assertEqual((self.source/'app.py').read_bytes(),original)
  self.assertIn('Project test output',result['evidence'])

 def test_http_routes_submit_consent_and_foreign_origin(self):
  import io
  from types import SimpleNamespace
  from app import Handler
  crew=Crew(self.root/'db',self.root/'runs',self.source,None)
  def post(path,data,origin='http://127.0.0.1:8765'):
   h=Handler.__new__(Handler);h.crew=crew;h.server=SimpleNamespace(server_port=8765);h.path=path
   body=json.dumps(data).encode();h.headers={'Host':'127.0.0.1:8765','Origin':origin,'Content-Type':'application/json','Content-Length':str(len(body))};h.rfile=io.BytesIO(body)
   out=[];h._json=lambda status,obj:out.append((status,obj));h.do_POST();return out[0]
  status,result=post('/api/tasks',{'request':'One task'})
  self.assertEqual(status,201);self.assertEqual(crew.list()[0]['status'],'NEEDS_OWNER_DECISION')
  self.assertEqual(post('/api/tasks/'+result['id']+'/approve',{'consent':'true'})[0],400)
  self.assertEqual(post('/api/tasks',{'request':'Other'},'https://foreign.example')[0],403)

 def test_sqlite_runtime_grants_only_exact_library_and_target(self):
  from crew import sqlite_runtime_grants
  library=self.root/'runtime'/'libsqlite3.dylib';library.parent.mkdir();library.write_bytes(b'fixture library')
  alias=self.root/'libsqlite3.dylib';alias.symlink_to(library)
  grants=sqlite_runtime_grants([alias,self.root/'missing.dylib'])
  self.assertEqual(grants,{str(alias):'read',str(library.resolve()):'read',str(library.parent.resolve()):'read'})
  self.assertNotIn(str(library.parent.parent),grants)

 def test_preflight_loads_sqlite_before_starting_model(self):
  commands=[]
  class RefuseSQLite:
   def __init__(self,*args):self.log=[]
   def send(self,*args):pass
   def close(self):pass
   def call(self,method,params):
    commands.append(method)
    if method=='initialize':return {}
    if method=='command/exec':
     self_code=' '.join(params['command'])
     if 'import pathlib, socket, sys, sqlite3' not in self_code or "SELECT 1" not in self_code:
      raise AssertionError('SQLite was not checked')
     return {'exitCode':1,'stdout':'','stderr':'Library not loaded: libsqlite3.dylib (blocked by sandbox)'}
    raise AssertionError('Model must not start after SQLite failure')
  workspace=self.root/'preflight';snapshot(self.source,workspace);evidence=[]
  with patch('crew.BoundedRPC',RefuseSQLite),self.assertRaisesRegex(CrewError,'No model task started'):
   CodexAdapter(sys.executable,self.home).run(workspace,'One task',time.monotonic()+2,evidence.append)
  self.assertEqual(commands,['initialize','command/exec'])
  self.assertTrue(any('libsqlite3.dylib' in line for line in evidence))
