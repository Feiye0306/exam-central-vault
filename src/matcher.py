"""
考卷答案配對引擎 (Answer Matcher)
將同一回數之題目卷與解答卷進行 100% 精準成對綁定
"""

from typing import List, Dict, Any, Tuple
from .parser import ExamFilenameParser

class ExamAnswerMatcher:
    @staticmethod
    def match_papers(files_meta: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        輸入檔案元資料清單，自動將題目卷與答案卷配對。
        回傳: (matched_papers, orphan_answers)
        """
        questions_by_key: Dict[str, Dict[str, Any]] = {}
        answers_by_key: Dict[str, Dict[str, Any]] = {}

        for item in files_meta:
            key = item["pairing_key"]
            if item["is_answer"]:
                answers_by_key[key] = item
            else:
                questions_by_key[key] = item

        # 進行成對合併
        matched_results = []
        orphan_answers = []

        for key, q in questions_by_key.items():
            if key in answers_by_key:
                ans = answers_by_key[key]
                q["has_answer"] = True
                q["answer_file_id"] = ans.get("file_id")
                q["answer_file_url"] = ans.get("file_url")
                q["answer_filename"] = ans.get("raw_filename")
            else:
                q["has_answer"] = False
                q["answer_file_id"] = None
                q["answer_file_url"] = None
                q["answer_filename"] = None
            matched_results.append(q)

        for key, a in answers_by_key.items():
            if key not in questions_by_key:
                orphan_answers.append(a)

        return matched_results, orphan_answers
