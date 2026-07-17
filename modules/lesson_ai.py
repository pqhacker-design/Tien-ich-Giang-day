from google import genai
from google.genai import types
import json

def generate_lesson_plan_ai(api_key, raw_text, metadata, competency_framework):
    """Gọi Gemini API xử lý chuẩn hóa toàn bộ giáo án theo định dạng JSON chuyên sâu (dùng SDK google-genai mới)"""
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("Chưa cấu hình Gemini API Key hợp lệ.")

    client = genai.Client(api_key=api_key.strip())
    
    # Trích xuất mức độ/loại giáo án từ metadata phục vụ phân hóa sư phạm
    lesson_type = metadata.get("lesson_type", "Giáo án tiêu chuẩn")
    
    # Thiết lập chỉ thị sư phạm phân hóa động dựa trên mức độ giáo án đã chọn
    differentiation_instruction = ""
    if lesson_type == "Giáo án dành phụ đạo HS yếu":
        differentiation_instruction = (
            "- Mục tiêu kiến thức tập trung vào mức độ NHẬN BIẾT và THÔNG HIỂU cốt lõi, giảm tải các nội dung quá phức tạp.\n"
            "- Các câu hỏi, nhiệm vụ học tập chia nhỏ thành nhiều bước (scaffolding), có gợi ý rõ ràng và sử dụng nhiều học liệu trực quan.\n"
            "- Tiến trình tổ chức thực hiện cần tăng cường các hoạt động rèn luyện thực hành, sửa sai kịp thời và động viên học sinh."
        )
    elif lesson_type == "Giáo án dạy HS giỏi":
        differentiation_instruction = (
            "- Thiết kế mục tiêu kiến thức mở rộng, nâng cao, tăng cường tỉ lệ phân bổ cho mức độ VẬN DỤNG và VẬN DỤNG CAO.\n"
            "- Nội dung bài học và sản phẩm yêu cầu tính sáng tạo, lập luận đa chiều, hoặc giải quyết các bài toán/tình huống phức tạp.\n"
            "- Tổ chức thực hiện theo hướng tự học chuyên sâu, thảo luận nhóm phản biện, ứng dụng CNTT cao để nghiên cứu/phát triển sản phẩm."
        )
    else:  # Giáo án tiêu chuẩn
        differentiation_instruction = (
            "- Đảm bảo cấu trúc chuẩn, phân bổ đều đặn và hài hòa giữa các mức độ nhận thức từ Nhận biết, Thông hiểu đến Vận dụng.\n"
            "- Phù hợp với năng lực chung của đại đa số học sinh trong lớp học phổ thông đại trà."
        )

    system_prompt = (
        "Bạn là chuyên gia thiết kế bài dạy cao cấp theo CTGDPT 2018 và Công văn 5512 của Bộ Giáo dục Việt Nam.\n"
        "Nhiệm vụ của bạn là phân tích dữ liệu giáo án thô và xuất ra một cấu trúc giáo án số hóa hoàn chỉnh.\n"
        "BẮT BUỘC trả về dữ liệu định dạng JSON nguyên bản, không chứa mã markdown ```json ở đầu hay cuối. "
        "Cấu trúc JSON phải tuân thủ chính xác các khóa sau đây:\n"
        "{\n"
        "  'thong_tin_chung': {'ten_bai_hoc': '', 'mon_hoc': '', 'lop': '', 'thoi_luong': '', 'muc_do_giao_an': ''},\n"
        "  'muc_tieu': {'kien_thuc': [], 'nang_luc': [], 'pham_chat': []},\n"
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
    
    YÊU CẦU ĐẶC BIỆT VỀ PHÂN HÓA SƯ PHẠM:
    Bài dạy này yêu cầu thiết kế theo hình thức: **{lesson_type}**
    Hãy tuân thủ nghiêm ngặt định hướng chuyên môn sau đây khi biên soạn toàn bộ nội dung giáo án và ma trận mục tiêu:
    {differentiation_instruction}
    
    Hãy thiết kế chi tiết 4 hoạt động chính theo CV 5512, tích hợp khéo léo học liệu số và công cụ AI (như GeoGebra, Padlet, Kahoot,...).
    Lưu ý: Điền giá trị '{lesson_type}' vào khóa 'muc_do_giao_an' trong phần 'thong_tin_chung'.
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
        if clean_text.startswith("```json"):
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(clean_text)
    except Exception as e:
        raise ValueError(f"Lỗi phản hồi JSON từ Gemini API: {e}\nNội dung thô: {response.text}")
