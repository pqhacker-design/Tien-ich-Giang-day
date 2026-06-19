import google.generativeai as genai
import json
import streamlit as st

def get_ai_response(prompt):
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi kết nối AI: {str(e)}"

def analyze_document_with_ai(text, file_name):
    # Prompt phân tích tổng hợp & chấm điểm hồ sơ học đường + NĐ30
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
       "thieu_sot_cau_truc": ["Thiếu mục Vận dụng", "Thiếu tiêu chí đánh giá số"],
       "gdpt_2018_check": {{
          "pham_chat": "Đã thể hiện đạt yêu cầu",
          "nang_luc_chung": "Cần làm rõ năng lực giải quyết vấn đề",
          "nang_luc_dac_thu": "Tốt"
       }},
       "de_xuat_cai_tien": ["Bổ sung hoạt động vận dụng thực tiễn", "Tăng cường công cụ đánh giá số"],
       "loi_the_thuc": [
          {{"stt": 1, "loai": "Thể thức", "goc": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM (thiếu in đậm)", "de_xuat": "In đậm, căn giữa", "muc_do": "Cao"}}
       ]
    }}
    """
    res = get_ai_response(prompt)
    if res:
        try:
            # Làm sạch chuỗi JSON nếu dính markdown ```json
            cleaned = res.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except:
            return None
    return None