import tempfile
from pathlib import Path
import unittest
from sys import path
path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import init_db, add_seed, list_seeds, update_seed_state, SeedError

class OrchardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "orchard.sqlite3"
        init_db(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_seed_survives_reopening_database(self):
        seed = add_seed(self.db, "A private photo gallery", "For the family")
        items = list_seeds(self.db)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], seed["id"])
        self.assertEqual(items[0]["detail"], "For the family")
        init_db(self.db)
        self.assertEqual(len(list_seeds(self.db)), 1)

    def test_rejects_blank_or_too_long(self):
        for title in ("   ", "a"*121, 42):
            with self.subTest(title=str(title)[:15]), self.assertRaises(SeedError):
                add_seed(self.db, title)
        self.assertEqual(list_seeds(self.db), [])

    def test_state_transitions_are_bounded(self):
        seed = add_seed(self.db, "Simple idea")
        with self.assertRaises(SeedError):
            update_seed_state(self.db, seed["id"], "PLANNED", 1)
        exploring = update_seed_state(self.db, seed["id"], "EXPLORING", 1)
        self.assertEqual(exploring["version"], 2)
        planned = update_seed_state(self.db, seed["id"], "PLANNED", 2)
        self.assertEqual(planned["state"], "PLANNED")
        with self.assertRaises(SeedError):
            update_seed_state(self.db, seed["id"], "PARKED", 2)  # stale version
        self.assertEqual(list_seeds(self.db)[0]["version"], 3)

    def test_rejects_unknown_seeds_and_invalid_state(self):
        seed = add_seed(self.db, "Find and test")
        with self.assertRaises(SeedError):
            update_seed_state(self.db, seed["id"], "HARVESTED", 1)
        with self.assertRaises(SeedError):
            update_seed_state(self.db, "invalid-id", "EXPLORING", 1)
        with self.assertRaises(SeedError):
            update_seed_state(self.db, seed["id"], "EXPLORING", True)

if __name__ == "__main__":
    unittest.main()
