"""
考卷中央庫 - 試算表與清冊匯出器 (Sheets Exporter)
將入庫結果產出為標準 CSV，格式 100% 契合 Google Sheets papers 分頁表頭
"""

import csv
from pathlib import Path
from typing import List
from .schema import PAPERS_SHEET_HEADERS, PaperRecord

class SheetsExporter:
    @staticmethod
    def export_to_csv(records: List[PaperRecord], out_path: Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(PAPERS_SHEET_HEADERS)
            for r in records:
                writer.writerow(r.to_row())
        return out_path
