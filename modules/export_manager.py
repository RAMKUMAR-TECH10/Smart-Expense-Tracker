"""CSV export utilities."""

from __future__ import annotations

import csv
from pathlib import Path

from config import REPORTS_DIR
from modules.error_handler import ExportError, get_logger

logger = get_logger("export")

EXPORT_FIELDS = [
    "transaction_id",
    "title",
    "amount",
    "transaction_type",
    "category_name",
    "transaction_date",
    "description",
]


class ExportManager:
    def __init__(self, reports_dir: Path | str | None = None) -> None:
        self.reports_dir = Path(reports_dir) if reports_dir else REPORTS_DIR

    def export_transactions(self, rows: list[dict], filename: str = "transactions.csv") -> str:
        if not isinstance(rows, list):
            raise ExportError("No transaction records available for export.")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        path = self.reports_dir / filename
        try:
            with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=EXPORT_FIELDS, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow({field: row.get(field, "") for field in EXPORT_FIELDS})
        except (OSError, csv.Error) as exc:
            logger.error("CSV export failed: %s", exc)
            raise ExportError(f"CSV export failed: {exc}") from exc
        logger.info("Exported %d transactions to %s", len(rows), path)
        return str(path)
