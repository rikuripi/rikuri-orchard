"""Run ONLY inside an approved sandbox: imports candidate-generated Python.

Usage: sandboxed-python this_file.py /absolute/path/to/candidate/project
Do not run an unreviewed model result on the host.
"""
from pathlib import Path
import sys
import unittest

if len(sys.argv) != 2:
    raise SystemExit('Expected one candidate project path')
project = Path(sys.argv.pop()).resolve()
if (project / 'mean.py').is_symlink():
    raise SystemExit('Candidate implementation must not be a symlink')
sys.path.insert(0, str(project))
from mean import mean

class IndependentMeanAcceptance(unittest.TestCase):
    def test_fractional_result(self):
        self.assertAlmostEqual(mean([1, 2]), 1.5)

    def test_negative_fractional_result(self):
        self.assertAlmostEqual(mean([-2, -1]), -1.5)

    def test_single_value(self):
        self.assertEqual(mean([3]), 3)

    def test_empty_input_contract(self):
        with self.assertRaises(ValueError):
            mean([])

unittest.main()
