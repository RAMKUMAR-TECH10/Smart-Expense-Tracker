"""Application settings and shared constants."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = Path(os.environ.get("EXPENSE_TRACKER_DB", DATABASE_DIR / "expense_tracker.db"))
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

APP_NAME = "Smart Expense Tracker"
VERSION = "1.0.0"
CURRENCY_SYMBOL = "₹"

INCOME = "Income"
EXPENSE = "Expense"
TRANSACTION_TYPES = (INCOME, EXPENSE)

DEFAULT_CATEGORIES: tuple[tuple[str, str], ...] = (
    ("Food", EXPENSE),
    ("Transportation", EXPENSE),
    ("Shopping", EXPENSE),
    ("Education", EXPENSE),
    ("Entertainment", EXPENSE),
    ("Healthcare", EXPENSE),
    ("Housing", EXPENSE),
    ("Salary", INCOME),
    ("Freelancing", INCOME),
    ("Investments", INCOME),
    ("Other", EXPENSE),
)

DATE_FORMAT = "%Y-%m-%d"
MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500

COLOR_THEME = {
    "balance": "#2E8B57",
    "income": "#1E9E63",
    "expense": "#D9534F",
    "saving": "#3B82C4",
    "accent": "#4A90E2",
    "warning": "#E8A33D",
}
