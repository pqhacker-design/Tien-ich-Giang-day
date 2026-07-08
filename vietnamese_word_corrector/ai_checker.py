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
