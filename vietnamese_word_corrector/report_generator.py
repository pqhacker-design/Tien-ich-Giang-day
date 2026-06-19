import pandas as pd
import io

def generate_excel_report(errors, score_dict):
    output = io.BytesIO()
    
    # Tạo bảng dữ liệu lỗi
    df_errors = pd.DataFrame(errors)
    if df_errors.empty:
        df_errors = pd.DataFrame(columns=["stt", "loai", "goc", "de_xuat", "muc_do", "status"])
        
    # Tạo bảng điểm số
    df_scores = pd.DataFrame([{
        "Thể thức": score_dict.get("the_thuc", 0),
        "Nội dung": score_dict.get("noi_dung", 0),
        "GDPT 2018": score_dict.get("gdpt_2018", 0),
        "Năng lực số": score_dict.get("nang_luc_so", 0),
        "Tính khoa học": score_dict.get("khoa_hoc", 0),
        "Tổng điểm": score_dict.get("tong", 0)
    }])
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_scores.to_excel(writer, sheet_name='Điểm Số Hồ Sơ', index=False)
        df_errors.to_excel(writer, sheet_name='Chi Tiết Lỗi Phát Hiện', index=False)
        
    return output.getvalue()