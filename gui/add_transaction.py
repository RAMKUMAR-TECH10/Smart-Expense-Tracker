"""Add/edit transaction form and dialog."""

from __future__ import annotations

from datetime import date
from typing import Any, Callable

import customtkinter as ctk

from config import EXPENSE, INCOME, TRANSACTION_TYPES
from gui import AppServices
from gui.components import SectionTitle, show_error, show_info
from modules.error_handler import ExpenseTrackerError


class TransactionForm(ctk.CTkFrame):
    def __init__(
        self,
        master: Any,
        services: AppServices,
        on_saved: Callable[[], None],
        transaction_id: int | None = None,
    ) -> None:
        super().__init__(master, corner_radius=14)
        self.services = services
        self.on_saved = on_saved
        self.transaction_id = transaction_id
        self.category_ids: dict[str, int] = {}

        self.grid_columnconfigure((0, 1), weight=1)
        SectionTitle(
            self, "Edit Transaction" if transaction_id else "Add Transaction"
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 12))

        self.title_var = ctk.StringVar()
        self.amount_var = ctk.StringVar()
        self.type_var = ctk.StringVar(value=EXPENSE)
        self.date_var = ctk.StringVar(value=date.today().isoformat())
        self.category_var = ctk.StringVar()

        labels = [
            ("Title", 1, 0),
            ("Amount", 1, 1),
            ("Type", 2, 0),
            ("Category", 2, 1),
            ("Date (YYYY-MM-DD)", 3, 0),
            ("Description", 3, 1),
        ]
        for text, row, column in labels:
            ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(
                row=row, column=column, sticky="w", padx=20, pady=(6, 2)
            )

        self.title_entry = ctk.CTkEntry(self, textvariable=self.title_var, placeholder_text="e.g. Grocery shopping")
        self.title_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))

        self.amount_entry = ctk.CTkEntry(self, textvariable=self.amount_var, placeholder_text="0.00")
        self.amount_entry.grid(row=1, column=1, sticky="ew", padx=20, pady=(0, 8))

        self.type_combo = ctk.CTkComboBox(
            self,
            values=list(TRANSACTION_TYPES),
            variable=self.type_var,
            command=lambda _value: self._reload_categories(),
        )
        self.type_combo.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))

        self.category_combo = ctk.CTkComboBox(self, variable=self.category_var, values=[])
        self.category_combo.grid(row=2, column=1, sticky="ew", padx=20, pady=(0, 8))

        self.date_entry = ctk.CTkEntry(self, textvariable=self.date_var)
        self.date_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 8))

        self.description_box = ctk.CTkTextbox(self, height=70)
        self.description_box.grid(
            row=4, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 12)
        )

        self.save_button = ctk.CTkButton(
            self,
            text="Save Transaction" if transaction_id else "Add Transaction",
            command=self.save,
            height=38,
        )
        self.save_button.grid(row=5, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))

        self._reload_categories()
        if transaction_id:
            self._load_transaction(transaction_id)

    def _reload_categories(self, preferred_id: int | None = None) -> None:
        categories = self.services.categories.get_all(self.type_var.get())
        self.category_ids = {row["category_name"]: row["category_id"] for row in categories}
        names = list(self.category_ids)
        self.category_combo.configure(values=names)
        if preferred_id:
            for name, category_id in self.category_ids.items():
                if category_id == preferred_id:
                    self.category_var.set(name)
                    return
        if names and self.category_var.get() not in names:
            self.category_var.set(names[0])
        elif not names:
            self.category_var.set("")

    def _load_transaction(self, transaction_id: int) -> None:
        record = self.services.transactions.get(transaction_id)
        if not record:
            return
        self.title_var.set(record["title"])
        self.amount_var.set(str(record["amount"]))
        self.type_var.set(record["transaction_type"])
        self.date_var.set(record["transaction_date"])
        self.description_box.delete("1.0", "end")
        self.description_box.insert("1.0", record["description"] or "")
        self._reload_categories(record["category_id"])

    def _payload(self) -> dict[str, Any]:
        return {
            "title": self.title_var.get(),
            "amount": self.amount_var.get(),
            "transaction_type": self.type_var.get(),
            "category_id": self.category_ids.get(self.category_var.get()),
            "transaction_date": self.date_var.get(),
            "description": self.description_box.get("1.0", "end").strip(),
        }

    def save(self) -> None:
        try:
            payload = self._payload()
            if self.transaction_id:
                self.services.transactions.update(self.transaction_id, payload)
                message = "Transaction updated successfully."
            else:
                self.services.transactions.add(payload)
                message = "Transaction added successfully."
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Invalid Transaction")
            return
        show_info(message)
        self.on_saved()
        if not self.transaction_id:
            self.title_var.set("")
            self.amount_var.set("")
            self.description_box.delete("1.0", "end")
            self.title_entry.focus_set()


class AddTransactionView(ctk.CTkFrame):
    def __init__(self, master: Any, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.form = TransactionForm(self, services, on_saved=lambda: None)


class TransactionDialog(ctk.CTkToplevel):
    def __init__(self, master: Any, services: AppServices, transaction_id: int) -> None:
        super().__init__(master)
        self.title("Edit Transaction")
        self.geometry("520x430")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.form = TransactionForm(
            self, services, on_saved=self.destroy, transaction_id=transaction_id
        )
        self.form.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
