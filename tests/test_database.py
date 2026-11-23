"""Tests for database setup and persistence."""

import tempfile
import unittest
from pathlib import Path

from modules.database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        self.db = Database(self.db_path)

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def test_tables_created(self) -> None:
        names = {
            row["name"]
            for row in self.db.fetchall("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        self.assertTrue({"transactions", "categories", "budgets", "settings"}.issubset(names))

    def test_default_categories_seeded(self) -> None:
        categories = self.db.fetchall("SELECT * FROM categories")
        self.assertGreaterEqual(len(categories), 10)
        self.assertTrue(any(row["category_name"] == "Food" for row in categories))

    def test_settings_round_trip(self) -> None:
        self.db.set_setting("theme", "dark")
        self.assertEqual(self.db.get_setting("theme"), "dark")
        self.assertEqual(self.db.get_setting("missing", "fallback"), "fallback")

    def test_persists_after_reopen(self) -> None:
        self.db.execute("INSERT INTO categories (category_name, category_type) VALUES (?, ?)", ("Pets", "Expense"))
        self.db.close()
        self.db = Database(self.db_path)
        self.assertIsNotNone(
            self.db.fetchone("SELECT * FROM categories WHERE category_name = 'Pets'")
        )


if __name__ == "__main__":
    unittest.main()
