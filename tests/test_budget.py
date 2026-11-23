"""Tests for budget validation, persistence and over-budget detection."""

import tempfile
import unittest
from pathlib import Path

from modules.budget_manager import BudgetManager
from modules.database import Database
from modules.error_handler import ValidationError
from modules.transaction_manager import TransactionManager


class BudgetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.db")
        self.budgets = BudgetManager(self.db)
        self.transactions = TransactionManager(self.db)
        self.food_id = self.db.fetchone(
            "SELECT category_id FROM categories WHERE category_name = 'Food'"
        )["category_id"]

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def _budget(self, amount: str = "5000") -> dict:
        return {
            "category_id": self.food_id,
            "budget_amount": amount,
            "month": 1,
            "year": 2026,
        }

    def test_valid_budget_saved(self) -> None:
        budget_id = self.budgets.set_budget(self._budget())
        budget = self.budgets.get_budget(self.food_id, 1, 2026)
        self.assertIsNotNone(budget)
        self.assertEqual(budget["budget_id"], budget_id)
        self.assertEqual(float(budget["budget_amount"]), 5000)

    def test_invalid_budget_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            self.budgets.set_budget(self._budget("-100"))
        with self.assertRaises(ValidationError):
            self.budgets.set_budget(self._budget("100") | {"month": 13})

    def test_exceeded_budget_warning(self) -> None:
        self.budgets.set_budget(self._budget("1000"))
        self.transactions.add(
            {
                "title": "Expensive dinner",
                "amount": "1500",
                "transaction_type": "Expense",
                "category_id": self.food_id,
                "transaction_date": "2026-01-10",
                "description": "",
            }
        )
        status = self.budgets.get_budget_status(1, 2026)
        self.assertEqual(len(status), 1)
        self.assertTrue(status[0]["exceeded"])
        self.assertEqual(status[0]["percentage"], 150.0)
        warnings = self.budgets.check_budget_warnings(1, 2026)
        self.assertTrue(any("exceeded" in warning for warning in warnings))

    def test_updating_existing_budget_does_not_duplicate(self) -> None:
        self.budgets.set_budget(self._budget("5000"))
        self.budgets.set_budget(self._budget("7000"))
        self.assertEqual(len(self.budgets.get_monthly_budgets(1, 2026)), 1)
        self.assertEqual(
            float(self.budgets.get_budget(self.food_id, 1, 2026)["budget_amount"]), 7000
        )


if __name__ == "__main__":
    unittest.main()
