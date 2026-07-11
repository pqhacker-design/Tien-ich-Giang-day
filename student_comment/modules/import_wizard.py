import pandas as pd
import re
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_detect_and_parse(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Nhận diện file VNEDU, SMAS hoặc Excel bất kỳ (Module 1)"""
        df_raw = pd.read_excel(uploaded_file, header=None)
        
        header_idx = 0
        keywords = {
            "code": [r"mã.*hs", r"mã.*học sinh", r"sbd"],
            "name": [r"họ.*tên", r"tên.*học sinh", r"họ và tên"],
            "class": [r"lớp"],
            "tx": [r"thường xuyên", r"đđtgk", r"miệng", r"15p"],
            "gk": [r"giữa kỳ", r"đđtghk"],
            "ck": [r"cuối kỳ", r"đđtck"],
            "tb": [r"trung bình", r"đtb"]
        }
        
        # Quét 15 dòng đầu để tìm dòng chứa tiêu đề
        for idx, row in df_raw.iloc[:15].iterrows():
            row_str = " ".join(row.dropna().astype(str)).lower()
            if any(re.search(p, row_str) for key_list in keywords.values() for p in key_list):
                header_idx = idx
                break

        df = pd.read_excel(uploaded_file, skiprows=header_idx)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Ánh xạ cột
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            for key, patterns in keywords.items():
                if any(re.search(p, col_lower) for p in patterns):
                    column_map[key] = col
                    break
                    
        return df, column_map
