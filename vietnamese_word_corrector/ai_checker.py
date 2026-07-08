import google.generativeai as genai
import json
import streamlit as st
import re

def get_ai_response(prompt):
    api_key = st.session_state.get("gemini_api_key", "") # Sửa lại key đồng bộ với trang chủ
    if not api_key:
        return "Chưa cấu hình API Key tại trang chủ."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}"
def detect_headings_with_ai(text):
    """Sử dụng Gemini để nhận diện danh sách các câu/đoạn là đề mục trong văn bản"""
    prompt = f"""
    Hãy đọc văn bản sau và liệt kê chính xác tất cả các DÒNG TÊN ĐỀ MỤC, TIÊU ĐỀ CON, HOẶC MỤC LỚN có trong văn bản.
    Chỉ trả về dạng danh sách JSON các chuỗi ký tự đề mục, không giải thích gì thêm.
    Ví dụ: ["1. Mục đích", "II. Nội dung công việc", "a) Chuẩn bị"]

    Nội dung văn bản:
    {text[:3000]}
    """
    res = get_ai_response(prompt)
    try:
        import json, re
        match = re.search(r'\[.*\]', res, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return []
def classify_paragraphs_with_ai(paragraph_list):
    """
    Sử dụng AI phân loại cấu trúc cho từng đoạn văn trong file Word.
    Trả về danh sách loại hình tương ứng: QUOC_HIEU, MAIN_TITLE, HEADING_1, HEADING_2, BODY_TEXT, SIGNATURE
    """
    if not paragraph_list:
        return []
    
    # Chuẩn bị dữ liệu gửi cho AI (đánh số dòng)
    numbered_paragraphs = [f"[{i}] {p}" for i, p in enumerate(paragraph_list)]
    prompt_text = "\n".join(numbered_paragraphs[:150]) # Phân tích tối đa 150 đoạn đầu

    prompt = f"""
    Bạn là một chuyên gia về thể thức văn bản hành chính Việt Nam (Nghị định 30/2020/NĐ-CP).
    Hãy phân loại vai trò của từng dòng văn bản dưới đây thành một trong các nhãn sau:
    - QUOC_HIEU: Quốc hiệu, tiêu ngữ (CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM...)
    - MAIN_TITLE: Tên loại văn bản / Tiêu đề lớn nhất (BÁO CÁO, QUYẾT ĐỊNH, BẢNG THUYẾT MINH..., Tên dự án/sự kiện)
    - HEADING_1: Đề mục lớn, tiêu đề phần/chương/mục (1., 2., I., II., TỔNG QUAN, PHÂN TÍCH, KẾT LUẬN, SỰ KIỆN...)
    - HEADING_2: Đề mục nhỏ hơn (a), b), Ý nghĩa:, Tông màu:, Phông chữ...)
    - BODY_TEXT: Đoạn văn nội dung thông thường
    - SIGNATURE: Nơi nhận, Chức danh, Chữ ký cuối văn bản

    Yêu cầu trả về JSON duy nhất là 1 danh sách chuỗi nhãn tương ứng theo đúng thứ tự index [0], [1], [2]...
    Ví dụ: ["MAIN_TITLE", "HEADING_1", "BODY_TEXT", "HEADING_2", "BODY_TEXT"]

    Danh sách dòng:
    {prompt_text}
    """
    
    res = get_ai_response(prompt)
    try applicants:
        import json, re
        match = re.search(r'\[.*\]', res, re.DOTALL)
        if match:
            labels = json.loads(match.group())
            # Nếu thiếu nhãn do văn bản dài hơn 150 dòng, bổ sung BODY_TEXT cho phần còn lại
            while len(labels) < len(paragraph_list):
                labels.append("BODY_TEXT")
            return labels
    except Exception:
        pass
        
    # Mặc định trả về BODY_TEXT nếu AI gặp lỗi
    return ["BODY_TEXT"] * len(paragraph_list)
def analyze_document_with_ai(text, file_name):
    prompt = f"""
    Bạn là Chuyên gia kiểm định văn bản hành chính và hồ sơ giáo dục theo chương trình GDPT 2018.
    Hãy phân tích văn bản sau (Tên file: {file_name}):
    ---
    {text[:4000]}
    ---
    Trả về định dạng JSON duy nhất, không bao gồm ký tự markdown loại khác ngoài json. Cấu trúc JSON như sau:
    {{
       "loai_ho_so": "Tên loại hồ sơ nhận diện",
       "do_tin_cay": 95,
       "diem": {{
          "the_thuc": 90,
          "noi_dung": 85,
          "gdpt_2018": 80,
          "nang_luc_so": 75,
          "khoa_hoc": 85,
          "tong": 83
       }},
       "xep_loai": "Khá",
       "thieu_sot_cau_truc": ["Thiếu mục Vận dụng"],
       "gdpt_2018_check": {{
          "pham_chat": "Đã thể hiện đạt yêu cầu",
          "nang_luc_chung": "Cần làm rõ",
          "nang_luc_dac_thu": "Tốt"
       }},
       "de_xuat_cai_tien": ["Bổ sung hoạt động vận dụng thực tiễn"],
       "loi_the_thuc": [
          {{"stt": 1, "loai": "Thể thức", "goc": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", "de_xuat": "In đậm, căn giữa", "muc_do": "Cao"}}
       ]
    }}
    """
    res = get_ai_response(prompt)
    if res:
        try:
            # Sử dụng Regex bóc tách nội dung nằm giữa cặp ngoặc nhọn {} nếu có text thừa xung quanh
            json_match = re.search(r'\{.*\}', res, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)
                return json.loads(cleaned)
            
            # Dự phòng phương pháp cũ nếu regex không khớp
            cleaned = res.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except Exception as e:
            # Nếu phân rã thất bại, trả về chuỗi thông báo lỗi để giao diện bắt được
            return f"Lỗi phân rã cấu trúc JSON từ AI: {str(e)}. Phản hồi thô: {res}"
    return None
