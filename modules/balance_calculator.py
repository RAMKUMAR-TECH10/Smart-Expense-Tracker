"""Balance, income, expense and savings calculations."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from config import EXPENSE, INCOME
from modules.database import Database
from modules.transaction_manager import decimal_amount

ZERO = Decimal("0.00")


class BalanceCalculator:
    def __init__(self, database: Database) -> None:
        self.db = database

    def totals(self) -> dict[str, Decimal]:
        rows = self.db.fetchall(
            """SELECT transaction_type, COALESCE(SUM(amount), 0) AS total
               FROM transactions GROUP BY transaction_type"""
        )
        totals = {row["transaction_type"]: decimal_amount(row["total"]) for row in rows}
        income = totals.get(INCOME, ZERO)
        expenses = totals.get(EXPENSE, ZERO)
        return {"income": income, "expenses": expenses, "balance": income - expenses}

    def total_income(self) -> Decimal:
        return self.totals()["income"]

    def total_expenses(self) -> Decimal:
        return self.totals()["expenses"]

    def balance(self) -> Decimal:
        return self.totals()["balance"]

    def monthly_totals(self, month: int | None = None, year: int | None = None) -> dict[str, Decimal]:
        today = date.today()
        rows = self.db.fetchall(
            """SELECT transaction_type, COALESCE(SUM(amount), 0) AS total
               FROM transactions
               WHERE strftime('%m', transaction_date) = ?
                 AND strftime('%Y', transaction_date) = ?
               GROUP BY transaction_type""",
            (f"{month or today.month:02d}", str(year or today.year)),
        )
        totals = {row["transaction_type"]: decimal_amount(row["total"]) for row in rows}
        income = totals.get(INCOME, ZERO)
        expenses = totals.get(EXPENSE, ZERO)
        return {
            "income": income,
            "expenses": expenses,
            "savings": income - expenses,
        }

    def monthly_savings(self, month: int | None = None, year: int | None = None) -> Decimal:
        return self.monthly_totals(month, year)["savings"]

    def summary(self) -> dict[str, Any]:
        all_time = self.totals()
        monthly = self.monthly_totals()
        return {**{f"total_{key}": value for key, value in all_time.items()}, **monthly}
