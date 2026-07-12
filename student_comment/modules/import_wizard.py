import pandas as pd
import re
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_detect_and_parse(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Tự động nhận diện file SMAS, VNEDU hoặc Excel bất kỳ"""
        # Đọc dữ liệu thô
        if str(uploaded_file.name).endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file, header=None)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None)
        
        header_idx = 0
        
        # Bộ từ khóa mở rộng bám sát cấu trúc SMAS/VNEDU
        keywords = {
            "code": [r"mã.*hs", r"mã.*học sinh", r"sbd", r"dinhdanh", r"stt"],
            "name": [r"họ.*tên", r"tên.*học sinh", r"họ và tên", r"hoten"],
            "class": [r"lớp", r"tenlop"],
            "tx": [r"ddgtx", r"thường xuyên", r"đđtgk", r"miệng", r"15p"],
            "gk": [r"ddggk", r"giữa kỳ", r"đđtghk", r"ddtghk"],
            "ck": [r"ddgck", r"cuối kỳ", r"đđtck", r"ddtck"],
            "tb": [r"tbm_hki", r"tbm_hkii", r"tbm", r"trung bình", r"đtb"]
        }
        
        # Quét 20 dòng đầu tiên để tìm dòng chứa tiêu đề
        for idx, row in df_raw.iloc[:20].iterrows():
            row_str = " ".join(row.dropna().astype(str)).lower()
            if any(re.search(p, row_str) for key_list in keywords.values() for p in key_list):
                header_idx = idx
                break

        # Tải lại DataFrame bỏ qua các dòng hành chính ở trên
        if str(uploaded_file.name).endswith('.csv'):
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, skiprows=header_idx)
        else:
            uploaded_file.seek(0)
            df = pd.read_excel(uploaded_file, skiprows=header_idx)
            
        df.columns = [str(c).strip() for c in df.columns]
        
        # Ánh xạ cột tự động
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            for key, patterns in keywords.items():
                if key not in column_map and any(re.search(p, col_lower) for p in patterns):
                    column_map[key] = col
                    break
                    
        return df, column_map
