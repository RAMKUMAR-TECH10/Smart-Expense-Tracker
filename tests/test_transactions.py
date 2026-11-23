"""Tests for transaction management, search and export."""

import csv
import tempfile
import unittest
from pathlib import Path

from modules.database import Database
from modules.export_manager import ExportManager
from modules.report_generator import ReportGenerator
from modules.error_handler import ValidationError
from modules.transaction_manager import TransactionManager


class TransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.db")
        self.manager = TransactionManager(self.db)
        self.food_id = self.db.fetchone(
            "SELECT category_id FROM categories WHERE category_name = 'Food'"
        )["category_id"]
        self.salary_id = self.db.fetchone(
            "SELECT category_id FROM categories WHERE category_name = 'Salary'"
        )["category_id"]

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def _expense(self, title: str = "Groceries", amount: str = "250") -> dict:
        return {
            "title": title,
            "amount": amount,
            "transaction_type": "Expense",
            "category_id": self.food_id,
            "transaction_date": "2026-01-15",
            "description": "Weekly shopping",
        }

    def test_add_valid_expense(self) -> None:
        transaction_id = self.manager.add(self._expense())
        record = self.manager.get(transaction_id)
        self.assertIsNotNone(record)
        self.assertEqual(record["title"], "Groceries")
        self.assertEqual(float(record["amount"]), 250)

    def test_add_valid_income(self) -> None:
        transaction_id = self.manager.add(
            {
                "title": "Monthly salary",
                "amount": "35000",
                "transaction_type": "Income",
                "category_id": self.salary_id,
                "transaction_date": "2026-01-01",
                "description": "",
            }
        )
        self.assertEqual(self.manager.get(transaction_id)["transaction_type"], "Income")

    def test_negative_amount_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.add(self._expense(amount="-10"))

    def test_empty_title_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.add(self._expense(title=""))

    def test_wrong_category_type_rejected(self) -> None:
        data = self._expense()
        data["category_id"] = self.salary_id
        with self.assertRaises(ValidationError):
            self.manager.add(data)

    def test_update_and_delete(self) -> None:
        transaction_id = self.manager.add(self._expense())
        data = self._expense("Updated", "300")
        self.assertTrue(self.manager.update(transaction_id, data))
        self.assertEqual(self.manager.get(transaction_id)["title"], "Updated")
        self.assertTrue(self.manager.delete(transaction_id))
        self.assertIsNone(self.manager.get(transaction_id))

    def test_search_and_date_filter(self) -> None:
        self.manager.add(self._expense("Lunch", "200"))
        self.manager.add(self._expense("Dinner", "400"))
        self.assertEqual(len(self.manager.search("lunch")), 1)
        self.assertEqual(len(self.manager.search("", "Expense")), 2)
        self.assertEqual(len(self.manager.filter_by_date("2026-02-01", "2026-02-28")), 0)

    def test_invalid_date_filter_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.filter_by_date("32-01-2026", "2026-01-31")

    def test_tiny_amount_rounds_to_zero_and_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.add(self._expense(amount="0.001"))

    def test_monthly_report_handles_february(self) -> None:
        report = ReportGenerator(self.db).monthly_report(2, 2026)
        self.assertEqual(report["period"], "02/2026")
        self.assertEqual(report["transactions"], [])

    def test_csv_export(self) -> None:
        self.manager.add(self._expense())
        path = ExportManager(self.temp_dir.name).export_transactions(self.manager.get_all())
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["title"], "Groceries")


if __name__ == "__main__":
    unittest.main()
