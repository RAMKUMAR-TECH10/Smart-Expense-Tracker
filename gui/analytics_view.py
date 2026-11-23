"""Charts and financial analytics view."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from gui import AppServices
from gui.components import SectionTitle, show_error, show_info
from modules.error_handler import ExpenseTrackerError


class ChartPanel(ctk.CTkFrame):
    def __init__(self, master: Any, title: str) -> None:
        super().__init__(master, corner_radius=14)
        self.grid_columnconfigure(0, weight=1)
        SectionTitle(self, title).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
        self.figure = Figure(figsize=(6, 3.2), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 10))
        self.grid_rowconfigure(1, weight=1)

    def render(self, draw: Any) -> None:
        self.axes.clear()
        draw(self.axes)
        self.figure.tight_layout()
        self.canvas.draw()


class AnalyticsView(ctk.CTkFrame):
    def __init__(self, master: Any, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.services = services
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(8, 10))
        SectionTitle(toolbar, "Reports & Analytics").pack(side="left")
        ctk.CTkButton(toolbar, text="Refresh", command=self.refresh, width=90).pack(side="right", padx=6)
        ctk.CTkButton(
            toolbar, text="Save Text Report", command=self.save_report, width=140
        ).pack(side="right", padx=6)

        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, sticky="nsew")
        container.grid_columnconfigure((0, 1), weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        self.monthly_panel = ChartPanel(container, "Monthly Income vs Expenses")
        self.monthly_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=6)

        self.category_panel = ChartPanel(container, "Category-wise Spending")
        self.category_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=6)

        self.trend_panel = ChartPanel(container, "Six-Month Trend")
        self.trend_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=6)

        summary = ctk.CTkFrame(container, corner_radius=14)
        summary.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=6)
        SectionTitle(summary, "Savings Overview").grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))
        self.summary_label = ctk.CTkLabel(
            summary, text="", justify="left", anchor="nw", font=ctk.CTkFont(size=13)
        )
        self.summary_label.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        summary.grid_rowconfigure(1, weight=1)

    def refresh(self) -> None:
        try:
            data = self.services.processor.chart_data()
        except ExpenseTrackerError as exc:
            show_error(str(exc), "Analytics Error")
            return

        monthly = data["monthly"]

        def draw_monthly(ax: Any) -> None:
            labels = ["Income", "Expenses"]
            values = [float(monthly["income"]), float(monthly["expenses"])]
            bars = ax.bar(labels, values, color=["#1E9E63", "#D9534F"], width=0.55)
            ax.set_ylabel("Amount")
            ax.set_title("Current Month")
            ax.grid(axis="y", alpha=0.25)
            for bar, value in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value,
                    f"{value:,.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

        self.monthly_panel.render(draw_monthly)

        spending = data["category_spending"]

        def draw_categories(ax: Any) -> None:
            if spending.empty:
                ax.text(0.5, 0.5, "No expense data yet", ha="center", va="center")
                ax.set_axis_off()
                return
            ax.barh(
                spending["category_name"].astype(str),
                spending["amount"].astype(float),
                color="#4A90E2",
            )
            ax.invert_yaxis()
            ax.set_xlabel("Amount")
            ax.grid(axis="x", alpha=0.25)

        self.category_panel.render(draw_categories)

        trend = data["monthly_trend"]

        def draw_trend(ax: Any) -> None:
            if trend.empty:
                ax.text(0.5, 0.5, "No trend data yet", ha="center", va="center")
                ax.set_axis_off()
                return
            months = trend["month"].astype(str)
            ax.plot(months, trend["income"], marker="o", label="Income", color="#1E9E63")
            ax.plot(months, trend["expense"], marker="o", label="Expenses", color="#D9534F")
            ax.plot(months, trend["savings"], marker="o", label="Savings", color="#3B82C4")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.25)
            ax.tick_params(axis="x", rotation=30)

        self.trend_panel.render(draw_trend)

        comparison = data["comparison"]
        self.summary_label.configure(
            text=(
                f"Monthly income:   {monthly['income']:,.2f}\n"
                f"Monthly expenses: {monthly['expenses']:,.2f}\n"
                f"Monthly savings:  {monthly['savings']:,.2f}\n\n"
                f"Last month:       {comparison['previous_expenses']:,.2f}\n"
                f"Change:           {comparison['difference']:,.2f}"
            )
        )

    def save_report(self) -> None:
        try:
            report = self.services.reports.monthly_report()
            path = self.services.reports.save_text_report(
                self.services.reports.format_text_report(report)
            )
        except (ExpenseTrackerError, OSError) as exc:
            show_error(str(exc), "Report Failed")
            return
        show_info(f"Report saved to:\n{path}")
