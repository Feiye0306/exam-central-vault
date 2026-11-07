"""
考卷中央庫 - 實際環境批次入庫執行程式 (ingest_live.py)
用途：讀取 Google Drive 本地量產線與手邊卷成品庫，執行自動入庫、答案配對與去重，匯出標準 papers.csv
"""

import sys
import sqlite3
from pathlib import Path

# 將 src 加入路徑
sys.path.insert(0, str(Path(__file__).parent))
sys.stdout.reconfigure(encoding='utf-8')

from src.ingestor import ExamIngestor
from src.sheets_exporter import SheetsExporter

DB_PATH = Path.home() / r"AppData/Local/Google/DriveFS/103892331746295711843/metadata_sqlite_db"

def run_live_ingestion():
    if not DB_PATH.exists():
        print("錯誤：找不到 DriveFS 本地中繼庫")
        return

    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()

    # 抓取「考卷自動整理測試 / 成品測試」底下的所有 PDF
    cur.execute("SELECT stable_id FROM items WHERE id='1NaxLUoWV8ANzz9cedrMmE6vedZlEOgNm'")
    row = cur.fetchone()
    if not row:
        print("未找到成品測試目錄")
        return

    incoming_files = []
    def scan_dir(folder_id, current_path=""):
        cur.execute("""
            SELECT i.stable_id, i.id, i.local_title, i.is_folder, i.file_size
            FROM items i
            JOIN stable_parents p ON i.stable_id = p.item_stable_id
            WHERE p.parent_stable_id = ? AND i.trashed = 0
        """, (folder_id,))
        for item in cur.fetchall():
            if item[3]: # folder
                scan_dir(item[0], f"{current_path}/{item[2]}")
            else:
                if item[2].endswith(".pdf"):
                    incoming_files.append({
                        "file_id": item[1],
                        "filename": item[2],
                        "size": item[4],
                        "path": current_path
                    })

    scan_dir(row[0], "考卷自動整理測試/成品測試")
    print(f"掃描到實體 PDF 總數: {len(incoming_files)} 個")

    # 執行入庫
    ingestor = ExamIngestor()
    stats = ingestor.process_incoming_batch(incoming_files)

    print("\n=== 入庫處理結果統計 ===")
    print(f"處理檔案數: {stats['total_processed']}")
    print(f"成功入庫試卷數: {stats['ingested_count']}")
    print(f"重複檔案被攔截數: {stats['duplicate_count']}")
    print(f"孤立答案卷數: {stats['orphan_answers_count']}")
    print(f"待確認 (Review) 數: {stats['review_count']}")

    # 匯出至 data/papers.csv
    out_csv = Path(__file__).parent / "data" / "papers.csv"
    SheetsExporter.export_to_csv(ingestor.records, out_csv)
    print(f"\n✅ 營運庫 papers 分頁資料已匯出至: {out_csv} (共 {len(ingestor.records)} 筆紀錄)")

    # 輸出入庫清單摘要
    print("\n=== 入庫清冊摘要 (前 10 筆) ===")
    for r in ingestor.records[:10]:
        ans_flag = "有答案" if r.has_answer else "無答案"
        print(f"[{r.paper_id}] {r.title} | {r.grade}{r.semester}{r.subject} | {r.difficulty} | {ans_flag}")

if __name__ == "__main__":
    run_live_ingestion()
