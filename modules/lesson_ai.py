from google import genai
from google.genai import types
import json

def generate_lesson_plan_ai(api_key, raw_text, metadata, competency_framework):
    """Gọi Gemini API xử lý chuẩn hóa toàn bộ giáo án theo định dạng JSON song ngữ hoặc thuần Việt"""
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("Chưa cấu hình Gemini API Key hợp lệ.")

    client = genai.Client(api_key=api_key.strip())
    
    # Lấy tùy chọn ngôn ngữ từ cấu hình metadata
    lang_style = metadata.get("language_style", "Thuần Tiếng Việt")
    
    # Xây dựng chỉ thị ngôn ngữ động cho AI
    if "Song ngữ" in lang_style:
        language_instruction = (
            f"YÊU CẦU ĐẶC BIỆT VỀ NGÔN NGỮ: Người dùng yêu cầu xuất giáo án dưới dạng {lang_style}.\n"
            "Đối với TẤT CẢ các nội dung văn bản bên trong các mảng (array) hoặc chuỗi (string) như: 'ten_bai_hoc', 'muc_tieu', 'thiet_bi_day_hoc', và các tiến trình hoạt động,\n"
            "bạn PHẢI hiển thị dưới dạng song ngữ theo cấu trúc: [Nội dung Tiếng Việt] / [Bản dịch Tiếng nước ngoài tương ứng].\n"
            "Ví dụ: 'ten_bai_hoc': 'Phép cộng trong phạm vi 10 / Addition within 10'. Hãy đảm bảo thuật ngữ chuyên ngành sư phạm chính xác."
        )
    else:
        language_instruction = "YÊU CẦU NGÔN NGỮ: Toàn bộ giáo án viết bằng thuần Tiếng Việt chuẩn quy chuẩn sư phạm Việt Nam."

    system_prompt = (
        "Bạn là chuyên gia thiết kế bài dạy cao cấp theo CTGDPT 2018 và Công văn 5512 của Bộ Giáo dục Việt Nam.\\n"
        "Nhiệm vụ của bạn là phân tích dữ liệu giáo án thô và xuất ra một cấu trúc giáo án số hóa hoàn chỉnh.\\n"
        f"{language_instruction}\\n"
        "BẮT BUỘC trả về dữ liệu định dạng JSON nguyên bản, không chứa mã markdown ```json ở đầu hay cuối. "
        "Cấu trúc JSON phải tuân thủ chính xác các khóa sau đây:\\n"
        "{\\n"
        "  'thong_tin_chung': {'ten_bai_hoc': '', 'mon_hoc': '', 'lop': '', 'thoi_luong': ''},\\n"
        "  'muc_tieu': {'kien_thuc': [], 'nang_luc': [], 'pham_chat': []},\\n"
        "  'thiet_bi_day_hoc': [],\\n"
        "  'tien_trinh_day_hoc': [\\n"
        "    {\\n"
        "      'ten_hoat_dong': 'Ví dụ: Hoạt động 1: Xác định nhiệm vụ... ',\\n"
        "      'muc_tieu': '',\\n"
        "      'noi_dung': '',\\n"
        "      'san_pham': '',\\n"
        "      'to_chuc_thuc_hien': ''\\n"
        "    }\\n"
        "  ],\\n"
        "  'hoc_lieu_so': {'hoc_lieu_so': [], 'cong_cu_ai': []},\\n"
        "  'ma_tran_muc_tieu': [{'noi_dung': '', 'nhan_biet': '', 'thong_hieu': '', 'van_dung': '', 'van_dung_cao': ''}]\\n"
        "}"
    )
    
    user_content = f"""
    Dữ liệu giáo án đầu vào: {raw_text}
    Thông tin định danh cấu trúc: {json.dumps(metadata, ensure_ascii=False)}
    Khung năng lực số cần tích hợp tự nhiên vào các hoạt động: {json.dumps(competency_framework, ensure_ascii=False)}
    
    Hãy thiết kế chi tiết 4 hoạt động chính theo CV 5512, tích hợp khéo léo học liệu số và công cụ AI (như GeoGebra, Padlet, Kahoot,...).
    Nhớ tuân thủ đúng yêu cầu về phong cách ngôn ngữ: {lang_style}.
    """
    
    config = types.GenerateContentConfig(
        temperature=0.3,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        response_mime_type="application/json",
        system_instruction=system_prompt
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_content,
        config=config
    )
    
    try:
        clean_text = response.text.strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"error": f"Lỗi parse JSON kết quả từ AI: {str(e)}", "raw_response": response.text}
