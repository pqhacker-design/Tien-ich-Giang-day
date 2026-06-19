import re
from underthesea import word_tokenize

def check_vietnamese_spelling(text):
    errors = []
    # Tokenize từ vựng tiếng Việt sơ bộ
    words = word_tokenize(text)
    
    # Giả lập bộ từ điển lỗi không dấu/sai dấu hành chính
    pattern_wrong = {
        r"\bhoc tập\b": "học tập",
        r"\btiến hành thực hiện\b": "thực hiện",
        r"\bhoạt dộng\b": "hoạt động",
        r"\bquản lí\b": "quản lý"
    }
    
    idx = 1
    for pattern, suggest in pattern_wrong.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for m in matches:
            errors.append({
                "stt": idx,
                "loai": "Chính tả",
                "goc": m.group(),
                "de_xuat": suggest,
                "muc_do": "Cao",
                "vi_tri": m.start()
            })
            idx += 1
            
    return errors