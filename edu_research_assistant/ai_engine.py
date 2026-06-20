import google.generativeai as genai

def call_ai_stream(prompt, system_instruction="", api_key=None):
    """Xử lý gọi Gemini API sử dụng API Key linh hoạt truyền từ Session State"""
    if api_key and api_key.strip() != "":
        try:
            # Kích hoạt API bằng Key lấy từ Session State của Trang chủ
            genai.configure(api_key=api_key)
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Lỗi kết nối API: {str(e)}. Vui lòng kiểm tra lại tính hợp lệ của Key."
    else:
        return "[Chế độ Ngoại tuyến] Không tìm thấy API Key. Vui lòng cấu hình tại Trang chủ."

def get_council_critique(title, content, level="Cấp Tỉnh", api_key=None):
    """Đóng vai Hội đồng thẩm định đánh giá đề tài chuyên sâu"""
    system_prompt = f"""Bạn là Chủ tịch Hội đồng Thẩm định Sáng kiến kinh nghiệm và Đề tài Nghiên cứu Khoa học Sư phạm Ứng dụng {level} của Bộ Giáo dục và Đào tạo Việt Nam.
    Hãy phân tích, phản biện khắt khe và chấm điểm công tâm (thang điểm 100)..."""
    
    prompt = f"Tên đề tài: {title}\n\nNội dung chi tiết:\n{content}"
    return call_ai_stream(prompt, system_prompt, api_key=api_key)
