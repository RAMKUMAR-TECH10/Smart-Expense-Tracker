"""Monthly budget management and monitoring."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from config import EXPENSE
from modules.database import Database
from modules.error_handler import ValidationError, get_logger
from modules.validation import validate_budget
from modules.transaction_manager import decimal_amount

logger = get_logger("budgets")


class BudgetManager:
    def __init__(self, database: Database) -> None:
        self.db = database

    def set_budget(self, data: dict[str, Any]) -> int:
        record = validate_budget(data)
        category = self.db.fetchone(
            "SELECT category_type FROM categories WHERE category_id = ?", (record["category_id"],)
        )
        if category is None:
            raise ValidationError("Selected category does not exist.")
        if category["category_type"] != EXPENSE:
            raise ValidationError("Budgets can only be set for expense categories.")
        existing = self.get_budget(record["category_id"], record["month"], record["year"])
        if existing:
            self.db.execute(
                "UPDATE budgets SET budget_amount = ? WHERE budget_id = ?",
                (float(record["budget_amount"]), existing["budget_id"]),
            )
            logger.info("Updated budget for category %s", record["category_id"])
            return int(existing["budget_id"])
        cursor = self.db.execute(
            """INSERT INTO budgets (category_id, budget_amount, month, year)
               VALUES (?, ?, ?, ?)""",
            (
                record["category_id"],
                float(record["budget_amount"]),
                record["month"],
                record["year"],
            ),
        )
        logger.info("Created budget for category %s", record["category_id"])
        return int(cursor.lastrowid or 0)

    def get_budget(self, category_id: int, month: int, year: int) -> dict | None:
        return self.db.fetchone(
            """SELECT b.*, c.category_name FROM budgets b
               JOIN categories c ON b.category_id = c.category_id
               WHERE b.category_id = ? AND b.month = ? AND b.year = ?""",
            (category_id, month, year),
        )

    def delete_budget(self, budget_id: int) -> bool:
        return self.db.execute("DELETE FROM budgets WHERE budget_id = ?", (budget_id,)).rowcount > 0

    def get_monthly_budgets(self, month: int | None = None, year: int | None = None) -> list[dict]:
        today = date.today()
        return self.db.fetchall(
            """SELECT b.*, c.category_name FROM budgets b
               JOIN categories c ON b.category_id = c.category_id
               WHERE b.month = ? AND b.year = ? ORDER BY c.category_name""",
            (month or today.month, year or today.year),
        )

    def get_budget_status(
        self, month: int | None = None, year: int | None = None
    ) -> list[dict[str, Any]]:
        today = date.today()
        month, year = month or today.month, year or today.year
        budgets = self.get_monthly_budgets(month, year)
        status: list[dict[str, Any]] = []
        for budget in budgets:
            rows = self.db.fetchall(
                """SELECT COALESCE(SUM(amount), 0) AS total FROM transactions
                   WHERE category_id = ? AND transaction_type = ?
                     AND strftime('%m', transaction_date) = ?
                     AND strftime('%Y', transaction_date) = ?""",
                (
                    budget["category_id"],
                    EXPENSE,
                    f"{month:02d}",
                    str(year),
                ),
            )
            spent = decimal_amount(rows[0]["total"] if rows else 0)
            limit = decimal_amount(budget["budget_amount"])
            percent = float((spent / limit) * 100) if limit > 0 else 0.0
            status.append(
                {
                    **budget,
                    "spent": spent,
                    "remaining": limit - spent,
                    "percentage": round(percent, 2),
                    "exceeded": spent > limit,
                }
            )
        return status

    def check_budget_warnings(self, month: int | None = None, year: int | None = None) -> list[str]:
        warnings = []
        for item in self.get_budget_status(month, year):
            if item["exceeded"]:
                warnings.append(
                    f"{item['category_name']} budget exceeded by {item['remaining'] * -1:.2f}"
                )
            elif item["percentage"] >= 90:
                warnings.append(f"{item['category_name']} budget is {item['percentage']:.0f}% used")
        for message in warnings:
            logger.warning("Budget warning: %s", message)
        return warnings
