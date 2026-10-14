import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review import ReviewError, ReviewStore, read_file

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'source'; self.source.mkdir()
        self.runs = self.base / 'runs'; self.runs.mkdir()
        self.db = self.base / 'data.sqlite3'
        self.files = ('app.py', 'index.html', 'tests/test_app.py')
        for relative in self.files:
            p = self.source / relative; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('original '+relative+'\n')
        self.store = ReviewStore(self.db,self.runs,self.source,self.files)
        self.tid = str(uuid.uuid4())
        self.workspace = self.runs/self.tid/'workspace'
        shutil.copytree(self.source,self.workspace)
        self.before = {p: (self.source/p).read_bytes() for p in self.files}
        self.hashes = {p: hashlib.sha256(v).hexdigest() for p,v in self.before.items()}
        (self.workspace/'index.html').write_text('reviewed heading\n')
        self.rid = None

    def tearDown(self):
        self.temp.cleanup()

    def capture(self):
        self.rid = self.store.capture(self.tid,self.hashes,self.workspace,'Ran 3 tests\nOK\nFixture evidence; not a live model run.')
        return self.rid

    def apply(self):
        return self.store.operate(self.tid,self.rid,True)

    def restore(self):
        return self.store.operate(self.tid,self.rid,True,restore=True)

    def test_read_only_review_and_exact_diff(self):
        self.capture();review=self.store.get(self.tid)
        self.assertEqual(review['status'],'READY')
        self.assertEqual([c['path'] for c in review['changes']],['index.html'])
        self.assertIn('+reviewed heading',review['changes'][0]['diff'])
        self.assertIn('+original index.html',review['changes'][0]['recovery_diff'])
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])
        self.assertEqual(self.store.get(self.tid)['review_id'],self.rid)

    def test_explicit_consent_and_current_digest_required(self):
        self.capture()
        for consent in (False,None,'true',1):
            with self.assertRaises(ReviewError):self.store.operate(self.tid,self.rid,consent)
        with self.assertRaises(ReviewError):self.store.operate(self.tid,'stale',True)
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])

    def test_apply_backup_and_approved_recovery(self):
        self.capture();review=self.apply()
        self.assertEqual(review['status'],'APPLIED');self.assertTrue(review['recovery_available'])
        self.assertEqual((self.source/'index.html').read_text(),'reviewed heading\n')
        with self.assertRaises(ReviewError):self.store.operate(self.tid,self.rid,False,restore=True)
        self.assertEqual(self.restore()['status'],'RESTORED')
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])
        self.assertIn('original index.html',self.store.get(self.tid)['changes'][0]['diff'])

    def test_source_drift_even_in_unchanged_file_rejects_apply(self):
        self.capture();(self.source/'app.py').write_text('owner changed this')
        with self.assertRaisesRegex(ReviewError,'Working project changed'):self.apply()
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])

    def test_result_drift_rejects_and_keeps_original_review(self):
        self.capture();(self.workspace/'index.html').write_text('different candidate')
        with self.assertRaisesRegex(ReviewError,'result changed'):self.apply()
        self.assertIn('reviewed heading',self.store.get(self.tid)['changes'][0]['diff'])
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])

    def test_duplicate_requests_do_not_overwrite_newer_owner_work(self):
        self.capture();self.apply();(self.source/'index.html').write_text('newer owner edit')
        self.assertEqual(self.apply()['status'],'APPLIED')
        self.assertEqual((self.source/'index.html').read_text(),'newer owner edit')
        with self.assertRaisesRegex(ReviewError,'has changed'):self.restore()

    def test_duplicate_restore_is_idempotent(self):
        self.capture();self.apply();self.restore();(self.source/'index.html').write_text('owner edit after recovery')
        self.assertEqual(self.restore()['status'],'RESTORED')
        self.assertEqual((self.source/'index.html').read_text(),'owner edit after recovery')

    def test_source_symlink_rejects_without_touching_referent(self):
        self.capture();target=self.base/'outside';target.write_text('outside preserved')
        (self.source/'index.html').unlink();(self.source/'index.html').symlink_to(target)
        with self.assertRaises(ReviewError):self.apply()
        self.assertEqual(target.read_text(),'outside preserved')

    def test_symlink_parent_cannot_be_followed(self):
        self.capture();original=self.source/'tests';moved=self.base/'saved-tests';original.rename(moved);original.symlink_to(moved,target_is_directory=True)
        with self.assertRaises(ReviewError):self.apply()
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])

    def test_project_replacement_rejects_apply(self):
        self.capture();self.source.rename(self.base/'old-source');shutil.copytree(self.base/'old-source',self.source)
        with self.assertRaisesRegex(ReviewError,'directory changed'):self.apply()

    def test_traversal_and_binary_results_rejected(self):
        with self.assertRaises(ReviewError):read_file(self.source,'../outside')
        (self.workspace/'index.html').write_bytes(b'bad\x00binary')
        with self.assertRaisesRegex(ReviewError,'Binary'):self.capture()

    def test_new_files_and_deletions_not_automatically_applied(self):
        (self.workspace/'new.py').write_text('new source')
        with self.assertRaisesRegex(ReviewError,'New files'):self.capture()
        (self.workspace/'new.py').unlink();(self.workspace/'index.html').unlink()
        with self.assertRaises(OSError):self.capture()

    def test_protected_tests_and_manifest_changes_rejected(self):
        (self.workspace/'tests/test_app.py').write_text('weakened')
        with self.assertRaisesRegex(ReviewError,'Protected'):self.capture()
        with self.assertRaisesRegex(ReviewError,'manifest'):self.store.capture(self.tid,{'../unsafe':'bad'},self.workspace,'tests')

    def test_integrity_tampering_rejects_review(self):
        self.capture()
        with self.store.connect() as conn:conn.execute("UPDATE reviews SET payload='{}'")
        with self.assertRaisesRegex(ReviewError,'integrity'):self.store.get(self.tid)

    def test_permission_modes_preserved(self):
        os.chmod(self.source/'index.html',0o640);self.capture();self.apply()
        self.assertEqual(os.stat(self.source/'index.html').st_mode & 0o777,0o640)
        self.restore();self.assertEqual(os.stat(self.source/'index.html').st_mode & 0o777,0o640)

    def test_worker_lock_prevents_application(self):
        self.capture();self.store.lock.acquire()
        try:
            with self.assertRaisesRegex(ReviewError,'busy'):self.apply()
        finally:self.store.lock.release()

    def test_preparation_failure_leaves_sources_untouched(self):
        self.capture()
        with patch('review.os.fchmod',side_effect=OSError('injected stage failure')):
            with self.assertRaises(ReviewError):self.apply()
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])
        self.assertEqual(self.store.get(self.tid)['status'],'FAILED')
        self.assertEqual(list(self.source.glob('.orchard-stage-*')),[])

    def test_failure_after_first_write_rolls_back_all_replacements(self):
        (self.workspace/'app.py').write_text('reviewed app\n');self.capture()
        replace=self.store.replace;count=0
        def injected(path,*args):
            nonlocal count
            count+=1;replace(path,*args)
            if count==2:raise OSError('failure after second replacement')
        with patch.object(self.store,'replace',injected):
            with self.assertRaises(ReviewError):self.apply()
        self.assertEqual(self.store.get(self.tid)['status'],'FAILED')
        for path in self.files:self.assertEqual((self.source/path).read_bytes(),self.before[path])

    def test_partial_failure_preserves_conflicting_external_edit(self):
        (self.workspace/'app.py').write_text('reviewed app\n');self.capture()
        replace=self.store.replace;count=0
        def injected(path,*args):
            nonlocal count
            count+=1
            if count==2:
                (self.source/'app.py').write_text('concurrent owner content')
                raise OSError('injected conflict')
            return replace(path,*args)
        with patch.object(self.store,'replace',injected):
            with self.assertRaises(ReviewError):self.apply()
        self.assertEqual(self.store.get(self.tid)['status'],'RECOVERY_NEEDED')
        self.assertEqual((self.source/'app.py').read_text(),'concurrent owner content')
        with self.assertRaises(ReviewError):self.restore()

    def test_restart_requires_owner_recovery_without_auto_writes(self):
        self.capture();self.store.set_state(self.tid,'APPLYING','interrupted')
        (self.source/'index.html').write_text('reviewed heading\n')
        restored=ReviewStore(self.db,self.runs,self.source,self.files)
        self.assertEqual(restored.get(self.tid)['status'],'INTERRUPTED')
        self.assertEqual((self.source/'index.html').read_text(),'reviewed heading\n')
        self.assertEqual(restored.operate(self.tid,self.rid,True,restore=True)['status'],'RESTORED')

    def test_no_changes_have_no_writes_and_historical_runs_have_no_review(self):
        (self.workspace/'index.html').write_bytes(self.before['index.html']);self.capture()
        self.assertEqual(self.store.get(self.tid)['changes'],[])
        with self.assertRaises(ReviewError):self.store.get(str(uuid.uuid4()))

    def test_http_apply_origin_consent_digest_and_review(self):
        from app import Handler
        self.capture()
        def request(method,path,payload=None,origin='http://127.0.0.1:8765'):
            handler=Handler.__new__(Handler);handler.crew=SimpleNamespace(reviews=self.store);handler.server=SimpleNamespace(server_port=8765);handler.path=path
            body=json.dumps(payload or {}).encode();handler.headers={'Host':'127.0.0.1:8765','Origin':origin,'Content-Type':'application/json','Content-Length':str(len(body))};handler.rfile=io.BytesIO(body)
            output=[];handler._json=lambda status,obj:output.append((status,obj))
            getattr(handler,'do_'+method)();return output[0]
        base='/api/tasks/'+self.tid
        self.assertEqual(request('GET',base+'/review')[0],200)
        self.assertEqual(request('POST',base+'/apply',{'consent':True,'review_id':self.rid},origin='https://outside.example')[0],403)
        self.assertEqual(request('POST',base+'/apply',{'consent':False,'review_id':self.rid})[0],409)
        self.assertEqual(request('POST',base+'/apply',{'consent':True,'review_id':'stale'})[0],409)
        self.assertEqual(request('POST',base+'/apply',{'consent':True,'review_id':self.rid})[1]['review']['status'],'APPLIED')
        self.assertEqual(request('POST',base+'/restore',{'consent':True,'review_id':self.rid})[1]['review']['status'],'RESTORED')

    def test_new_file_added_after_review_is_rejected(self):
        self.capture();(self.workspace/'new.py').write_text('new result')
        with self.assertRaisesRegex(ReviewError,'New files'):self.apply()
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])

    def test_final_receipt_failure_rolls_back_file(self):
        self.capture();set_state=self.store.set_state;failed=False
        def injected(tid,state,*args):
            nonlocal failed
            if state=='APPLIED' and not failed:
                failed=True;raise RuntimeError('injected receipt failure')
            return set_state(tid,state,*args)
        with patch.object(self.store,'set_state',injected):
            with self.assertRaises(ReviewError):self.apply()
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])
        self.assertEqual(self.store.get(self.tid)['status'],'FAILED')

    def test_html_payload_is_returned_as_diff_data_without_source_writes(self):
        (self.workspace/'index.html').write_text('<img src=x onerror="alert(1)">\n')
        self.capture();view=self.store.get(self.tid)
        self.assertIn('<img src=x',view['changes'][0]['diff'])
        self.assertEqual((self.source/'index.html').read_bytes(),self.before['index.html'])

if __name__=='__main__':unittest.main()
