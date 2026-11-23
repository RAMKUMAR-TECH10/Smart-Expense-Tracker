"""Dashboard overview view."""

from __future__ import annotations

import customtkinter as ctk

from config import COLOR_THEME
from gui.components import Card, DataTable, ProgressRow, SectionTitle, format_money
from gui import AppServices


class DashboardView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkBaseClass, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.services = services
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(8, 12))
        SectionTitle(self, "Dashboard", ).grid(row=0, column=0, sticky="w")
        self.period_label = ctk.CTkLabel(header, text="", text_color="gray")
        self.period_label.pack(side="right")

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.cards: dict[str, Card] = {}
        for index, (key, title, color) in enumerate(
            (
                ("balance", "Total Balance", COLOR_THEME["balance"]),
                ("income", "Total Income", COLOR_THEME["income"]),
                ("expenses", "Total Expenses", COLOR_THEME["expense"]),
                ("savings", "Monthly Savings", COLOR_THEME["saving"]),
            )
        ):
            card = Card(cards, title, accent=color)
            card.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 8, 0))
            self.cards[key] = card

        self.comparison_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=12), anchor="w", text_color="gray"
        )
        self.comparison_label.grid(row=2, column=0, sticky="w", pady=(8, 4))

        lower = ctk.CTkFrame(self, fg_color="transparent")
        lower.grid(row=3, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=3)
        lower.grid_columnconfigure(1, weight=2)
        lower.grid_rowconfigure(0, weight=1)

        recent_frame = ctk.CTkFrame(lower, corner_radius=14)
        recent_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        recent_frame.grid_rowconfigure(1, weight=1)
        recent_frame.grid_columnconfigure(0, weight=1)
        SectionTitle(recent_frame, "Recent Transactions").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6)
        )
        self.recent_table = DataTable(
            recent_frame,
            columns=[
                ("title", "Name", 130),
                ("category_name", "Category", 110),
                ("transaction_date", "Date", 90),
                ("transaction_type", "Type", 70),
                ("amount", "Amount", 90),
            ],
        )
        self.recent_table.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))

        budget_frame = ctk.CTkFrame(lower, corner_radius=14)
        budget_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        SectionTitle(budget_frame, "Budget Overview").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 8)
        )
        self.budget_container = ctk.CTkScrollableFrame(budget_frame, fg_color="transparent")
        self.budget_container.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))
        self.budget_container.grid_columnconfigure(0, weight=1)
        budget_frame.grid_rowconfigure(1, weight=1)

    def refresh(self) -> None:
        report = self.services.reports.dashboard_report()
        self.cards["balance"].set_value(format_money(report["total_balance"]))
        self.cards["income"].set_value(format_money(report["total_income"]))
        self.cards["expenses"].set_value(format_money(report["total_expenses"]))
        self.cards["savings"].set_value(format_money(report["monthly_savings"]))
        self.period_label.configure(text=f"Monthly: {format_money(report['monthly_income'])} in / {format_money(report['monthly_expenses'])} out")

        comparison = self.services.processor.month_comparison()
        difference = comparison["difference"]
        direction = "higher" if difference > 0 else "lower" if difference < 0 else "same as"
        self.comparison_label.configure(
            text=f"This month's expenses are {format_money(abs(difference))} {direction} last month."
        )

        recent = [
            {**row, "amount": format_money(row["amount"])} for row in report["recent_transactions"]
        ]
        self.recent_table.populate(recent, "No transactions yet. Add one to get started.")

        for child in self.budget_container.winfo_children():
            child.destroy()
        status = report["budget_status"]
        if not status:
            label = ctk.CTkLabel(
                self.budget_container, text="No budgets set for this month.", text_color="gray"
            )
            label.grid(row=0, column=0, pady=20)
            return
        for index, item in enumerate(status):
            row = ProgressRow(self.budget_container, item["category_name"])
            row.grid(row=index, column=0, sticky="ew", pady=6)
            row.update_values(
                format_money(item["spent"]),
                format_money(item["budget_amount"]),
                item["percentage"],
                item["exceeded"],
            )
