import google.generativeai as genai
import json

def generate_lesson_plan_ai(api_key, raw_text, metadata, competency_framework):
    """Gọi Gemini API xử lý chuẩn hóa toàn bộ giáo án theo định dạng JSON chuyên sâu"""
    genai.configure(api_key=api_key)
    
    # Cấu hình tham số mô hình tối ưu cho sinh văn bản giáo dục cấu trúc
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json"
    }
    
    # Đã sửa lại chuẩn tên model có tiền tố models/
    model = genai.GenerativeModel(
        model_name="models/gemini-2.5-flash",
        generation_config=generation_config
    )
    
    system_prompt = (
        "Bạn là chuyên gia thiết kế bài dạy cao cấp theo CTGDPT 2018 và Công văn 5512 của Bộ Giáo dục Việt Nam.\n"
        "Nhiệm vụ của bạn là phân tích dữ liệu giáo án thô và xuất ra một cấu trúc giáo án số hóa hoàn chỉnh.\n"
        "BẮT BUỘC trả về dữ liệu định dạng JSON nguyên bản, không chứa mã markdown ```json ở đầu hay cuối. "
        "Cấu trúc JSON phải tuân thủ chính xác các khóa sau đây:\n"
        "{\n"
        "  'thong_tin_chung': {'mon_hoc': '', 'lop': '', 'cap_hoc': '', 'thoi_luong': '', 'ten_bai_hoc': ''},\n"
        "  'muc_tieu': {\n"
        "    'pham_chat': [],\n"
        "    'nang_luc_chung': [],\n"
        "    'nang_luc_dac_thu': []\n"
        "  },\n"
        "  'thiet_bi_day_hoc': [],\n"
        "  'tien_trinh_day_hoc': [\n"
        "    {\n"
        "      'ten_hoat_dong': 'Hoạt động 1: Khởi động...',\n"
        "      'muc_tieu': '',\n"
        "      'noi_dung': '',\n"
        "      'san_pham': '',\n"
        "      'to_chuc_thuc_hien': ''\n"
        "    }\n"
        "  ],\n"
        "  'chuyen_doi_so': {'hoc_lieu_so': [], 'cong_cu_ai': []},\n"
        "  'ma_tran_muc_tieu': [{'noi_dung': '', 'nhan_biet': '', 'thong_hieu': '', 'van_dung': '', 'van_dung_cao': ''}]\n"
        "}"
    )
    
    user_content = f"""
    Dữ liệu giáo án đầu vào: {raw_text}
    Thông tin định danh cấu trúc: {json.dumps(metadata, ensure_ascii=False)}
    Khung năng lực số cần tích hợp tự nhiên vào các hoạt động: {json.dumps(competency_framework, ensure_ascii=False)}
    
    Hãy thiết kế chi tiết 4 hoạt động chính theo CV 5512, tích hợp khéo léo học liệu số và công cụ AI (như GeoGebra, Quizizz, Canva, Gemini) phù hợp với cấp học.
    """
    
    response = model.generate_content([system_prompt, user_content])
    
    try:
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        return json.loads(clean_text.strip())
    except Exception as e:
        return {"error": f"Lỗi phân tích cú pháp AI: {str(e)}", "raw_response": response.text}
