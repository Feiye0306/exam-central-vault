"""
考卷入庫箱與去重引擎 (Exam Ingestor)
實作 content_hash 雜湊去重、生成唯一 paper_id、與審核狀態標記
"""

import hashlib
from typing import List, Dict, Any, Tuple
from datetime import datetime
from .schema import PaperRecord
from .parser import ExamFilenameParser
from .matcher import ExamAnswerMatcher

class ExamIngestor:
    def __init__(self):
        # 內存或資料庫已登記的 content_hash 集合
        self.registered_hashes: set = set()
        self.records: List[PaperRecord] = []
        self.review_queue: List[Dict[str, Any]] = []
        self.rejected_duplicates: List[Dict[str, Any]] = []
        self.counter: int = 1

    def calculate_hash(self, file_id: str, title: str, size: int = 0) -> str:
        """
        計算檔案的指紋 Hash。
        在 Google Drive 環境中，結合 file_id 與標題及大小生成唯一指紋。
        """
        raw = f"{file_id}_{title}_{size}".encode('utf-8')
        return hashlib.sha256(raw).hexdigest()

    def process_incoming_batch(self, incoming_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批次處理入庫箱檔案
        incoming_files 格式: [{"file_id": ..., "filename": ..., "size": ..., "path": ...}, ...]
        """
        parsed_items = []
        for f in incoming_files:
            meta = ExamFilenameParser.parse(f["filename"], f.get("path", ""))
            meta["file_id"] = f["file_id"]
            meta["file_url"] = f"https://drive.google.com/file/d/{f['file_id']}/view"
            meta["size"] = f.get("size", 0)
            meta["content_hash"] = self.calculate_hash(f["file_id"], meta["title"], f.get("size", 0))
            parsed_items.append(meta)

        # 1. 執行答案卷與題目卷成對配對
        matched_questions, orphan_answers = ExamAnswerMatcher.match_papers(parsed_items)

        ingested_count = 0
        duplicate_count = 0

        today_str = datetime.now().strftime("%Y%m%d")

        for q in matched_questions:
            chash = q["content_hash"]

            # 2. 去重檢查 (Content Hash De-duplication)
            if chash in self.registered_hashes:
                self.rejected_duplicates.append({
                    "title": q["title"],
                    "file_id": q["file_id"],
                    "reason": f"重複試卷已在中央庫 (Hash: {chash[:8]}...)"
                })
                duplicate_count += 1
                continue

            # 3. 審核狀態判定 (若關鍵欄位缺失則進 review)
            status = "active"
            if not q["chapter"] or q["publisher"] == "其他":
                status = "review"

            paper_id = f"PAP_{today_str}_{self.counter:04d}"
            self.counter += 1

            record = PaperRecord(
                paper_id=paper_id,
                title=q["title"],
                grade=q["grade"],
                semester=q["semester"],
                subject=q["subject"],
                publisher=q["publisher"],
                book_title=q["book_title"],
                round_num=q["round_num"],
                chapter=q["chapter"],
                paper_type=q["paper_type"],
                difficulty=q["difficulty"],
                file_id=q["file_id"],
                file_url=q["file_url"],
                content_hash=chash,
                has_answer=q["has_answer"],
                answer_file_id=q.get("answer_file_id"),
                answer_file_url=q.get("answer_file_url"),
                status=status
            )

            self.registered_hashes.add(chash)
            self.records.append(record)
            if status == "review":
                self.review_queue.append(record)
            ingested_count += 1

        return {
            "total_processed": len(incoming_files),
            "ingested_count": ingested_count,
            "duplicate_count": duplicate_count,
            "orphan_answers_count": len(orphan_answers),
            "review_count": len(self.review_queue)
        }
