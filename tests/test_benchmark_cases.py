"""Verify the reusable comparison gates using only authored synthetic fixtures.

These tests do not invoke models or execute model-generated results.
"""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / 'benchmarks'
spec = importlib.util.spec_from_file_location('heading_acceptance', BENCHMARKS / 'acceptance/heading.py')
heading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(heading)

class BenchmarkCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name) / 'project'

    def tearDown(self):
        self.temp.cleanup()

    def test_heading_gate_rejects_unchanged_page(self):
        shutil.copytree(BENCHMARKS / 'cases/heading', self.project)
        with self.assertRaises(ValueError):
            heading.check(self.project)

    def test_heading_gate_accepts_exact_edit(self):
        shutil.copytree(BENCHMARKS / 'cases/heading', self.project)
        (self.project / 'index.html').write_bytes(heading.AFTER)
        heading.check(self.project)

    def test_heading_gate_rejects_unrelated_change(self):
        shutil.copytree(BENCHMARKS / 'cases/heading', self.project)
        (self.project / 'index.html').write_bytes(heading.AFTER + b'<!-- unrelated edit -->')
        with self.assertRaises(ValueError):
            heading.check(self.project)

    def test_heading_gate_rejects_symlink(self):
        self.project.mkdir()
        reference = Path(self.temp.name) / 'other.html'
        reference.write_bytes(heading.AFTER)
        (self.project / 'index.html').symlink_to(reference)
        with self.assertRaises(ValueError):
            heading.check(self.project)

    def test_mean_baseline_green_does_not_prove_acceptance(self):
        shutil.copytree(BENCHMARKS / 'cases/mean', self.project)
        baseline = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'],
                                  cwd=self.project, capture_output=True, text=True, timeout=5)
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        acceptance = subprocess.run([sys.executable, str(BENCHMARKS / 'acceptance/mean.py'), str(self.project)],
                                    cwd=self.project, capture_output=True, text=True, timeout=5)
        self.assertNotEqual(acceptance.returncode, 0)
        self.assertIn('FAIL: test_fractional_result', acceptance.stderr)
        self.assertIn('FAIL: test_negative_fractional_result', acceptance.stderr)

    def test_mean_gate_accepts_fractional_fix_preserving_empty_contract(self):
        shutil.copytree(BENCHMARKS / 'cases/mean', self.project)
        implementation = self.project / 'mean.py'
        implementation.write_text(implementation.read_text().replace('sum(values) // len(values)', 'sum(values) / len(values)'))
        acceptance = subprocess.run([sys.executable, str(BENCHMARKS / 'acceptance/mean.py'), str(self.project)],
                                    cwd=self.project, capture_output=True, text=True, timeout=5)
        self.assertEqual(acceptance.returncode, 0, acceptance.stderr)

if __name__ == '__main__':
    unittest.main()
