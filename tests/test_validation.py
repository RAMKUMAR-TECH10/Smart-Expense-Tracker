"""Tests for input validation."""

import unittest
from decimal import Decimal

from modules.validation import (
    validate_amount,
    validate_date,
    validate_description,
    validate_title,
    validate_transaction_type,
)


class ValidationTests(unittest.TestCase):
    def test_valid_title(self) -> None:
        self.assertEqual(validate_title("  Salary "), (True, "Salary"))

    def test_empty_title_rejected(self) -> None:
        ok, message = validate_title("   ")
        self.assertFalse(ok)
        self.assertIn("empty", message.lower())

    def test_valid_amount(self) -> None:
        ok, value = validate_amount("1250.50")
        self.assertTrue(ok)
        self.assertEqual(value, Decimal("1250.50"))

    def test_negative_and_invalid_amounts_rejected(self) -> None:
        self.assertFalse(validate_amount("-5")[0])
        self.assertFalse(validate_amount("0")[0])
        self.assertFalse(validate_amount("abc")[0])

    def test_transaction_type(self) -> None:
        self.assertEqual(validate_transaction_type("income"), (True, "Income"))
        self.assertFalse(validate_transaction_type("Transfer")[0])

    def test_dates(self) -> None:
        self.assertEqual(validate_date("2026-02-28"), (True, "2026-02-28"))
        self.assertEqual(validate_date("28-02-2026"), (True, "2026-02-28"))
        self.assertFalse(validate_date("31-02-2026")[0])

    def test_description_limit(self) -> None:
        self.assertTrue(validate_description("a" * 500)[0])
        self.assertFalse(validate_description("a" * 501)[0])


if __name__ == "__main__":
    unittest.main()
