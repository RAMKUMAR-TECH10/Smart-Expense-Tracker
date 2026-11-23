"""Financial report generation built on processed data."""

from __future__ import annotations

import calendar
from datetime import date
from typing import Any

from config import CURRENCY_SYMBOL
from modules.balance_calculator import BalanceCalculator
from modules.budget_manager import BudgetManager
from modules.data_processor import DataProcessor
from modules.database import Database
from modules.transaction_manager import TransactionManager


class ReportGenerator:
    def __init__(self, database: Database) -> None:
        self.db = database
        self.transactions = TransactionManager(database)
        self.calculator = BalanceCalculator(database)
        self.processor = DataProcessor(database, self.calculator)
        self.budgets = BudgetManager(database)

    def dashboard_report(self) -> dict[str, Any]:
        totals = self.calculator.totals()
        monthly = self.calculator.monthly_totals()
        return {
            "total_balance": totals["balance"],
            "total_income": totals["income"],
            "total_expenses": totals["expenses"],
            "monthly_savings": monthly["savings"],
            "monthly_income": monthly["income"],
            "monthly_expenses": monthly["expenses"],
            "recent_transactions": self.transactions.get_recent(5),
            "budget_status": self.budgets.get_budget_status(),
        }

    def monthly_report(self, month: int | None = None, year: int | None = None) -> dict[str, Any]:
        today = date.today()
        month, year = month or today.month, year or today.year
        monthly = self.calculator.monthly_totals(month, year)
        return {
            "period": f"{month:02d}/{year}",
            "income": monthly["income"],
            "expenses": monthly["expenses"],
            "savings": monthly["savings"],
            "category_spending": self.processor.category_spending(month, year),
            "budget_status": self.budgets.get_budget_status(month, year),
            "transactions": self.transactions.filter_by_date(
                f"{year:04d}-{month:02d}-01",
                f"{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}",
            ),
        }

    def format_text_report(self, report: dict[str, Any]) -> str:
        lines = ["Smart Expense Tracker Report", "=" * 28]
        for key, value in report.items():
            if key in {"category_spending", "transactions", "budget_status", "period"}:
                continue
            if isinstance(value, float) or hasattr(value, "quantize"):
                lines.append(f"{key.replace('_', ' ').title()}: {CURRENCY_SYMBOL}{value:,.2f}")
            else:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
        if "period" in report:
            lines.insert(2, f"Period: {report['period']}")
        return "\n".join(lines)

    def save_text_report(self, text: str, filename: str | None = None) -> str:
        from config import REPORTS_DIR

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / (filename or f"report_{date.today():%Y%m%d}.txt")
        path.write_text(text, encoding="utf-8")
        return str(path)
