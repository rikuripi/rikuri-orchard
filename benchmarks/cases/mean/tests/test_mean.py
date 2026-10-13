import unittest
from mean import mean

class BaselineMeanTests(unittest.TestCase):
    def test_integer_mean(self):
        self.assertEqual(mean([2, 4]), 3)

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            mean([])

if __name__ == '__main__':
    unittest.main()
