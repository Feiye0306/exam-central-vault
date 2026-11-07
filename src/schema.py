"""
考卷中央庫 - 營運資料庫 papers 分頁與試卷資料模型 (Schema)
依據設計提案 v1 §1.2 與 Task #90 規格定義
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

PAPERS_SHEET_HEADERS = [
    "paper_id",          # 試卷唯一識別碼 (PAP_YYYYMMDD_XXX)
    "title",             # 規範顯示全名
    "grade",             # 年級 (高一 / 高二 / 高三 / 國中)
    "semester",          # 學期 (上 / 下)
    "subject",           # 科目 (數學 / 物理 / 化學 / 英文 / 國文 / 生物 / 地科)
    "publisher",         # 出版社或來源 (南一 / 翰林 / 龍騰 / 泰宇 / 各校段考 / 歷屆模考)
    "book_title",        # 書名/系列 (強化導引題本 / 習作 / 差異化練習 / 歷屆試題)
    "round_num",         # 回數 (第01回、第02回...)
    "chapter",           # 章節或考點名稱 (如: 1-1 有理數與實數)
    "paper_type",        # 類型 (課後練習 / 單元卷 / 段考複習 / 診斷卷)
    "difficulty",        # 難度等級 (基礎 A / 進階 B / 挑戰 C)
    "file_id",           # Google Drive 試卷檔案 ID
    "file_url",          # 試卷線上檢視連結
    "content_hash",      # 內容 SHA-256 / 唯一識別指紋 (去重用)
    "has_answer",        # 是否已配對答案卷 (TRUE / FALSE)
    "answer_file_id",    # 答案卷 Google Drive 檔案 ID
    "answer_file_url",   # 答案卷線上檢視連結
    "status",            # 狀態 (active: 已入庫 / review: 待確認)
    "ingested_at"        # 入庫時間
]

@dataclass
class PaperRecord:
    paper_id: str
    title: str
    grade: str
    semester: str
    subject: str
    publisher: str
    book_title: str
    round_num: str
    chapter: str
    paper_type: str
    difficulty: str
    file_id: str
    file_url: str
    content_hash: str
    has_answer: bool = False
    answer_file_id: Optional[str] = None
    answer_file_url: Optional[str] = None
    status: str = "active"
    ingested_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_row(self):
        return [
            self.paper_id,
            self.title,
            self.grade,
            self.semester,
            self.subject,
            self.publisher,
            self.book_title,
            self.round_num,
            self.chapter,
            self.paper_type,
            self.difficulty,
            self.file_id,
            self.file_url,
            self.content_hash,
            "TRUE" if self.has_answer else "FALSE",
            self.answer_file_id or "",
            self.answer_file_url or "",
            self.status,
            self.ingested_at
        ]
