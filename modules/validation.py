"""Input validation helpers for financial records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from config import (
    DATE_FORMAT,
    EXPENSE,
    INCOME,
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
    TRANSACTION_TYPES,
)
from modules.error_handler import ValidationError

MIN_AMOUNT = Decimal("0.01")


def validate_title(value: object) -> tuple[bool, str]:
    title = str(value or "").strip()
    if not title:
        return False, "Title cannot be empty."
    if len(title) > MAX_TITLE_LENGTH:
        return False, f"Title must be {MAX_TITLE_LENGTH} characters or fewer."
    return True, title


def validate_amount(value: object, *, positive: bool = True) -> tuple[bool, str | Decimal]:
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError, ValueError):
        return False, "Amount must be a valid number."
    if not amount.is_finite():
        return False, "Amount must be a finite number."
    if positive and amount <= 0:
        return False, "Amount must be greater than zero."
    if amount.as_tuple().exponent < -2:
        amount = amount.quantize(Decimal("0.01"))
        if positive and amount <= 0:
            return False, "Amount must be at least 0.01."
    return True, amount


def validate_transaction_type(value: object) -> tuple[bool, str]:
    transaction_type = str(value or "").strip().title()
    if transaction_type not in TRANSACTION_TYPES:
        return False, "Transaction type must be Income or Expense."
    return True, transaction_type


def validate_date(value: object) -> tuple[bool, str]:
    if isinstance(value, datetime):
        return True, value.date().strftime(DATE_FORMAT)
    if isinstance(value, date):
        return True, value.strftime(DATE_FORMAT)
    text = str(value or "").strip()
    for fmt in (DATE_FORMAT, "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return True, datetime.strptime(text, fmt).strftime(DATE_FORMAT)
        except ValueError:
            continue
    return False, "Date must be valid (YYYY-MM-DD)."


def validate_category_id(value: object) -> tuple[bool, str | int]:
    try:
        category_id = int(str(value).strip())
    except (TypeError, ValueError):
        return False, "Please select a category."
    if category_id <= 0:
        return False, "Please select a category."
    return True, category_id


def validate_description(value: object) -> tuple[bool, str]:
    text = "" if value is None else str(value).strip()
    if len(text) > MAX_DESCRIPTION_LENGTH:
        return False, f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
    return True, text


def validate_budget_amount(value: object) -> tuple[bool, str | Decimal]:
    return validate_amount(value, positive=True)


def validate_month(value: object) -> tuple[bool, str | int]:
    try:
        month = int(str(value).strip())
    except (TypeError, ValueError):
        return False, "Month must be between 1 and 12."
    if not 1 <= month <= 12:
        return False, "Month must be between 1 and 12."
    return True, month


def validate_year(value: object) -> tuple[bool, str | int]:
    try:
        year = int(str(value).strip())
    except (TypeError, ValueError):
        return False, "Year must be a valid four-digit year."
    if not 1900 <= year <= 9999:
        return False, "Year must be a valid four-digit year."
    return True, year


def _check(results: list[tuple[bool, object]], label: str) -> object:
    for ok, value in results:
        if not ok:
            raise ValidationError(f"{label}: {value}")
    return [value for _, value in results]


def validate_transaction(data: dict) -> dict:
    """Validate a complete transaction record, raising ValidationError on failure."""

    title_ok, title = validate_title(data.get("title"))
    amount_ok, amount = validate_amount(data.get("amount"))
    type_ok, transaction_type = validate_transaction_type(data.get("transaction_type"))
    category_ok, category_id = validate_category_id(data.get("category_id"))
    date_ok, transaction_date = validate_date(data.get("transaction_date"))
    desc_ok, description = validate_description(data.get("description"))

    _check([(title_ok, title)], "Invalid title")
    _check([(amount_ok, amount)], "Invalid amount")
    _check([(type_ok, transaction_type)], "Invalid transaction type")
    _check([(category_ok, category_id)], "Invalid category")
    _check([(date_ok, transaction_date)], "Invalid date")
    _check([(desc_ok, description)], "Invalid description")

    return {
        "title": title,
        "amount": amount,
        "transaction_type": transaction_type,
        "category_id": category_id,
        "transaction_date": transaction_date,
        "description": description,
    }


def validate_budget(data: dict) -> dict:
    amount_ok, amount = validate_budget_amount(data.get("budget_amount"))
    category_ok, category_id = validate_category_id(data.get("category_id"))
    month_ok, month = validate_month(data.get("month"))
    year_ok, year = validate_year(data.get("year"))
    _check([(amount_ok, amount)], "Invalid budget amount")
    _check([(category_ok, category_id)], "Invalid category")
    _check([(month_ok, month)], "Invalid month")
    _check([(year_ok, year)], "Invalid year")
    return {
        "budget_amount": amount,
        "category_id": category_id,
        "month": month,
        "year": year,
    }


def category_type_matches(transaction_type: str, category_type: str) -> bool:
    return str(transaction_type).strip().title() == str(category_type).strip().title() or str(
        category_type
    ).strip().title() == "Both"


__all__ = [
    "EXPENSE",
    "INCOME",
    "ValidationError",
    "validate_amount",
    "validate_budget",
    "validate_budget_amount",
    "validate_category_id",
    "validate_date",
    "validate_description",
    "validate_month",
    "validate_title",
    "validate_transaction",
    "validate_transaction_type",
    "validate_year",
]
