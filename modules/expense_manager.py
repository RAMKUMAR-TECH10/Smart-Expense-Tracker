"""Expense-specific convenience API."""

from __future__ import annotations

from typing import Any

from config import EXPENSE
from modules.transaction_manager import TransactionManager


class ExpenseManager:
    def __init__(self, manager: TransactionManager) -> None:
        self.manager = manager

    def add(self, data: dict[str, Any]) -> int:
        return self.manager.add({**data, "transaction_type": EXPENSE})

    def get_all(self) -> list[dict[str, Any]]:
        return self.manager.search("", EXPENSE)
