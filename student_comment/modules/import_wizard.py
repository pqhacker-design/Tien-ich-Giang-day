import pandas as pd
import io
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_detect_and_parse(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str]]:
        # 1. Đọc tất cả dòng dưới dạng text thuần để tránh lỗi parse C-engine
        content = uploaded_file.getvalue().decode('utf-8-sig', errors='ignore')
        lines = content.splitlines()

        header_idx = -1
        for idx, line in enumerate(lines[:25]):
            if "DDGTX_TinhDiem" in line or "TBM_HKI" in line:
                header_idx = idx
                break

        if header_idx == -1:
            header_idx = 0

        # 2. Đọc vào Pandas từ dòng tiêu đề phát hiện được
        df = pd.read_csv(
            io.StringIO(content), 
            skiprows=header_idx, 
            dtype=str, 
            on_bad_lines='skip'
        )

        # 3. Gán lại tên cho 4 cột đầu tiên (do file SMAS để trống 4 cột đầu ở dòng tiêu đề)
        cols = list(df.columns)
        if len(cols) >= 4:
            cols[0] = "STT"
            cols[1] = "System_ID"
            cols[2] = "Mã HS"
            cols[3] = "Họ và tên"
        df.columns = [str(c).strip() for c in cols]

        # 4. Loại bỏ các dòng JSON metadata cấu hình SMAS & dòng trống
        df = df[~df['STT'].astype(str).str.contains(r'\{|"Id"|Batch', na=False)]
        df = df[df['Họ và tên'].notna() & (df['Họ và tên'].str.strip() != "")]
        df = df.reset_index(drop=True)

        # 5. Ánh xạ cột tự động sang chuẩn hệ thống
        mapping = {
            "code": "Mã HS",
            "name": "Họ và tên",
            "class": "Lớp",
            "tx": "DDGTX_TinhDiem",
            "gk": "DDGGK_TinhDiem",
            "ck": "DDGCK_TinhDiem",
            "tb": "TBM_HKI"
        }

        # Tìm các cột điểm thực tế trong DataFrame
        found_mapping = {}
        for key, target_col in mapping.items():
            for col in df.columns:
                if target_col.lower() in col.lower():
                    found_mapping[key] = col
                    break

        # Sửa kiểu dữ liệu an toàn chống Segfault cho PyArrow
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str)

        return df, found_mapping
