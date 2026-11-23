"""Entry point for Smart Expense Tracker."""

from __future__ import annotations

from modules.balance_calculator import BalanceCalculator
from modules.budget_manager import BudgetManager
from modules.category_manager import CategoryManager
from modules.data_processor import DataProcessor
from modules.database import Database
from modules.error_handler import get_logger, log_error
from modules.export_manager import ExportManager
from modules.expense_manager import ExpenseManager
from modules.income_manager import IncomeManager
from modules.report_generator import ReportGenerator
from modules.transaction_manager import TransactionManager
from gui import AppServices
from gui.main_window import MainWindow

logger = get_logger("main")


def build_services(db_path=None) -> AppServices:
    database = Database(db_path)
    transactions = TransactionManager(database)
    calculator = BalanceCalculator(database)
    return AppServices(
        database=database,
        transactions=transactions,
        income=IncomeManager(transactions),
        expense=ExpenseManager(transactions),
        categories=CategoryManager(database),
        budgets=BudgetManager(database),
        calculator=calculator,
        processor=DataProcessor(database, calculator),
        reports=ReportGenerator(database),
        exporter=ExportManager(),
    )


def main() -> None:
    services = None
    try:
        services = build_services()
        logger.info("Starting application")
        app = MainWindow(services)
        app.mainloop()
    except Exception as exc:  # noqa: BLE001
        log_error("Application failed to start", exc)
        try:
            from tkinter import messagebox

            messagebox.showerror("Startup Error", f"The application could not start:\n{exc}")
        except Exception:  # noqa: BLE001
            print(f"Startup error: {exc}")
    finally:
        if services is not None:
            services.database.close()


if __name__ == "__main__":
    main()
