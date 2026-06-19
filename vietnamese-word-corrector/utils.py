import json
import os
import docx

DEFAULT_CRITERIA = {
    "GIAO_AN": ["Mục tiêu", "Thiết bị dạy học", "Tiến trình dạy học", "Hoạt động khởi động", "Hoạt động hình thành kiến thức", "Luyện tập", "Vận dụng"],
    "BIEN_BAN": ["Thời gian", "Địa điểm", "Thành phần", "Nội dung", "Kết luận", "Chữ ký"],
    "BAO_CAO": ["Số liệu", "Minh chứng", "Đánh giá kết quả", "Phương hướng"]
}

def load_criteria():
    if os.path.exists("criteria.json"):
        with open("criteria.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CRITERIA

def save_criteria(criteria):
    with open("criteria.json", "w", encoding="utf-8") as f:
        json.dump(criteria, f, ensure_ascii=False, indent=4)

def get_docx_info(file_path):
    doc = docx.Document(file_path)
    text = []
    for p in doc.paragraphs:
        text.append(p.text)
    full_text = " ".join(text)
    words = len(full_text.split())
    # Giả lập số trang dựa trên số từ (1 trang ~ 400 từ)
    pages = max(1, words // 400)
    return {
        "filename": os.path.basename(file_path),
        "word_count": words,
        "page_count": pages,
        "full_text": full_text
    }