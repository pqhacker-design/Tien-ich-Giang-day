import pandas as pd
import re
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_detect_and_parse(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Nhận diện chính xác file SMAS / VNEDU và ép kiểu an toàn cho Streamlit/Arrow"""
        
        # 1. Đọc thô tất cả các hàng
        if str(uploaded_file.name).endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file, header=None, dtype=str)
        else:
            df_raw = pd.read_excel(uploaded_file, header=None, dtype=str)
        
        # 2. Tìm dòng chứa tiêu đề cột chính xác (tìm dòng có DDGTX_TinhDiem hoặc Tên học sinh)
        header_idx = None
        for idx, row in df_raw.iterrows():
            row_str = " ".join(row.dropna().astype(str)).lower()
            if "ddgtx" in row_str or "họ và tên" in row_str or "nguyễn" in row_str:
                # Nếu gặp dòng tiêu đề chứa tên cột
                if "ddgtx_tinhdiem" in row_str or "ddggk_tinhdiem" in row_str:
                    header_idx = idx
                    break
                # Nếu phát hiện dòng dữ liệu đầu tiên, tiêu đề là dòng ngay trước đó
                elif idx > 0 and header_idx is None:
                    header_idx = idx - 1
                    break
        
        if header_idx is None:
            header_idx = 0

        # 3. Đọc lại dữ liệu đúng từ dòng tiêu đề
        uploaded_file.seek(0)
        if str(uploaded_file.name).endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=header_idx, dtype=str)
        else:
            df = pd.read_excel(uploaded_file, skiprows=header_idx, dtype=str)
            
        # Làm sạch tên cột
        df.columns = [str(c).strip() for c in df.columns]
        
        # 4. Bỏ các hàng JSON metadata cấu hình (đặc trưng của SMAS)
        df = df[~df.iloc[:, 0].astype(str).str.contains(r'\{.*"PointCode"', na=False)].reset_index(drop=True)
        # Bỏ các hàng trống hoặc hàng tiêu đề lặp lại
        df = df.dropna(how='all').reset_index(drop=True)

        # 5. Định nghĩa bộ ánh xạ từ khóa cho SMAS/VNEDU
        keywords = {
            "code": [r"mã.*hs", r"mã.*học sinh", r"sbd", r"dinhdanh"],
            "name": [r"họ.*tên", r"tên.*học sinh", r"họ và tên", r"hoten"],
            "class": [r"lớp", r"tenlop"],
            "tx": [r"ddgtx", r"thường xuyên", r"đđtgk", r"miệng"],
            "gk": [r"ddggk", r"giữa kỳ", r"đđtghk"],
            "ck": [r"ddgck", r"cuối kỳ", r"đđtck"],
            "tb": [r"tbm_hki", r"tbm_hkii", r"tbm", r"trung bình", r"đtb"]
        }
        
        column_map = {}
        for col in df.columns:
            col_lower = col.lower()
            for key, patterns in keywords.items():
                if key not in column_map and any(re.search(p, col_lower) for p in patterns):
                    column_map[key] = col
                    break

        # 6. Ép kiểu dữ liệu an toàn (tránh lỗi ArrowTypeError & Segfault)
        for col in df.columns:
            # Chuyển các giá trị NaN/None thành chuỗi rỗng hoặc chuẩn hóa định dạng
            df[col] = df[col].fillna("").astype(str)

        return df, column_map
