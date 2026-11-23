"""Category management."""

from __future__ import annotations

from config import TRANSACTION_TYPES
from modules.database import Database
from modules.error_handler import ValidationError, get_logger

logger = get_logger("categories")


class CategoryManager:
    def __init__(self, database: Database) -> None:
        self.db = database

    def get_all(self, category_type: str | None = None) -> list[dict]:
        if category_type in TRANSACTION_TYPES:
            return self.db.fetchall(
                "SELECT * FROM categories WHERE category_type = ? ORDER BY category_name",
                (category_type,),
            )
        return self.db.fetchall("SELECT * FROM categories ORDER BY category_type, category_name")

    def get(self, category_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM categories WHERE category_id = ?", (category_id,))

    def add(self, name: str, category_type: str) -> int:
        clean_name = str(name or "").strip()
        clean_type = str(category_type or "").strip().title()
        if not clean_name:
            raise ValidationError("Category name cannot be empty.")
        if clean_type not in TRANSACTION_TYPES:
            raise ValidationError("Category type must be Income or Expense.")
        if self.db.fetchone("SELECT 1 FROM categories WHERE category_name = ?", (clean_name,)):
            raise ValidationError(f"Category '{clean_name}' already exists.")
        cursor = self.db.execute(
            "INSERT INTO categories (category_name, category_type) VALUES (?, ?)",
            (clean_name, clean_type),
        )
        logger.info("Added category '%s' (%s)", clean_name, clean_type)
        return int(cursor.lastrowid or 0)

    def update(self, category_id: int, name: str, category_type: str) -> bool:
        clean_name = str(name or "").strip()
        clean_type = str(category_type or "").strip().title()
        if not clean_name:
            raise ValidationError("Category name cannot be empty.")
        if clean_type not in TRANSACTION_TYPES:
            raise ValidationError("Category type must be Income or Expense.")
        duplicate = self.db.fetchone(
            "SELECT 1 FROM categories WHERE category_name = ? AND category_id != ?",
            (clean_name, category_id),
        )
        if duplicate:
            raise ValidationError(f"Category '{clean_name}' already exists.")
        cursor = self.db.execute(
            "UPDATE categories SET category_name = ?, category_type = ? WHERE category_id = ?",
            (clean_name, clean_type, category_id),
        )
        return cursor.rowcount > 0

    def delete(self, category_id: int) -> bool:
        if self.db.fetchone(
            "SELECT 1 FROM transactions WHERE category_id = ? LIMIT 1", (category_id,)
        ):
            raise ValidationError("Cannot delete a category used by transactions.")
        if self.db.fetchone("SELECT 1 FROM budgets WHERE category_id = ? LIMIT 1", (category_id,)):
            raise ValidationError("Cannot delete a category that has a budget.")
        cursor = self.db.execute("DELETE FROM categories WHERE category_id = ?", (category_id,))
        return cursor.rowcount > 0

    def names(self, category_type: str | None = None) -> list[str]:
        return [row["category_name"] for row in self.get_all(category_type)]
