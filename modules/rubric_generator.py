import pandas as pd

def generate_matrices(lesson_json):
    """Trích xuất ma trận mục tiêu từ JSON cấu trúc để làm dữ liệu cho bảng biểu"""
    matrix_data = lesson_json.get("ma_tran_muc_tieu", [])
    
    if not matrix_data:
        # Khung dự phòng tự động nếu AI thiếu trường
        matrix_data = [{
            "noi_dung": "Nội dung trọng tâm bài học",
            "nhan_biet": "Nhận biết các khái niệm cốt lõi.",
            "thong_hieu": "Hiểu và giải thích được bản chất.",
            "van_dung": "Giải quyết bài toán cơ bản.",
            "van_dung_cao": "Ứng dụng vào thực tiễn số hóa."
        }]
        
    df_matrix = pd.DataFrame(matrix_data)
    df_matrix.columns = ["Nội dung kiến thức", "Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"]
    
    # Tạo bảng Rubric đánh giá năng lực học sinh tương ứng
    rubric_data = [
        {"Tiêu chí đánh giá": "Mức độ tiếp thu kiến thức số", "Mức Chưa Đạt": "Chưa nắm rõ lý thuyết", "Mức Đạt": "Hiểu và làm theo hướng dẫn", "Mức Tốt": "Chủ động thực hành, sáng tạo"},
        {"Tiêu chí đánh giá": "Năng lực hợp tác giải quyết vấn đề", "Mức Chưa Đạt": "Thụ động trong làm việc nhóm", "Mức Đạt": "Hoàn thành nhiệm vụ được giao", "Mức Tốt": "Dẫn dắt, điều phối nhóm trực tuyến tốt"}
    ]
    df_rubric = pd.DataFrame(rubric_data)
    
    return df_matrix, df_rubric