"""Reusable CustomTkinter UI components."""

from __future__ import annotations

from typing import Any, Callable

import customtkinter as ctk
from tkinter import messagebox

from config import CURRENCY_SYMBOL


def format_money(value: object) -> str:
    try:
        return f"{CURRENCY_SYMBOL}{float(value):,.2f}"
    except (TypeError, ValueError):
        return f"{CURRENCY_SYMBOL}0.00"


class Card(ctk.CTkFrame):
    """Small statistic card used on the dashboard."""

    def __init__(
        self,
        master: Any,
        title: str,
        value: str = "",
        accent: str = "#4A90E2",
        **kwargs: Any,
    ) -> None:
        super().__init__(master, corner_radius=14, fg_color=("gray90", "gray18"), **kwargs)
        self.grid_columnconfigure(0, weight=1)
        indicator = ctk.CTkFrame(self, width=4, corner_radius=2, fg_color=accent)
        indicator.grid(row=0, column=0, sticky="nsw", padx=(14, 0), pady=16)
        indicator.grid_propagate(False)
        indicator.configure(height=42)
        self.title_label = ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        )
        self.title_label.grid(row=0, column=1, sticky="ew", padx=(10, 14), pady=(16, 0))
        self.value_label = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=accent, anchor="w"
        )
        self.value_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 14))

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=value)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master: Any, text: str, **kwargs: Any) -> None:
        super().__init__(
            master,
            text=text,
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
            **kwargs,
        )


class DataTable(ctk.CTkScrollableFrame):
    """Lightweight read-only table rendered as a grid of labels."""

    def __init__(
        self,
        master: Any,
        columns: list[tuple[str, str, int]],
        row_command: Callable[[int], None] | None = None,
        action_command: Callable[[int], None] | None = None,
        id_key: str = "transaction_id",
        **kwargs: Any,
    ) -> None:
        super().__init__(master, corner_radius=12, **kwargs)
        self.columns = columns
        self.row_command = row_command
        self.action_command = action_command
        self.id_key = id_key
        for index, (key, heading, width) in enumerate(columns):
            self.grid_columnconfigure(index, weight=1, minsize=width)
            header = ctk.CTkLabel(
                self,
                text=heading,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
            )
            header.grid(row=0, column=index, sticky="ew", padx=8, pady=(6, 10))

    def populate(self, rows: list[dict[str, Any]], empty_message: str = "No records found.") -> None:
        for child in self.winfo_children():
            if int(child.grid_info().get("row", -1)) >= 1:
                child.destroy()
        if not rows:
            label = ctk.CTkLabel(self, text=empty_message, text_color="gray")
            label.grid(row=1, column=0, columnspan=len(self.columns), pady=24)
            return
        for row_index, record in enumerate(rows, start=1):
            values = []
            for column_index, (key, _heading, _width) in enumerate(self.columns):
                value = record.get(key, "")
                label = ctk.CTkLabel(self, text=str(value), anchor="w", wraplength=260)
                label.grid(row=row_index, column=column_index, sticky="ew", padx=8, pady=4)
                command = None
                if column_index == 0:
                    command = self.row_command
                elif column_index == len(self.columns) - 1:
                    command = self.action_command
                if command:
                    label.bind(
                        "<Button-1>",
                        lambda _e, rid=record.get(self.id_key), cb=command: cb(rid),
                    )
                    label.configure(cursor="hand2", text_color=("#1E90FF", "#7FB3FF"))
                values.append(label)
            if row_index % 2 == 0:
                for label in values:
                    label.configure(text_color=("gray30", "gray70"))


class ProgressRow(ctk.CTkFrame):
    """Label + progress bar used for budget overview."""

    def __init__(self, master: Any, name: str, **kwargs: Any) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.name_label = ctk.CTkLabel(self, text=name, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.name_label.grid(row=0, column=0, sticky="w")
        self.detail_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), anchor="e")
        self.detail_label.grid(row=0, column=1, sticky="e")
        self.progress = ctk.CTkProgressBar(self, height=10, corner_radius=5)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 2))
        self.progress.set(0)

    def update_values(self, spent: str, limit: str, percentage: float, exceeded: bool = False) -> None:
        self.detail_label.configure(text=f"{spent} / {limit} ({percentage:.0f}%)")
        self.progress.set(min(percentage / 100, 1.0))
        self.progress.configure(progress_color="#D9534F" if exceeded else "#2E8B57")


def show_error(message: str, title: str = "Error") -> None:
    messagebox.showerror(title, message)


def show_info(message: str, title: str = "Success") -> None:
    messagebox.showinfo(title, message)


def ask_confirmation(message: str, title: str = "Confirm") -> bool:
    return bool(messagebox.askyesno(title, message))
