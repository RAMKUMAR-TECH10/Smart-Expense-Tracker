# Smart Expense Tracker

A modern, offline Python desktop application for managing income, expenses, categories, monthly budgets and financial reports. Built with CustomTkinter, SQLite, pandas and Matplotlib.

## Features

- Add, edit and delete income/expense transactions
- Organize transactions with custom income and expense categories
- Search by title or category and filter by transaction type/date range
- Total balance, total income, total expenses and monthly savings calculations
- Monthly category budgets with spending progress and over-budget warnings
- Dashboard with recent transactions and budget overview
- Interactive charts: monthly income vs expenses, category-wise spending and 6-month trends
- CSV export for filtered or complete transaction history
- Text report generation, database backup and light/dark/system themes
- Local SQLite storage; no account, API key or internet connection required
- Input validation, structured logging and `unittest` test suite

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the app

```bash
python main.py
```

The SQLite database is created automatically at `database/expense_tracker.db` with default categories. To use another database file, set the `EXPENSE_TRACKER_DB` environment variable before launching.

### 3. Run the tests

```bash
python -m unittest discover -s tests -v
```

Tests use temporary SQLite databases and never modify your real financial data.

## Project structure

```
.
├── main.py                 # Application entry point
├── config.py               # Paths, constants and settings
├── modules/
│   ├── database.py         # SQLite schema and connection handling
│   ├── validation.py       # Input validation with Decimal amounts
│   ├── error_handler.py    # Custom exceptions and logging
│   ├── transaction_manager.py
│   ├── income_manager.py
│   ├── expense_manager.py
│   ├── category_manager.py
│   ├── budget_manager.py
│   ├── balance_calculator.py
│   ├── data_processor.py   # pandas analytics
│   ├── report_generator.py
│   └── export_manager.py   # CSV export
├── gui/
│   ├── main_window.py      # Navigation shell and settings
│   ├── dashboard.py
│   ├── transaction_view.py
│   ├── add_transaction.py
│   ├── category_view.py
│   ├── budget_view.py
│   ├── analytics_view.py
│   └── components.py
├── database/               # Local SQLite database
├── reports/                # CSV exports, text reports and backups
├── logs/app.log            # Application and error log
├── tests/                  # Unit tests
└── assets/icons/           # Optional icons
```

## Database schema

| Table | Purpose |
| --- | --- |
| `transactions` | Transaction title, amount, type, category, date and description |
| `categories` | Income/expense categories with foreign keys from transactions and budgets |
| `budgets` | Monthly limit per expense category (unique per category/month/year) |
| `settings` | Key/value application settings |

Money values are validated as `Decimal` before being stored. `SQLite REAL` is used for storage to match the requested schema, and values are converted back to `Decimal` for all calculations.

## How to use

1. Open **Add Transaction** and record an income or expense. Select a category that matches the transaction type.
2. Open **Transactions** to search, filter, edit, delete or export records as CSV.
3. Open **Categories** to add your own categories. Categories in use cannot be deleted.
4. Open **Budgets** to set a monthly limit for an expense category and monitor utilization.
5. Open **Reports** to view charts and save a monthly text report.
6. Open **Settings** to change the theme, back up the database or export all records.

## Validation rules

- Title is required (max 100 characters)
- Amount must be a finite number greater than zero, with at most two decimal places
- Type must be `Income` or `Expense`
- Category is required and must match the transaction type
- Date must be valid; accepted formats include `YYYY-MM-DD`, `DD-MM-YYYY` and `DD/MM/YYYY`
- Description is optional (max 500 characters)
- Budget amount must be positive; month and year must be valid

## Optional future enhancements

Recurring expenses, budget notifications, PDF reports, database restore, password protection and application icons.

## License

MIT License. See `LICENSE`.
