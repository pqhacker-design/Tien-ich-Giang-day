import pandas as pd
import re
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_parse_excel(file_path_or_buffer) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Tự động nhận diện cấu trúc file VNEDU, SMAS hoặc Excel tự do"""
        # Đọc sheet đầu tiên
        df_raw = pd.read_excel(file_path_or_buffer, header=None)
        
        # Tìm dòng chứa header chuẩn
        header_idx = 0
        mapping = {}
        
        keywords = {
            "name": [r"họ.*tên", r"tên.*học sinh", r"nguyễn văn a"],
            "code": [r"mã.*hs", r"mã.*học sinh", r"sbd"],
            "class": [r"lớp"],
            "tx": [r"đđtgk", r"thường xuyên", r"miệng", r"15p"],
            "gk": [r"giữa kỳ", r"đđtghk"],
            "ck": [r"cuối kỳ", r"đđtck"],
            "tb": [r"trung bình", r"đtb"]
        }
        
        # Quét 15 dòng đầu để tìm header
        for idx, row in df_raw.iloc[:15].iterrows():
            row_str = " ".join(row.dropna().astype(str)).lower()
            if any(re.search(pattern, row_str) for key_list in keywords.values() for pattern in key_list):
                header_idx = idx
                break
                
        df_clean = pd.read_excel(file_path_or_buffer, skiprows=header_idx)
        df_clean.columns = [str(c).strip() for c in df_clean.columns]
        
        # Mapping tự động các cột
        for col in df_clean.columns:
            col_lower = col.lower()
            for key, patterns in keywords.items():
                if any(re.search(p, col_lower) for p in patterns):
                    mapping[key] = col
                    break
                    
        return df_clean, mapping
