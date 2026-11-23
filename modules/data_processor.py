"""Data preparation and financial analytics using pandas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd

from config import EXPENSE, INCOME
from modules.balance_calculator import BalanceCalculator
from modules.database import Database
from modules.transaction_manager import decimal_amount

COLUMNS = [
    "transaction_id",
    "title",
    "amount",
    "transaction_type",
    "category_id",
    "transaction_date",
    "description",
    "category_name",
    "category_type",
]


class DataProcessor:
    def __init__(self, database: Database, calculator: BalanceCalculator | None = None) -> None:
        self.db = database
        self.calculator = calculator or BalanceCalculator(database)

    def transactions_frame(self) -> pd.DataFrame:
        rows = self.db.fetchall(
            """SELECT t.transaction_id, t.title, t.amount, t.transaction_type, t.category_id,
                      t.transaction_date, t.description, c.category_name, c.category_type
               FROM transactions t JOIN categories c ON t.category_id = c.category_id
               ORDER BY t.transaction_date, t.transaction_id"""
        )
        frame = pd.DataFrame(rows, columns=COLUMNS)
        if frame.empty:
            return pd.DataFrame(columns=COLUMNS)
        frame["transaction_date"] = pd.to_datetime(frame["transaction_date"], errors="coerce")
        frame["amount_decimal"] = frame["amount"].apply(decimal_amount)
        frame["month"] = frame["transaction_date"].dt.to_period("M").astype(str)
        return frame

    def category_spending(self, month: int | None = None, year: int | None = None) -> pd.DataFrame:
        frame = self.transactions_frame()
        if frame.empty:
            return pd.DataFrame(columns=["category_name", "amount"])
        frame = frame[frame["transaction_type"] == EXPENSE]
        if month and year:
            frame = frame[
                (frame["transaction_date"].dt.month == month)
                & (frame["transaction_date"].dt.year == year)
            ]
        if frame.empty:
            return pd.DataFrame(columns=["category_name", "amount"])
        result = (
            frame.groupby("category_name", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        return result.reset_index(drop=True)

    def monthly_trend(self, months: int = 6) -> pd.DataFrame:
        frame = self.transactions_frame()
        if frame.empty:
            return pd.DataFrame(columns=["month", "income", "expense", "savings"])
        frame = frame[frame["month"] >= self._month_key(months)]
        grouped = (
            frame.groupby(["month", "transaction_type"])["amount"].sum().unstack(fill_value=0)
        )
        for column in (INCOME, EXPENSE):
            if column not in grouped.columns:
                grouped[column] = 0.0
        grouped = grouped.reset_index().rename(columns={INCOME: "income", EXPENSE: "expense"})
        grouped["savings"] = grouped["income"] - grouped["expense"]
        return grouped[["month", "income", "expense", "savings"]].sort_values("month")

    def month_comparison(self) -> dict[str, Decimal]:
        today = date.today()
        current = self.calculator.monthly_totals(today.month, today.year)
        previous_month = today.month - 1 or 12
        previous_year = today.year if today.month > 1 else today.year - 1
        previous = self.calculator.monthly_totals(previous_month, previous_year)
        return {
            "current_expenses": current["expenses"],
            "previous_expenses": previous["expenses"],
            "difference": current["expenses"] - previous["expenses"],
        }

    def chart_data(self) -> dict[str, Any]:
        monthly = self.calculator.monthly_totals()
        return {
            "balance_cards": self.calculator.summary(),
            "category_spending": self.category_spending(),
            "monthly_trend": self.monthly_trend(),
            "monthly": monthly,
            "comparison": self.month_comparison(),
        }

    @staticmethod
    def _month_key(months: int) -> str:
        today = date.today()
        year, month = today.year, today.month - (months - 1)
        while month <= 0:
            month += 12
            year -= 1
        return f"{year:04d}-{month:02d}"
