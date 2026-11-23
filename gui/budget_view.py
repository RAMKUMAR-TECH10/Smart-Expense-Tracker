"""Monthly budget management view."""

from __future__ import annotations

from datetime import date
from typing import Any

import customtkinter as ctk

from gui import AppServices
from gui.components import (
    DataTable,
    ProgressRow,
    SectionTitle,
    ask_confirmation,
    format_money,
    show_error,
    show_info,
)
from modules.error_handler import ExpenseTrackerError


class BudgetView(ctk.CTkFrame):
    def __init__(self, master: Any, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.services = services
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        SectionTitle(self, "Monthly Budgets").grid(row=0, column=0, sticky="w", pady=(8, 10))

        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for column in range(5):
            form.grid_columnconfigure(column, weight=1)

        self.category_var = ctk.StringVar()
        self.amount_var = ctk.StringVar()
        self.month_var = ctk.StringVar(value=str(date.today().month))
        self.year_var = ctk.StringVar(value=str(date.today().year))
        self.category_ids: dict[str, int] = {}

        ctk.CTkLabel(form, text="Category", anchor="w").grid(row=0, column=0, sticky="w", padx=(12, 4), pady=(8, 2))
        ctk.CTkLabel(form, text="Limit", anchor="w").grid(row=0, column=1, sticky="w", padx=4, pady=(8, 2))
        ctk.CTkLabel(form, text="Month", anchor="w").grid(row=0, column=2, sticky="w", padx=4, pady=(8, 2))
        ctk.CTkLabel(form, text="Year", anchor="w").grid(row=0, column=3, sticky="w", padx=4, pady=(8, 2))

        self.category_combo = ctk.CTkComboBox(form, variable=self.category_var, values=[])
        self.category_combo.grid(row=1, column=0, sticky="ew", padx=(12, 4), pady=(0, 12))
        ctk.CTkEntry(form, textvariable=self.amount_var, placeholder_text="0.00").grid(
            row=1, column=1, sticky="ew", padx=4, pady=(0, 12)
        )
        ctk.CTkEntry(form, textvariable=self.month_var).grid(
            row=1, column=2, sticky="ew", padx=4, pady=(0, 12)
        )
        ctk.CTkEntry(form, textvariable=self.year_var).grid(
            row=1, column=3, sticky="ew", padx=4, pady=(0, 12)
        )
        ctk.CTkButton(form, text="Save Budget", command=self.save_budget).grid(
            row=1, column=4, sticky="ew", padx=(4, 12), pady=(0, 12)
        )

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        ctk.CTkLabel(filters, text="Viewing", anchor="w").pack(side="left", padx=(2, 6))
        self.view_month = ctk.StringVar(value=str(date.today().month))
        self.view_year = ctk.StringVar(value=str(date.today().year))
        ctk.CTkEntry(filters, textvariable=self.view_month, width=60).pack(side="left", padx=4)
        ctk.CTkEntry(filters, textvariable=self.view_year, width=80).pack(side="left", padx=4)
        ctk.CTkButton(filters, text="Refresh", command=self.refresh, width=90).pack(side="left", padx=8)
        self.warning_label = ctk.CTkLabel(filters, text="", text_color="#E8A33D")
        self.warning_label.pack(side="right")

        lower = ctk.CTkFrame(self, fg_color="transparent")
        lower.grid(row=3, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=1)
        lower.grid_columnconfigure(1, weight=1)
        lower.grid_rowconfigure(0, weight=1)

        progress_frame = ctk.CTkFrame(lower, corner_radius=12)
        progress_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        SectionTitle(progress_frame, "Spending Progress").grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 8)
        )
        self.progress_container = ctk.CTkScrollableFrame(progress_frame, fg_color="transparent")
        self.progress_container.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.progress_container.grid_columnconfigure(0, weight=1)
        progress_frame.grid_rowconfigure(1, weight=1)

        table_frame = ctk.CTkFrame(lower, corner_radius=12)
        table_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        SectionTitle(table_frame, "Configured Budgets").grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 8)
        )
        self.table = DataTable(
            table_frame,
            columns=[
                ("category_name", "Category", 120),
                ("budget_amount", "Limit", 90),
                ("action", "Action", 70),
            ],
            action_command=self.delete_budget,
            id_key="budget_id",
        )
        self.table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))

    def _period(self) -> tuple[int, int]:
        try:
            return int(self.view_month.get()), int(self.view_year.get())
        except ValueError:
            return date.today().month, date.today().year

    def refresh(self) -> None:
        categories = self.services.categories.get_all("Expense")
        self.category_ids = {row["category_name"]: row["category_id"] for row in categories}
        self.category_combo.configure(values=list(self.category_ids))
        if self.category_ids and self.category_var.get() not in self.category_ids:
            self.category_var.set(next(iter(self.category_ids)))

        month, year = self._period()
        status = self.services.budgets.get_budget_status(month, year)
        for child in self.progress_container.winfo_children():
            child.destroy()
        if not status:
            ctk.CTkLabel(
                self.progress_container, text="No budgets for this period.", text_color="gray"
            ).grid(row=0, column=0, pady=20)
        for index, item in enumerate(status):
            row = ProgressRow(self.progress_container, item["category_name"])
            row.grid(row=index, column=0, sticky="ew", pady=6)
            row.update_values(
                format_money(item["spent"]),
                format_money(item["budget_amount"]),
                item["percentage"],
                item["exceeded"],
            )

        self.table.populate(
            [
                {
                    "category_name": item["category_name"],
                    "budget_amount": format_money(item["budget_amount"]),
                    "budget_id": item["budget_id"],
                    "action": "Delete",
                }
                for item in status
            ],
            "No budgets configured.",
        )
        warnings = self.services.budgets.check_budget_warnings(month, year)
        self.warning_label.configure(text=" | ".join(warnings))

    def save_budget(self) -> None:
        try:
            self.services.budgets.set_budget(
                {
                    "category_id": self.category_ids.get(self.category_var.get()),
                    "budget_amount": self.amount_var.get(),
                    "month": self.view_month.get(),
                    "year": self.view_year.get(),
                }
            )
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Invalid Budget")
            return
        self.amount_var.set("")
        show_info("Budget saved.")
        self.refresh()
        self.winfo_toplevel().refresh_all()

    def delete_budget(self, budget_id: int) -> None:
        if not budget_id or not ask_confirmation("Delete this budget?"):
            return
        self.services.budgets.delete_budget(budget_id)
        self.refresh()
        self.winfo_toplevel().refresh_all()
