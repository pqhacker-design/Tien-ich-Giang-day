import pandas as pd
import io
import re
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_detect_and_parse(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str]]:
        # 1. Đọc nội dung file
        content = uploaded_file.getvalue().decode('utf-8-sig', errors='ignore')
        lines = content.splitlines()

        # 2. Tìm dòng chứa tiêu đề điểm số (DDGTX_TinhDiem / TBM_HKI)
        header_idx = -1
        for idx, line in enumerate(lines[:25]):
            if "DDGTX_TinhDiem" in line or "TBM_HKI" in line or "DDGGK_TinhDiem" in line:
                header_idx = idx
                break

        if header_idx == -1:
            header_idx = 0

        # 3. Lọc bỏ dòng chứa cấu hình JSON ("{" hoặc "PointCode") và dòng trống
        clean_lines = []
        clean_lines.append(lines[header_idx]) # Dòng header
        
        for line in lines[header_idx + 1:]:
            if '{"' in line or 'PointCode' in line or 'PointWeight' in line:
                continue
            if line.strip():
                clean_lines.append(line)

        # 4. Đưa vào Pandas xử lý bằng python engine
        clean_csv_content = "\n".join(clean_lines)
        df = pd.read_csv(
            io.StringIO(clean_csv_content),
            dtype=str,
            engine='python',
            on_bad_lines='skip'
        )

        # 5. Đặt tên chuẩn xác cho các cột theo VỊ TRÍ CỘT (Index-based)
        # File SMAS chuẩn: Cột 0: STT, Cột 1: ID, Cột 2: Mã HS, Cột 3: Họ tên
        col_names = list(df.columns)
        
        # Tạo danh sách tên cột mới an toàn
        new_cols = []
        for i, col in enumerate(col_names):
            col_str = str(col).strip()
            if i == 0:
                new_cols.append("STT")
            elif i == 1:
                new_cols.append("System_ID")
            elif i == 2:
                new_cols.append("Mã HS")
            elif i == 3:
                new_cols.append("Họ và tên")
            else:
                # Giữ nguyên tên cột điểm từ SMAS hoặc đặt tên mặc định nếu rỗng
                new_cols.append(col_str if col_str and not col_str.startswith("Unnamed") else f"Col_{i}")

        df.columns = new_cols

        # 6. Lọc lấy dòng học sinh thực sự dựa vào CỘT THỨ 4 (Index 3 - Họ và tên)
        name_col = df.columns[3]
        df = df[df[name_col].notna() & (df[name_col].astype(str).str.strip() != "")]
        
        # Bỏ dòng lặp lại tiêu đề (nếu có)
        df = df[df[name_col] != "Họ và tên"].reset_index(drop=True)

        # 7. Ánh xạ các cột điểm tự động
        found_mapping = {
            "code": "Mã HS",
            "name": name_col,
            "class": "Lớp"
        }

        # Tìm các cột điểm trong DataFrame
        for col in df.columns:
            col_lower = col.lower()
            if "ddgtx" in col_lower and "tx" not in found_mapping:
                found_mapping["tx"] = col
            elif "ddggk" in col_lower:
                found_mapping["gk"] = col
            elif "ddgck" in col_lower:
                found_mapping["ck"] = col
            elif "tbm" in col_lower:
                found_mapping["tb"] = col

        # 8. Làm sạch tất cả các giá trị về dạng Chuỗi (String) an toàn
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str)

        return df, found_mapping
