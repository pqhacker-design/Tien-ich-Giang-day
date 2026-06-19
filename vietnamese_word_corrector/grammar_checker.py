import re

def check_vietnamese_grammar(text):
    errors = []
    # Danh sách các câu hành chính rườm rà, lặp ý
    grammar_rules = [
        {
            "pattern": r"nhà trường sẽ tiến hành thực hiện tổ chức",
            "suggest": "nhà trường sẽ tổ chức",
            "loai": "Ngữ pháp",
            "muc_do": "Trung bình"
        },
        {
            "pattern": r"để nhằm mục đích",
            "suggest": "để",
            "loai": "Hành văn",
            "muc_do": "Thấp"
        }
    ]
    
    idx = 1
    for rule in grammar_rules:
        matches = re.finditer(rule["pattern"], text, re.IGNORECASE)
        for m in matches:
            errors.append({
                "stt": idx,
                "loai": rule["loai"],
                "goc": m.group(),
                "de_xuat": rule["suggest"],
                "muc_do": rule["muc_do"]
            })
            idx += 1
            
    return errors