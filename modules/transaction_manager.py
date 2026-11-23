"""Core transaction and category management."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from config import EXPENSE, INCOME
from modules.database import Database
from modules.error_handler import ValidationError, get_logger
from modules.validation import (
    category_type_matches,
    validate_date,
    validate_transaction,
)

logger = get_logger("transactions")

TRANSACTION_COLUMNS = """
    t.transaction_id, t.title, t.amount, t.transaction_type, t.category_id,
    t.transaction_date, t.description, c.category_name, c.category_type
"""
TRANSACTION_JOIN = "FROM transactions t JOIN categories c ON t.category_id = c.category_id"


def decimal_amount(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


class TransactionManager:
    def __init__(self, database: Database) -> None:
        self.db = database

    def add(self, data: dict) -> int:
        record = validate_transaction(data)
        self._ensure_category_match(record["category_id"], record["transaction_type"])
        cursor = self.db.execute(
            """INSERT INTO transactions
               (title, amount, transaction_type, category_id, transaction_date, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                record["title"],
                float(record["amount"]),
                record["transaction_type"],
                record["category_id"],
                record["transaction_date"],
                record["description"],
            ),
        )
        logger.info("Added %s transaction '%s'", record["transaction_type"], record["title"])
        return int(cursor.lastrowid or 0)

    def update(self, transaction_id: int, data: dict) -> bool:
        record = validate_transaction(data)
        self._ensure_category_match(record["category_id"], record["transaction_type"])
        cursor = self.db.execute(
            """UPDATE transactions SET title = ?, amount = ?, transaction_type = ?,
               category_id = ?, transaction_date = ?, description = ?
               WHERE transaction_id = ?""",
            (
                record["title"],
                float(record["amount"]),
                record["transaction_type"],
                record["category_id"],
                record["transaction_date"],
                record["description"],
                transaction_id,
            ),
        )
        if cursor.rowcount == 0:
            logger.warning("No transaction found with id %s", transaction_id)
            return False
        logger.info("Updated transaction %s", transaction_id)
        return True

    def delete(self, transaction_id: int) -> bool:
        cursor = self.db.execute(
            "DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,)
        )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info("Deleted transaction %s", transaction_id)
        return deleted

    def get(self, transaction_id: int) -> dict[str, Any] | None:
        return self.db.fetchone(
            f"SELECT {TRANSACTION_COLUMNS} {TRANSACTION_JOIN} WHERE t.transaction_id = ?",
            (transaction_id,),
        )

    def get_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        sql = (
            f"SELECT {TRANSACTION_COLUMNS} {TRANSACTION_JOIN} "
            "ORDER BY t.transaction_date DESC, t.transaction_id DESC"
        )
        params: tuple[Any, ...] = ()
        if limit:
            sql += " LIMIT ?"
            params = (limit,)
        return self.db.fetchall(sql, params)

    def search(self, term: str, transaction_type: str | None = None) -> list[dict[str, Any]]:
        sql = f"SELECT {TRANSACTION_COLUMNS} {TRANSACTION_JOIN} WHERE 1=1"
        params: list[Any] = []
        if term and term.strip():
            sql += " AND (LOWER(t.title) LIKE ? OR LOWER(c.category_name) LIKE ?)"
            pattern = f"%{term.strip().lower()}%"
            params.extend([pattern, pattern])
        if transaction_type in (INCOME, EXPENSE):
            sql += " AND t.transaction_type = ?"
            params.append(transaction_type)
        sql += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"
        return self.db.fetchall(sql, params)

    def filter_by_date(self, start: str, end: str) -> list[dict[str, Any]]:
        start_ok, clean_start = validate_date(start)
        end_ok, clean_end = validate_date(end)
        if not start_ok:
            raise ValidationError(f"Invalid start date: {clean_start}")
        if not end_ok:
            raise ValidationError(f"Invalid end date: {clean_end}")
        if clean_start > clean_end:
            raise ValidationError("Start date must be before end date.")
        return self.db.fetchall(
            f"SELECT {TRANSACTION_COLUMNS} {TRANSACTION_JOIN} "
            "WHERE t.transaction_date BETWEEN ? AND ? "
            "ORDER BY t.transaction_date DESC, t.transaction_id DESC",
            (clean_start, clean_end),
        )

    def get_recent(self, limit: int = 5) -> list[dict[str, Any]]:
        return self.get_all(limit)

    def _ensure_category_match(self, category_id: int, transaction_type: str) -> None:
        row = self.db.fetchone(
            "SELECT category_type FROM categories WHERE category_id = ?", (category_id,)
        )
        if row is None:
            raise ValidationError("Selected category does not exist.")
        if not category_type_matches(transaction_type, row["category_type"]):
            raise ValidationError(
                f"Category type does not match {transaction_type}. Choose a matching category."
            )
