"""
考卷中央庫步驟 1 單元測試與驗收腳本 (test_vault.py)
驗收指標：
1. 輔導課實體卷批次入庫 (>=20 份)
2. 答案成對配對 100%
3. content_hash 重複入庫攔截
4. 元資料自動解析完整度
"""

import pytest
import sqlite3
import sys
from pathlib import Path

# 將 src 加入 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.schema import PaperRecord, PAPERS_SHEET_HEADERS
from src.parser import ExamFilenameParser
from src.matcher import ExamAnswerMatcher
from src.ingestor import ExamIngestor
from src.sheets_exporter import SheetsExporter

# 輔導課真實題本 19 份題目卷 + 19 份解答卷 Mock 資料
SAMPLE_NAN_YI_DATA = [
    # 第 1 回
    {"file_id": "FID_01_Q", "filename": "113上南一_高一上數學_強化導引題本_第01回_有理數與實數.pdf", "size": 491005},
    {"file_id": "FID_01_A", "filename": "113上南一_高一上數學_強化導引題本_第01回_有理數與實數_Ans.pdf", "size": 500636},
    # 第 2 回
    {"file_id": "FID_02_Q", "filename": "113上南一_高一上數學_強化導引題本_第02回_乘法公式、分式與根式運算.pdf", "size": 466954},
    {"file_id": "FID_02_A", "filename": "113上南一_高一上數學_強化導引題本_第02回_乘法公式、分式與根式運算_Ans.pdf", "size": 476607},
    # 第 3 回
    {"file_id": "FID_03_Q", "filename": "113上南一_高一上數學_強化導引題本_第03回_雙重根式與算幾不等式.pdf", "size": 492652},
    {"file_id": "FID_03_A", "filename": "113上南一_高一上數學_強化導引題本_第03回_雙重根式與算幾不等式_Ans.pdf", "size": 502195},
    # 第 4 回
    {"file_id": "FID_04_Q", "filename": "113上南一_高一上數學_強化導引題本_第04回_數線的幾何性質與分點公式.pdf", "size": 595093},
    {"file_id": "FID_04_A", "filename": "113上南一_高一上數學_強化導引題本_第04回_數線的幾何性質與分點公式_Ans.pdf", "size": 600065},
    # 第 5 回
    {"file_id": "FID_05_Q", "filename": "113上南一_高一上數學_強化導引題本_第05回_含絕對值的方程式與不等式.pdf", "size": 459101},
    {"file_id": "FID_05_A", "filename": "113上南一_高一上數學_強化導引題本_第05回_含絕對值的方程式與不等式_Ans.pdf", "size": 468759},
    # 第 6 回
    {"file_id": "FID_06_Q", "filename": "113上南一_高一上數學_強化導引題本_第06回_指數律.pdf", "size": 473432},
    {"file_id": "FID_06_A", "filename": "113上南一_高一上數學_強化導引題本_第06回_指數律_Ans.pdf", "size": 483112},
    # 第 7 回
    {"file_id": "FID_07_Q", "filename": "113上南一_高一上數學_強化導引題本_第07回_科學記號與常用對數.pdf", "size": 462123},
    {"file_id": "FID_07_A", "filename": "113上南一_高一上數學_強化導引題本_第07回_科學記號與常用對數_Ans.pdf", "size": 471781},
    # 第 8 回
    {"file_id": "FID_08_Q", "filename": "113上南一_高一上數學_強化導引題本_第08回_直線方程式.pdf", "size": 558448},
    {"file_id": "FID_08_A", "filename": "113上南一_高一上數學_強化導引題本_第08回_直線方程式_Ans.pdf", "size": 563443},
    # 第 9 回
    {"file_id": "FID_09_Q", "filename": "113上南一_高一上數學_強化導引題本_第09回_直線方程式的應用.pdf", "size": 485968},
    {"file_id": "FID_09_A", "filename": "113上南一_高一上數學_強化導引題本_第09回_直線方程式的應用_Ans.pdf", "size": 497032},
    # 第 10 回
    {"file_id": "FID_10_Q", "filename": "113上南一_高一上數學_強化導引題本_第10回_圓的方程式.pdf", "size": 602480},
    {"file_id": "FID_10_A", "filename": "113上南一_高一上數學_強化導引題本_第10回_圓的方程式_Ans.pdf", "size": 607472},
    # 第 11 回
    {"file_id": "FID_11_Q", "filename": "113上南一_高一上數學_強化導引題本_第11回_圓與直線的關係.pdf", "size": 587328},
    {"file_id": "FID_11_A", "filename": "113上南一_高一上數學_強化導引題本_第11回_圓與直線的關係_Ans.pdf", "size": 592280},
    # 第 12 回
    {"file_id": "FID_12_Q", "filename": "113上南一_高一上數學_強化導引題本_第12回_圓的切線.pdf", "size": 468740},
    {"file_id": "FID_12_A", "filename": "113上南一_高一上數學_強化導引題本_第12回_圓的切線_Ans.pdf", "size": 478542},
    # 第 13 回
    {"file_id": "FID_13_Q", "filename": "113上南一_高一上數學_強化導引題本_第13回_多項式的四則運算.pdf", "size": 552023},
    {"file_id": "FID_13_A", "filename": "113上南一_高一上數學_強化導引題本_第13回_多項式的四則運算_Ans.pdf", "size": 557014},
    # 第 14 回
    {"file_id": "FID_14_Q", "filename": "113上南一_高一上數學_強化導引題本_第14回_餘式定理與因式定理.pdf", "size": 434081},
    {"file_id": "FID_14_A", "filename": "113上南一_高一上數學_強化導引題本_第14回_餘式定理與因式定理_Ans.pdf", "size": 443775},
    # 第 15 回
    {"file_id": "FID_15_Q", "filename": "113上南一_高一上數學_強化導引題本_第15回_二次函數的圖形.pdf", "size": 561669},
    {"file_id": "FID_15_A", "filename": "113上南一_高一上數學_強化導引題本_第15回_二次函數的圖形_Ans.pdf", "size": 566680},
    # 第 16 回
    {"file_id": "FID_16_Q", "filename": "113上南一_高一上數學_強化導引題本_第16回_二次函數的最大值與最小值.pdf", "size": 567805},
    {"file_id": "FID_16_A", "filename": "113上南一_高一上數學_強化導引題本_第16回_二次函數的最大值與最小值_Ans.pdf", "size": 573600},
    # 第 17 回
    {"file_id": "FID_17_Q", "filename": "113上南一_高一上數學_強化導引題本_第17回_三次函數及其圖形.pdf", "size": 559084},
    {"file_id": "FID_17_A", "filename": "113上南一_高一上數學_強化導引題本_第17回_三次函數及其圖形_Ans.pdf", "size": 564121},
    # 第 18 回
    {"file_id": "FID_18_Q", "filename": "113上南一_高一上數學_強化導引題本_第18回_多項式不等式.pdf", "size": 476270},
    {"file_id": "FID_18_A", "filename": "113上南一_高一上數學_強化導引題本_第18回_多項式不等式_Ans.pdf", "size": 494504},
    # 第 19 回
    {"file_id": "FID_19_Q", "filename": "113上南一_高一上數學_強化導引題本_第19回_簡答篇.pdf", "size": 489077},
    {"file_id": "FID_19_A", "filename": "113上南一_高一上數學_強化導引題本_第19回_簡答篇_Ans.pdf", "size": 489065},
    # 加測：第 19 & 20 份 習作卷 (單卷無 Ans)
    {"file_id": "FID_EX_01", "filename": "113上南一_高一數學_習作_第01回_1-1 實數.pdf", "size": 406120},
    {"file_id": "FID_EX_02", "filename": "113上南一_高一數學_習作_第02回_1-2 絕對值.pdf", "size": 390281}
]

def test_metadata_parsing():
    """測試檔名解析是否自動提取正確元資料"""
    meta = ExamFilenameParser.parse("113上南一_高一上數學_強化導引題本_第01回_有理數與實數.pdf")
    assert meta["grade"] == "高一"
    assert meta["semester"] == "上"
    assert meta["subject"] == "數學"
    assert meta["publisher"] == "南一"
    assert meta["book_title"] == "強化導引題本"
    assert meta["round_num"] == "第01回"
    assert meta["chapter"] == "有理數與實數"
    assert meta["difficulty"] == "進階 B"
    assert meta["is_answer"] is False

def test_batch_ingestion_and_answer_matching():
    """驗收目標 1 & 2: 批次入庫 >= 20 份，答案配對率 100%"""
    ingestor = ExamIngestor()
    result = ingestor.process_incoming_batch(SAMPLE_NAN_YI_DATA)

    # 40 份檔案入庫處理 -> 18 份導引題本題目卷 + 2 份習作 = 20 份成卷
    assert result["ingested_count"] == 20
    assert len(ingestor.records) == 20

    # 驗證前 18 份導引題本 100% 配對答案卷
    guide_records = [r for r in ingestor.records if r.book_title == "強化導引題本"]
    assert len(guide_records) == 18
    for r in guide_records:
        assert r.has_answer is True, f"{r.title} 答案配對失敗！"
        assert r.answer_file_id is not None
        assert r.answer_file_id.endswith("_A")
        assert r.status == "active"

    # 驗證習作卷未配對答案 (has_answer=False)
    exercise_records = [r for r in ingestor.records if r.book_title == "習作"]
    assert len(exercise_records) == 2
    for er in exercise_records:
        assert er.has_answer is False

def test_content_hash_deduplication():
    """驗收目標 3: 重複丟入同一份卷，被 content_hash 攔截不重複建列"""
    ingestor = ExamIngestor()
    # 第一次入庫
    res1 = ingestor.process_incoming_batch(SAMPLE_NAN_YI_DATA[:2]) # 第 1 回題目與答案
    assert res1["ingested_count"] == 1
    assert len(ingestor.records) == 1

    # 第二次重複丟入完全相同檔案
    res2 = ingestor.process_incoming_batch(SAMPLE_NAN_YI_DATA[:2])
    assert res2["ingested_count"] == 0
    assert res2["duplicate_count"] == 1
    assert len(ingestor.records) == 1
    assert len(ingestor.rejected_duplicates) == 1
    assert "重複試卷" in ingestor.rejected_duplicates[0]["reason"]

def test_sheets_export(tmp_path):
    """驗收目標 4: 匯出格式完整對齊 papers 表 19 欄結構"""
    ingestor = ExamIngestor()
    ingestor.process_incoming_batch(SAMPLE_NAN_YI_DATA)
    
    out_csv = tmp_path / "papers.csv"
    SheetsExporter.export_to_csv(ingestor.records, out_csv)

    assert out_csv.exists()
    content = out_csv.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 21 # 表頭 + 20 筆紀錄
    header = lines[0].strip().split(",")
    assert header == PAPERS_SHEET_HEADERS
