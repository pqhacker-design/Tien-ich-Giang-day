import google.generativeai as genai
import json
import streamlit as st
import re

def get_ai_response(prompt):
    api_key = st.session_state.get("gemini_api_key", "")
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
        match = re.search(r'\[.*\]', res, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return []

def classify_paragraphs_with_ai(paragraph_list):
    """
    Phân loại vai trò thể thức của từng đoạn văn bằng AI.
    Trả về danh sách nhãn tương ứng: QUOC_HIEU, MAIN_TITLE, HEADING_1, HEADING_2, BODY_TEXT, SIGNATURE
    """
    if not paragraph_list:
        return []
    
    numbered_paragraphs = [f"[{i}] {p}" for i, p in enumerate(paragraph_list)]
    prompt_text = "\n".join(numbered_paragraphs[:150]) # Phân tích 150 dòng đầu

    prompt = f"""
    Bạn là chuyên gia về thể thức văn bản hành chính Việt Nam (Nghị định 30/2020/NĐ-CP).
    Hãy phân loại vai trò của từng dòng văn bản dưới đây thành một trong các nhãn sau:
    - QUOC_HIEU: Quốc hiệu, tiêu ngữ (CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM...)
    - MAIN_TITLE: Tên loại văn bản / Tiêu đề chính lớn nhất (BÁO CÁO, QUYẾT ĐỊNH, BẢNG THUYẾT MINH..., Tên dự án/sự kiện)
    - HEADING_1: Đề mục lớn (1., 2., I., II., TỔNG QUAN, PHÂN TÍCH, KẾT LUẬN, SỰ KIỆN...)
    - HEADING_2: Đề mục nhỏ hơn (a), b), Ý nghĩa:, Tông màu:, Phông chữ...)
    - BODY_TEXT: Đoạn văn nội dung thông thường
    - SIGNATURE: Nơi nhận, Chức danh, Chữ ký cuối văn bản

    Yêu cầu trả về JSON duy nhất là 1 danh sách chuỗi nhãn tương ứng đúng thứ tự [0], [1], [2]...
    Ví dụ: ["MAIN_TITLE", "HEADING_1", "BODY_TEXT", "HEADING_2", "BODY_TEXT"]

    Danh sách dòng:
    {prompt_text}
    """
    
    res = get_ai_response(prompt)
    try:
        match = re.search(r'\[.*\]', res, re.DOTALL)
        if match:
            labels = json.loads(match.group())
            while len(labels) < len(paragraph_list):
                labels.append("BODY_TEXT")
            return labels
    except Exception:
        pass
        
    return ["BODY_TEXT"] * len(paragraph_list)

def analyze_document_with_ai(full_text, filename):
    prompt = f"""
    Bạn là Chuyên gia Đánh giá Hồ sơ Giáo dục & Thể thức Văn bản Hành chính (NĐ 30/2020/NĐ-CP).
    Hãy đọc và phân tích toàn bộ văn bản sau đây:
    Tên file: {filename}
    Nội dung văn bản:
    {full_text[:4000]}

    Yêu cầu xuất kết quả theo đúng định dạng JSON chuẩn như sau (không kèm văn bản dẫn dắt):
    {{
       "loai_ho_so": "Loại hồ sơ nhận diện",
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
            match = re.search(r'\{.*\}', res, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
    return {}
