import re
from underthesea import word_tokenize

def check_vietnamese_spelling(text):
    errors = []
    idx = 1
    
    # 1. Giả lập bộ từ điển lỗi không dấu / sai từ hành chính
    pattern_wrong = {
        r"\bhoc tập\b": "học tập",
        r"\btiến hành thực hiện\b": "thực hiện",
        r"\bhoạt dộng\b": "hoạt động",
        r"\bquản lí\b": "quản lý"
    }
    
    for pattern, suggest in pattern_wrong.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            errors.append({
                "stt": idx,
                "loai": "Chính tả",
                "goc": m.group(),
                "de_xuat": suggest,
                "muc_do": "Cao"
            })
            idx += 1

    # 2. KIỂM TRA LỖI DẤU CÂU (Bổ sung quy tắc Regex)
    punctuation_rules = [
        {
            # Khoảng trắng TRƯỚC dấu phẩy, dấu chấm, dấu hai chấm, dấu chấm phẩy
            "pattern": r"\s+([,\.:;\?!])",
            "suggest": r"\1",
            "loai": "Lỗi dấu câu",
            "note": "Không đặt khoảng trắng trước dấu câu"
        },
        {
            # Thiếu khoảng trắng SAU dấu phẩy, dấu chấm phẩy, dấu hai chấm
            "pattern": r"([,;:])([^\s\d\"])",
            "suggest": r"\1 \2",
            "loai": "Lỗi dấu câu",
            "note": "Cần có 1 khoảng trắng sau dấu câu"
        },
        {
            # Dấu ngoặc đơn mở có khoảng trắng phía sau (ví dụ: "( nội dung )")
            "pattern": r"\(\s+",
            "suggest": "(",
            "loai": "Lỗi dấu câu",
            "note": "Không có khoảng trắng sau dấu mở ngoặc"
        },
        {
            # Dấu ngoặc đơn đóng có khoảng trắng phía trước
            "pattern": r"\s+\)",
            "suggest": ")",
            "loai": "Lỗi dấu câu",
            "note": "Không có khoảng trắng trước dấu đóng ngoặc"
        }
    ]

    for rule in punctuation_rules:
        matches = re.finditer(rule["pattern"], text)
        for m in matches:
            # Tạo đề xuất sửa tự động bằng re.sub cho đoạn ngắn
            fixed_text = re.sub(rule["pattern"], rule["suggest"], m.group())
            errors.append({
                "stt": idx,
                "loai": rule["loai"],
                "goc": m.group(),
                "de_xuat": fixed_text if fixed_text != m.group() else rule["note"],
                "muc_do": "Trung bình"
            })
            idx += 1
            
    return errors
