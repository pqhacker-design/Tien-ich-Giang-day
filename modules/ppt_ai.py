from google import genai
from google.genai import types
import json

def generate_powerpoint_data_ai(api_key, raw_text, metadata, style_choice):
    """Gọi Gemini API để phân tách giáo án thô thành cấu trúc dữ liệu Slide JSON (dùng SDK google-genai mới)"""
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("Chưa cấu hình Gemini API Key hợp lệ.")

    client = genai.Client(api_key=api_key.strip())
    
    system_prompt = (
        "Bạn là chuyên gia thiết kế bài giảng điện tử và slide sư phạm tiên tiến.\n"
        "Hãy chuyển hóa giáo án được cung cấp thành cấu trúc các Slide PowerPoint logic, ngắn gọn.\n"
        "BẮT BUỘC trả về dữ liệu định dạng JSON nguyên bản, không chứa mã markdown ```json ở đầu hay cuối.\n"
        "Cấu trúc JSON phải tuân thủ chính xác định dạng mảng sau đây:\n"
        "{\n"
        "  'slides': [\n"
        "    {\n"
        "      'type': 'title', 'title': '', 'subtitle': '', 'teacher': '', 'school': '', 'notes': ''\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Lưu ý quan trọng: Trong nội dung hiển thị trên Slide, Tuyệt đối KHÔNG sử dụng ký hiệu toán học dạng mã LaTeX (như $...$ hoặc $$...$$). "
        "Hãy sử dụng các ký tự Unicode toán học thông thường (ví dụ: dùng ², ³, √, ±, ∈, →) "
        "để đảm bảo PowerPoint hiển thị được trực quan, không bị lỗi font."
    )
    
    user_content = f"""
    Dữ liệu giáo án hoặc nội dung đầu vào: {raw_text}
    Cấu hình lớp học: {json.dumps(metadata, ensure_ascii=False)}
    Phong cách thiết kế yêu cầu theo lứa tuổi: {style_choice}
    
    Yêu cầu thiết kế:
    1. Slide nội dung phải cực kỳ ngắn gọn (dạng bullet points), không sao chép nguyên văn cả đoạn dài của giáo án lên slide.
    2. Tự động đề xuất 'prompt_image' (Mô tả tiếng Anh/tiếng Việt để vẽ hình minh họa) phù hợp môn học.
    3. Tự tạo câu hỏi trắc nghiệm tương tác (quiz).
    4. Tích hợp năng lực số (Khai thác học liệu số, thảo luận trực tuyến) vào các slide hoạt động một cách tự nhiên.
    5. Phần 'notes' (Ghi chú giáo viên) phải ghi rõ mục tiêu slide, câu hỏi gợi mở và thời lượng dự kiến trình bày.
    """
    
    config = types.GenerateContentConfig(
        temperature=0.4,
        top_p=0.95,
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
