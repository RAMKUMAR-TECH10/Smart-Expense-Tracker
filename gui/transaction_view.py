"""Transaction history with search, date filters, edit, delete and export."""

from __future__ import annotations

from datetime import date
from typing import Any

import customtkinter as ctk

from config import TRANSACTION_TYPES
from gui import AppServices
from gui.add_transaction import TransactionDialog
from gui.components import DataTable, SectionTitle, ask_confirmation, format_money, show_error, show_info
from modules.error_handler import ExpenseTrackerError


class TransactionView(ctk.CTkFrame):
    def __init__(self, master: Any, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.services = services
        self._rows: list[dict[str, Any]] = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        SectionTitle(self, "Transactions").grid(row=0, column=0, sticky="w", pady=(8, 10))

        controls = ctk.CTkFrame(self, corner_radius=12)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        controls.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.search_var = ctk.StringVar()
        self.type_var = ctk.StringVar(value="All")
        self.from_var = ctk.StringVar()
        self.to_var = ctk.StringVar()

        ctk.CTkEntry(
            controls, textvariable=self.search_var, placeholder_text="Search name or category..."
        ).grid(row=0, column=0, sticky="ew", padx=(10, 6), pady=10)
        ctk.CTkComboBox(
            controls, values=["All", *TRANSACTION_TYPES], variable=self.type_var
        ).grid(row=0, column=1, sticky="ew", padx=6, pady=10)
        ctk.CTkEntry(controls, textvariable=self.from_var, placeholder_text="From YYYY-MM-DD").grid(
            row=0, column=2, sticky="ew", padx=6, pady=10
        )
        ctk.CTkEntry(controls, textvariable=self.to_var, placeholder_text="To YYYY-MM-DD").grid(
            row=0, column=3, sticky="ew", padx=6, pady=10
        )
        ctk.CTkButton(controls, text="Apply", command=self.refresh, width=80).grid(
            row=0, column=4, sticky="ew", padx=6, pady=10
        )
        ctk.CTkButton(controls, text="Export CSV", command=self.export_csv, width=100).grid(
            row=0, column=5, sticky="ew", padx=(6, 10), pady=10
        )
        ctk.CTkButton(controls, text="Clear Filters", command=self.clear_filters, width=110).grid(
            row=1, column=4, sticky="ew", padx=6, pady=(0, 10)
        )
        ctk.CTkLabel(controls, text="Click a name to edit; click the action cell to delete.", text_color="gray").grid(
            row=1, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 10)
        )

        self.table = DataTable(
            self,
            columns=[
                ("title", "Name", 140),
                ("category_name", "Category", 120),
                ("transaction_date", "Date", 100),
                ("transaction_type", "Type", 80),
                ("amount", "Amount", 100),
                ("action", "Action", 70),
            ],
            row_command=self.edit_transaction,
            action_command=self.delete_transaction,
        )
        self.table.grid(row=2, column=0, sticky="nsew")

    def refresh(self) -> None:
        term = self.search_var.get().strip()
        kind = self.type_var.get()
        start, end = self.from_var.get().strip(), self.to_var.get().strip()
        try:
            if start and end:
                rows = self.services.transactions.filter_by_date(start, end)
                if term or kind != "All":
                    text = term.lower()
                    rows = [
                        row
                        for row in rows
                        if (not text or text in row["title"].lower() or text in row["category_name"].lower())
                        and (kind == "All" or row["transaction_type"] == kind)
                    ]
            else:
                selected_type = None if kind == "All" else kind
                rows = self.services.transactions.search(term, selected_type)
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Filter Error")
            return
        self._rows = rows
        display = [
            {
                **row,
                "amount": format_money(row["amount"]),
                "action": "Delete",
            }
            for row in rows
        ]
        self.table.populate(display, "No transactions match the current filters.")

    def clear_filters(self) -> None:
        self.search_var.set("")
        self.type_var.set("All")
        self.from_var.set("")
        self.to_var.set("")
        self.refresh()

    def edit_transaction(self, transaction_id: int) -> None:
        if transaction_id:
            TransactionDialog(self.winfo_toplevel(), self.services, transaction_id)

    def delete_transaction(self, transaction_id: int) -> None:
        if not transaction_id:
            return
        record = self.services.transactions.get(transaction_id)
        if not record:
            return
        if not ask_confirmation(f"Delete '{record['title']}'? This cannot be undone."):
            return
        try:
            self.services.transactions.delete(transaction_id)
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Delete Failed")
            return
        show_info("Transaction deleted.")
        self.refresh()
        self.winfo_toplevel().refresh_all()

    def export_csv(self) -> None:
        try:
            path = self.services.exporter.export_transactions(self._rows)
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Export Failed")
            return
        show_info(f"CSV exported to:\n{path}")
