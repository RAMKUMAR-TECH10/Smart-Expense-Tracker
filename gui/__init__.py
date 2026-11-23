"""Smart Expense Tracker user interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AppServices:
    """Shared service instances passed to every view."""

    database: Any
    transactions: Any
    income: Any
    expense: Any
    categories: Any
    budgets: Any
    calculator: Any
    processor: Any
    reports: Any
    exporter: Any
