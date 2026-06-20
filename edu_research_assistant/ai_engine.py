import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Cấu hình API chung kết nối hệ sinh thái phần mềm giáo dục của thầy
def get_ai_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return "gemini"
    return "offline"

def call_ai_stream(prompt, system_instruction=""):
    mode = get_ai_client()
    if mode == "gemini":
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi kết nối API: {str(e)}. Hệ thống tự động chuyển sang chế độ mẫu ngoại tuyến."
    else:
        return "[Chế độ Ngoại tuyến] Vui lòng cấu hình GEMINI_API_KEY để nhận nội dung phân tích chuyên sâu từ AI."

def get_council_critique(title, content, level="Cấp Tỉnh"):
    """Đóng vai Hội đồng thẩm định đánh giá đề tài chuyên sâu"""
    system_prompt = f"""Bạn là Chủ tịch Hội đồng Thẩm định Sáng kiến kinh nghiệm và Đề tài Nghiên cứu Khoa học Sư phạm Ứng dụng {level} của Bộ Giáo dục và Đào tạo Việt Nam.
    Hãy phân tích, phản biện khắt khe và chấm điểm công tâm (thang điểm 100) theo đúng các tiêu chí:
    1. Tính mới & Tính sáng tạo (30đ)
    2. Tính thực tiễn & Giải quyết được bài toán giáo dục cốt lõi (30đ)
    3. Tính khả thi & Khả năng nhân rộng tại các cơ sở giáo dục (30đ)
    4. Thể thức văn bản & Tính logic khoa học sư phạm (10đ)
    Yêu cầu cấu trúc phản hồi bằng Markdown rõ ràng, chỉ ra điểm nghẽn và đưa ra khuyến nghị sửa đổi cụ thể lý luận - thực tiễn."""
    
    prompt = f"Tên đề tài: {title}\n\nNội dung chi tiết:\n{content}"
    return call_ai_stream(prompt, system_prompt)
