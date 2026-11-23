"""Logging setup and application-specific exceptions."""

from __future__ import annotations

import logging
import traceback
from functools import wraps
from typing import Any, Callable

from config import LOG_FILE

LOGS_DIR = LOG_FILE.parent
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("smart_expense_tracker")
_logger.setLevel(logging.INFO)
_logger.propagate = False

if not _logger.handlers:
    _formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    _file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _file_handler.setFormatter(_formatter)
    _logger.addHandler(_file_handler)
    _stream_handler = logging.StreamHandler()
    _stream_handler.setFormatter(_formatter)
    _logger.addHandler(_stream_handler)


class ExpenseTrackerError(Exception):
    """Base exception for the application."""


class ValidationError(ExpenseTrackerError):
    """Raised when user input is invalid."""


class DatabaseError(ExpenseTrackerError):
    """Raised when a database operation fails."""


class ExportError(ExpenseTrackerError):
    """Raised when exporting data fails."""


def get_logger(name: str | None = None) -> logging.Logger:
    if not name:
        return _logger
    child = logging.getLogger(f"smart_expense_tracker.{name}")
    child.setLevel(logging.INFO)
    child.propagate = True
    return child


logger = get_logger()
info = logger.info
warning = logger.warning
error = logger.error


def log_error(message: str, exc: BaseException | None = None) -> None:
    if exc is None:
        logger.error(message)
    else:
        logger.error("%s: %s\n%s", message, exc, traceback.format_exc())


def safe_operation(default: Any = None) -> Callable:
    """Decorator that logs unexpected errors instead of crashing the caller."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except ExpenseTrackerError:
                raise
            except Exception as exc:  # noqa: BLE001 - intentional safety net
                log_error(f"Unexpected error in {func.__qualname__}", exc)
                return default

        return wrapper

    return decorator
