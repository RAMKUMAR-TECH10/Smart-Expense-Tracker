"""Main application window and navigation shell."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import customtkinter as ctk

from config import APP_NAME, CURRENCY_SYMBOL, DATABASE_PATH, REPORTS_DIR, VERSION
from gui import AppServices
from gui.add_transaction import AddTransactionView
from gui.analytics_view import AnalyticsView
from gui.budget_view import BudgetView
from gui.category_view import CategoryView
from gui.components import SectionTitle, show_error, show_info
from gui.dashboard import DashboardView
from gui.transaction_view import TransactionView

NAV_ITEMS = (
    ("Dashboard", "dashboard"),
    ("Transactions", "transactions"),
    ("Add Transaction", "add_transaction"),
    ("Categories", "categories"),
    ("Budgets", "budgets"),
    ("Reports", "reports"),
    ("Settings", "settings"),
)


class SettingsView(ctk.CTkFrame):
    def __init__(self, master: Any, services: AppServices) -> None:
        super().__init__(master, fg_color="transparent")
        self.services = services
        self.grid_columnconfigure(0, weight=1)
        SectionTitle(self, "Settings").grid(row=0, column=0, sticky="w", pady=(8, 12))

        card = ctk.CTkFrame(self, corner_radius=14)
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="Appearance", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=18, pady=(16, 6)
        )
        theme = ctk.CTkSegmentedButton(
            card,
            values=["Light", "Dark", "System"],
            command=self._change_theme,
        )
        theme.set("Dark")
        theme.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        ctk.CTkLabel(card, text="Database & Reports", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, sticky="w", padx=18, pady=(6, 6)
        )
        ctk.CTkLabel(card, text=f"Database: {DATABASE_PATH}", text_color="gray", anchor="w").grid(
            row=3, column=0, sticky="ew", padx=18, pady=2
        )
        ctk.CTkLabel(
            card,
            text=f"Currency: {CURRENCY_SYMBOL}   |   Version: {VERSION}",
            text_color="gray",
            anchor="w",
        ).grid(row=4, column=0, sticky="ew", padx=18, pady=(2, 14))

        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 18))
        ctk.CTkButton(buttons, text="Backup Database", command=self.backup_database).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(buttons, text="Export All CSV", command=self.export_csv).pack(side="left")

        ctk.CTkLabel(
            self,
            text="All financial data stays on this computer. No external API or account is required.",
            text_color="gray",
            anchor="w",
        ).grid(row=2, column=0, sticky="w", pady=12)

    @staticmethod
    def _change_theme(value: str) -> None:
        ctk.set_appearance_mode(value.lower())

    def backup_database(self) -> None:
        try:
            REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = Path(REPORTS_DIR) / f"expense_tracker_backup_{stamp}.db"
            shutil.copy2(DATABASE_PATH, target)
        except OSError as exc:
            show_error(str(exc), "Backup Failed")
            return
        show_info(f"Backup saved to:\n{target}")

    def export_csv(self) -> None:
        try:
            path = self.services.exporter.export_transactions(
                self.services.transactions.get_all(), "all_transactions.csv"
            )
        except Exception as exc:  # noqa: BLE001
            show_error(str(exc), "Export Failed")
            return
        show_info(f"CSV exported to:\n{path}")


class MainWindow(ctk.CTk):
    def __init__(self, services: AppServices) -> None:
        super().__init__()
        self.services = services
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1240x780")
        self.minsize(1020, 660)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.views: dict[str, ctk.CTkFrame] = {}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.current_view = ""

        self._build_sidebar()
        self.content = ctk.CTkFrame(self, corner_radius=14, fg_color=("gray96", "gray13"))
        self.content.grid(row=0, column=1, sticky="nsew", padx=(0, 14), pady=14)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.show_view("dashboard")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            sidebar,
            text=APP_NAME,
            font=ctk.CTkFont(size=18, weight="bold"),
            wraplength=190,
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(24, 2))
        ctk.CTkLabel(
            sidebar, text="Personal Finance Manager", text_color="gray", font=ctk.CTkFont(size=11)
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 24))

        for index, (label, key) in enumerate(NAV_ITEMS, start=2):
            button = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray20", "gray80"),
                hover_color=("gray80", "gray25"),
                command=lambda item=key: self.show_view(item),
            )
            button.grid(row=index, column=0, sticky="ew", padx=12, pady=4)
            self.nav_buttons[key] = button

        ctk.CTkLabel(
            sidebar, text=f"Offline • Local SQLite data\nv{VERSION}", text_color="gray", font=ctk.CTkFont(size=10)
        ).grid(row=len(NAV_ITEMS) + 3, column=0, sticky="sw", padx=18, pady=(0, 20))
        sidebar.grid_rowconfigure(len(NAV_ITEMS) + 2, weight=1)

    def show_view(self, key: str) -> None:
        if key not in self.views:
            factories: dict[str, Any] = {
                "dashboard": lambda: DashboardView(self.content, self.services),
                "transactions": lambda: TransactionView(self.content, self.services),
                "add_transaction": lambda: AddTransactionView(self.content, self.services),
                "categories": lambda: CategoryView(self.content, self.services),
                "budgets": lambda: BudgetView(self.content, self.services),
                "reports": lambda: AnalyticsView(self.content, self.services),
                "settings": lambda: SettingsView(self.content, self.services),
            }
            self.views[key] = factories[key]()
        for view_key, button in self.nav_buttons.items():
            button.configure(
                fg_color=("#3B8ED0" if view_key == key else "transparent"),
                text_color=("white" if view_key == key else ("gray20", "gray80")),
            )
        for view in self.views.values():
            view.grid_forget()
        view = self.views[key]
        view.grid(row=0, column=0, sticky="nsew", padx=18, pady=12)
        self.current_view = key
        if hasattr(view, "refresh"):
            view.refresh()

    def refresh_all(self) -> None:
        for key, view in self.views.items():
            if key == self.current_view:
                continue
            if hasattr(view, "refresh"):
                try:
                    view.refresh()
                except Exception as exc:  # noqa: BLE001
                    from modules.error_handler import log_error

                    log_error(f"Failed to refresh view '{key}'", exc)

    def on_close(self) -> None:
        try:
            self.services.database.close()
        finally:
            self.destroy()
