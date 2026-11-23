"""Category management view."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from config import TRANSACTION_TYPES
from gui import AppServices
from gui.components import DataTable, SectionTitle, ask_confirmation, show_error, show_info
from modules.error_handler import ExpenseTrackerError


class CategoryView(ctk.CTkFrame):
    def __init__(self, master: Any, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.services = services
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        SectionTitle(self, "Categories").grid(row=0, column=0, sticky="w", pady=(8, 10))

        form = ctk.CTkFrame(self, corner_radius=12)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        form.grid_columnconfigure((0, 1, 2), weight=1)

        self.name_var = ctk.StringVar()
        self.type_var = ctk.StringVar(value="Expense")
        ctk.CTkEntry(form, textvariable=self.name_var, placeholder_text="Category name").grid(
            row=0, column=0, sticky="ew", padx=(12, 6), pady=12
        )
        ctk.CTkComboBox(form, values=list(TRANSACTION_TYPES), variable=self.type_var).grid(
            row=0, column=1, sticky="ew", padx=6, pady=12
        )
        ctk.CTkButton(form, text="Add Category", command=self.add_category).grid(
            row=0, column=2, sticky="ew", padx=(6, 12), pady=12
        )

        self.table = DataTable(
            self,
            columns=[
                ("category_id", "ID", 60),
                ("category_name", "Name", 180),
                ("category_type", "Type", 100),
                ("action", "Action", 80),
            ],
            action_command=self.delete_category,
            id_key="category_id",
        )
        self.table.grid(row=2, column=0, sticky="nsew")

    def refresh(self) -> None:
        rows = [
            {**row, "action": "Delete"} for row in self.services.categories.get_all()
        ]
        self.table.populate(rows, "No categories found.")

    def add_category(self) -> None:
        try:
            self.services.categories.add(self.name_var.get(), self.type_var.get())
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Invalid Category")
            return
        self.name_var.set("")
        show_info("Category added.")
        self.refresh()

    def delete_category(self, category_id: int) -> None:
        category = self.services.categories.get(category_id)
        if not category:
            return
        if not ask_confirmation(f"Delete category '{category['category_name']}'?"):
            return
        try:
            self.services.categories.delete(category_id)
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Delete Failed")
            return
        show_info("Category deleted.")
        self.refresh()
