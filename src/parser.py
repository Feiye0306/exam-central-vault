"""
考卷檔名與路徑解析器 (Metadata Parser)
從實體路徑與檔名智能提取標準元資料（免除老師手工改檔名或打標籤）
"""

import re
from typing import Dict, Any

class ExamFilenameParser:
    """
    支援常見檔名型態解析：
    例 1: 113上南一_高一上數學_強化導引題本_第01回_有理數與實數.pdf
    例 2: 113上南一_高一上數學_強化導引題本_第01回_有理數與實數_Ans.pdf
    例 3: 113上南一_高一數學_習作_第01回_1-1 實數.pdf
    例 4: 109高一上數_翰林差異化基礎篇_第01回_1-1 數與數線.pdf
    """
    
    @staticmethod
    def is_answer_file(filename: str) -> bool:
        lower = filename.lower()
        return bool(re.search(r'(_ans|解答|解析|簡答篇)', lower))

    @staticmethod
    def parse(filename: str, path_hint: str = "") -> Dict[str, Any]:
        raw_name = filename
        if raw_name.endswith(".pdf"):
            raw_name = raw_name[:-4]
            
        is_ans = ExamFilenameParser.is_answer_file(raw_name)
        
        # 去除 _Ans 後綴進行核心比對
        clean_name = re.sub(r'(_ans|_Ans|解答|解析)', '', raw_name).strip()
        
        # 1. 出版社
        publisher = "其他"
        for pub in ["南一", "翰林", "龍騰", "泰宇", "全華", "康熹"]:
            if pub in clean_name or pub in path_hint:
                publisher = pub
                break
                
        # 2. 年級與學期
        grade = "高一"
        if "高二" in clean_name or "高二" in path_hint:
            grade = "高二"
        elif "高三" in clean_name or "高三" in path_hint:
            grade = "高三"
        elif "國" in clean_name:
            grade = "國中"

        semester = "上"
        if "上" in clean_name or "上" in path_hint:
            semester = "上"
        elif "下" in clean_name or "下" in path_hint:
            semester = "下"

        # 3. 科目
        subject = "數學"
        for sub in ["數學", "物理", "化學", "英文", "國文", "生物", "地科"]:
            if sub in clean_name or sub in path_hint or (sub == "數學" and "數" in clean_name):
                subject = sub
                break

        # 4. 書名/系列
        book_title = "試卷"
        for b in ["強化導引題本", "差異化基礎篇", "習作", "課後練習", "段考模擬", "週考卷"]:
            if b in clean_name:
                book_title = b
                break

        # 5. 回數
        round_match = re.search(r'(第\d+回|回\d+|\bQ\d+\b)', clean_name)
        round_num = round_match.group(1) if round_match else "第01回"

        # 6. 章節 / 單元名稱
        chapter = ""
        # 嘗試從最後一個底線後面抓取
        parts = clean_name.split("_")
        if len(parts) >= 3:
            chapter = parts[-1].strip()
        else:
            chapter = clean_name

        # 7. 難度評級預設 (可依類型與章節推導)
        difficulty = "基礎 A"
        if "強化" in book_title or "進階" in clean_name:
            difficulty = "進階 B"
        elif "挑戰" in clean_name or "難" in clean_name or "競賽" in clean_name:
            difficulty = "挑戰 C"

        # 8. 配對基準鍵 (用於題目卷與答案卷精確對齊)
        pairing_key = f"{grade}_{semester}_{subject}_{publisher}_{book_title}_{round_num}".replace(" ", "")

        return {
            "title": clean_name,
            "raw_filename": filename,
            "is_answer": is_ans,
            "grade": grade,
            "semester": semester,
            "subject": subject,
            "publisher": publisher,
            "book_title": book_title,
            "round_num": round_num,
            "chapter": chapter,
            "paper_type": book_title,
            "difficulty": difficulty,
            "pairing_key": pairing_key
        }
