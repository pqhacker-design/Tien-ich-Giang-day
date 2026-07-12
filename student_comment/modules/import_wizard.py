import pandas as pd
import io
import re
from typing import Tuple, Dict

class AIImportWizard:
    @staticmethod
    def auto_detect_and_parse(uploaded_file) -> Tuple[pd.DataFrame, Dict[str, str]]:
        # 1. Đọc tất cả nội dung thành danh sách các dòng text
        content = uploaded_file.getvalue().decode('utf-8-sig', errors='ignore')
        lines = content.splitlines()

        # 2. Tìm dòng chứa tiêu đề cột điểm (DDGTX_TinhDiem / TBM_HKI)
        header_idx = -1
        for idx, line in enumerate(lines[:25]):
            if "DDGTX_TinhDiem" in line or "TBM_HKI" in line or "DDGGK_TinhDiem" in line:
                header_idx = idx
                break

        if header_idx == -1:
            header_idx = 0

        # 3. LỌC SẠCH DỮ LIỆU THÔ: Bỏ tất cả dòng chứa JSON cấu hình ("{" hoặc "PointCode")
        clean_lines = []
        # Lấy dòng tiêu đề
        clean_lines.append(lines[header_idx])
        
        # Lấy các dòng dữ liệu phía sau, BỎ QUA các dòng chứa JSON
        for line in lines[header_idx + 1:]:
            # Dòng chứa JSON thường bắt đầu bằng dấu ngoặc nhọn hoặc có chữ PointCode
            if '{"' in line or 'PointCode' in line or 'PointWeight' in line:
                continue
            if line.strip():  # Chỉ lấy dòng không rỗng
                clean_lines.append(line)

        # 4. Đưa chuỗi dòng đã làm sạch vào Pandas (dùng python engine để xử lý chuỗi an toàn tuyệt đối)
        clean_csv_content = "\n".join(clean_lines)
        df = pd.read_csv(
            io.StringIO(clean_csv_content),
            dtype=str,
            engine='python',        # Chuyển sang Python Engine tránh crash C-parser
            on_bad_lines='skip'     # Tự động bỏ qua các dòng nếu vẫn còn lệch cột
        )

        # 5. Đặt lại tên 4 cột đầu tiên của SMAS (vốn bị để trống tiêu đề)
        cols = list(df.columns)
        if len(cols) >= 4:
            cols[0] = "STT"
            cols[1] = "System_ID"
            cols[2] = "Mã HS"
            cols[3] = "Họ và tên"
        df.columns = [str(c).strip() for c in cols]

        # 6. Lọc chỉ giữ lại các dòng học sinh thực sự (có tên học sinh)
        df = df[df['Họ và tên'].notna() & (df['Họ và tên'].str.strip() != "")]
        df = df.reset_index(drop=True)

        # 7. Ánh xạ các cột điểm chính xác
        mapping = {
            "code": "Mã HS",
            "name": "Họ và tên",
            "class": "Lớp",
            "tx": "DDGTX_TinhDiem",
            "gk": "DDGGK_TinhDiem",
            "ck": "DDGCK_TinhDiem",
            "tb": "TBM_HKI"
        }

        found_mapping = {}
        for key, target_col in mapping.items():
            for col in df.columns:
                if target_col.lower() in col.lower():
                    found_mapping[key] = col
                    break

        # 8. Làm sạch toàn bộ dữ liệu trả về kiểu chuỗi (Tránh Segfault/ArrowTypeError)
        for col in df.columns:
            df[col] = df[col].fillna("").astype(str)

        return df, found_mapping
