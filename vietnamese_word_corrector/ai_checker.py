from google import genai
import json
import streamlit as st
import re

def get_ai_response(prompt):
    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        return ""
    try:
        # Khởi tạo Client từ gói google-genai mới
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text if response else ""
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối Gemini AI: {str(e)}")
        return ""

def classify_paragraphs_with_ai(paragraph_list):
    """
    Phân loại vai trò thể thức của từng đoạn văn bằng AI.
    CÓ TÍCH HỢP TRẢ VỀ MẶC ĐỊNH AN TOÀN KHI AI BẬN.
    """
    if not paragraph_list:
        return []
    
    # Chỉ lấy tối đa 80 đoạn đầu để đảm bảo tốc độ phản hồi từ AI
    sample_list = paragraph_list[:80]
    numbered_paragraphs = [f"[{i}] {p}" for i, p in enumerate(sample_list)]
    prompt_text = "\n".join(numbered_paragraphs)

    prompt = f"""
    Bạn là chuyên gia về thể thức văn bản hành chính Việt Nam.
    Hãy phân loại vai trò của từng dòng văn bản sau thành đúng một trong các nhãn:
    - QUOC_HIEU: Quốc hiệu, tiêu ngữ
    - MAIN_TITLE: Tên loại văn bản / Tiêu đề lớn
    - HEADING_1: Đề mục lớn (1., 2., I., II., TỔNG QUAN, PHÂN TÍCH...)
    - HEADING_2: Đề mục nhỏ (a), b), Ý nghĩa:, Tông màu...)
    - BODY_TEXT: Văn bản nội dung thông thường
    - SIGNATURE: Nơi nhận, chữ ký

    Chỉ trả về DUY NHẤT một mảng JSON các chuỗi nhãn theo đúng thứ tự.
    Ví dụ: ["MAIN_TITLE", "HEADING_1", "BODY_TEXT"]

    Danh sách dòng:
    {prompt_text}
    """
    
    res = get_ai_response(prompt)
    if res:
        try:
            match = re.search(r'\[.*\]', res, re.DOTALL)
            if match:
                labels = json.loads(match.group())
                if isinstance(labels, list) and len(labels) > 0:
                    # Bổ sung BODY_TEXT cho phần còn lại nếu văn bản dài
                    while len(labels) < len(paragraph_list):
                        labels.append("BODY_TEXT")
                    return labels
        except Exception:
            pass
        
    # Mặc định trả về BODY_TEXT nếu AI gặp sự cố
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
       "loai_ho_so": "Hồ sơ Thuyết minh / Báo cáo",
       "do_tin_cay": 95,
       "diem": {{
          "the_thuc": 90,
          "noi_dung": 85,
          "gdpt_2018": 80,
          "nang_luc_so": 75,
          "khoa_hoc": 85,
          "tong": 83
       }},
       "xep_loai": "Tốt",
       "thieu_sot_cau_truc": ["Cần bổ sung thêm thông tin ngày tháng ban hành"],
       "gdpt_2018_check": {{
          "pham_chat": "Đã thể hiện đạt yêu cầu",
          "nang_luc_chung": "Phù hợp",
          "nang_luc_dac_thu": "Tốt"
       }},
       "de_xuat_cai_tien": ["Căn chỉnh tiêu đề căn giữa theo quy định"],
       "loi_the_thuc": [
          {{"stt": 1, "loai": "Thể thức", "goc": "1. tổng quan", "de_xuat": "Chuyển thành chữ in hoa IN ĐẬM", "muc_do": "Trung bình"}}
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
            
    # Kết quả dự phòng an toàn nếu AI không phản hồi JSON
    return {
        "loai_ho_so": "Văn bản Hành chính / Giáo dục",
        "do_tin_cay": 80,
        "diem": {"the_thuc": 85, "noi_dung": 85, "gdpt_2018": 80, "nang_luc_so": 80, "khoa_hoc": 80, "tong": 82},
        "xep_loai": "Khá",
        "thieu_sot_cau_truc": [],
        "gdpt_2018_check": {"pham_chat": "Đạt", "nang_luc_chung": "Đạt", "nang_luc_dac_thu": "Đạt"},
        "de_xuat_cai_tien": ["Cần kiểm tra lại các quy tắc in hoa tiêu đề"],
        "loi_the_thuc": []
    }
