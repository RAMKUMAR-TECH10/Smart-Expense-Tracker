"""SQLite persistence layer for the expense tracker."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from config import DEFAULT_CATEGORIES, DATABASE_PATH
from modules.error_handler import DatabaseError, get_logger, log_error

logger = get_logger("database")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    category_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL UNIQUE,
    category_type TEXT NOT NULL CHECK (category_type IN ('Income', 'Expense'))
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    amount           REAL NOT NULL CHECK (amount > 0),
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('Income', 'Expense')),
    category_id      INTEGER NOT NULL,
    transaction_date TEXT NOT NULL,
    description      TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS budgets (
    budget_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id   INTEGER NOT NULL,
    budget_amount REAL NOT NULL CHECK (budget_amount > 0),
    month         INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year          INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
    UNIQUE (category_id, month, year)
);

CREATE TABLE IF NOT EXISTS settings (
    setting_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name  TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(year, month);
"""


class Database:
    """Thin, safe wrapper around a SQLite connection."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(DATABASE_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: sqlite3.Connection | None = None
        self.initialize()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def initialize(self) -> None:
        try:
            self.connection.executescript(SCHEMA)
            self.connection.commit()
            self._seed_defaults()
            logger.info("Database initialized at %s", self.db_path)
        except sqlite3.Error as exc:
            log_error("Failed to initialize database", exc)
            raise DatabaseError(f"Database initialization failed: {exc}") from exc

    def _seed_defaults(self) -> None:
        for name, category_type in DEFAULT_CATEGORIES:
            self.connection.execute(
                "INSERT OR IGNORE INTO categories (category_name, category_type) VALUES (?, ?)",
                (name, category_type),
            )
        self.connection.execute(
            "INSERT OR IGNORE INTO settings (setting_name, setting_value) VALUES (?, ?)",
            ("currency", "INR"),
        )
        self.connection.execute(
            "INSERT OR IGNORE INTO settings (setting_name, setting_value) VALUES (?, ?)",
            ("date_format", "%Y-%m-%d"),
        )
        self.connection.commit()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        try:
            with self.transaction() as conn:
                return conn.execute(sql, tuple(params))
        except sqlite3.Error as exc:
            log_error(f"Database execute failed: {sql}", exc)
            raise DatabaseError(f"Database operation failed: {exc}") from exc

    def executemany(self, sql: str, seq: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        try:
            with self.transaction() as conn:
                return conn.executemany(sql, [tuple(row) for row in seq])
        except sqlite3.Error as exc:
            log_error(f"Database executemany failed: {sql}", exc)
            raise DatabaseError(f"Database operation failed: {exc}") from exc

    def fetchone(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        try:
            cursor = self.connection.execute(sql, tuple(params))
            row = cursor.fetchone()
            return dict(row) if row is not None else None
        except sqlite3.Error as exc:
            log_error(f"Database fetch failed: {sql}", exc)
            raise DatabaseError(f"Database query failed: {exc}") from exc

    def fetchall(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        try:
            cursor = self.connection.execute(sql, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            log_error(f"Database fetch failed: {sql}", exc)
            raise DatabaseError(f"Database query failed: {exc}") from exc

    def get_setting(self, name: str, default: str = "") -> str:
        row = self.fetchone("SELECT setting_value FROM settings WHERE setting_name = ?", (name,))
        return row["setting_value"] if row else default

    def set_setting(self, name: str, value: str) -> None:
        self.execute(
            """INSERT INTO settings (setting_name, setting_value) VALUES (?, ?)
               ON CONFLICT(setting_name) DO UPDATE SET setting_value = excluded.setting_value""",
            (name, str(value)),
        )

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
