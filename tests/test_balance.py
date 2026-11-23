"""Tests for income, expense, balance and savings calculations."""

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from modules.balance_calculator import BalanceCalculator
from modules.database import Database
from modules.transaction_manager import TransactionManager


class BalanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.db")
        self.manager = TransactionManager(self.db)
        self.calculator = BalanceCalculator(self.db)
        self.food_id = self.db.fetchone(
            "SELECT category_id FROM categories WHERE category_name = 'Food'"
        )["category_id"]
        self.salary_id = self.db.fetchone(
            "SELECT category_id FROM categories WHERE category_name = 'Salary'"
        )["category_id"]

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def _add(self, title: str, amount: str, kind: str, category_id: int, day: int) -> None:
        self.manager.add(
            {
                "title": title,
                "amount": amount,
                "transaction_type": kind,
                "category_id": category_id,
                "transaction_date": f"2026-01-{day:02d}",
                "description": "",
            }
        )

    def test_totals_and_balance(self) -> None:
        self._add("Salary", "35000", "Income", self.salary_id, 1)
        self._add("Rent", "10000", "Expense", self.food_id, 2)
        totals = self.calculator.totals()
        self.assertEqual(totals["income"], Decimal("35000.00"))
        self.assertEqual(totals["expenses"], Decimal("10000.00"))
        self.assertEqual(totals["balance"], Decimal("25000.00"))
        self.assertEqual(self.calculator.balance(), Decimal("25000.00"))

    def test_monthly_savings(self) -> None:
        self._add("Salary", "20000", "Income", self.salary_id, 1)
        self._add("Food", "5000", "Expense", self.food_id, 3)
        monthly = self.calculator.monthly_totals(1, 2026)
        self.assertEqual(monthly["savings"], Decimal("15000.00"))
        self.assertEqual(self.calculator.monthly_savings(1, 2026), Decimal("15000.00"))

    def test_empty_database_totals_are_zero(self) -> None:
        totals = self.calculator.totals()
        self.assertEqual(totals["balance"], Decimal("0.00"))


if __name__ == "__main__":
    unittest.main()
