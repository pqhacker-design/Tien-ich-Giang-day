import os
import json
import re
from google import genai
from google.genai import types

class AIEngine:
    def __init__(self):
        # Lấy API Key từ biến môi trường hoặc Streamlit secrets
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def analyze_and_generate_code(self, prompt: str, mode: str) -> dict:
        """
        Phân tích đề bài và trả về code Matplotlib để vẽ hình.
        mode: 'geometry' (Hình học) hoặc 'function' (Đồ thị hàm số)
        """
        if not self.client:
            return {
                "error": "Chưa cấu hình GEMINI_API_KEY. Vui lòng nhập API key ở thanh bên.",
                "code": ""
            }

        system_instruction = """
        Bạn là một chuyên gia toán học và lập trình Python xuất sắc. Nhiệm vụ của bạn là chuyển đổi đề bài toán bằng tiếng Việt thành đoạn mã Python (sử dụng matplotlib, numpy, sympy) để vẽ hình chính xác.
        
        YÊU CẦU CHUNG:
        1. Chỉ trả về ĐOẠN MÃ PYTHON nằm trong khối ```python ... ```. Không giải thích dông dài.
        2. Mã phải tạo ra một đối tượng `fig, ax = plt.subplots()` và kết thúc KHÔNG chứa `plt.show()`. Chỉ cần vẽ lên `ax`.
        3. Tự động tính toán tọa độ hợp lý (ví dụ tam giác vuông, đường tròn, đồ thị). Nếu thiếu dữ kiện tọa độ, hãy tự giả định các điểm hợp lý sao cho hình đẹp và đúng tính chất hình học (ví dụ: A vuông thì A=(0,3), B=(0,0), C=(4,0)).
        4. Luôn thêm nhãn (label) cho các điểm, ẩn trục tọa độ đối với hình học thuần túy (THCS), giữ lại trục tọa độ cho hình học giải tích và đồ thị hàm số.
        5. Đảm bảo dùng font chữ có hỗ trợ hiển thị tốt (như Arial hoặc font mặc định nhưng tránh lỗi tiếng Việt nếu ghi chú).
        """

        if mode == 'geometry':
            user_prompt = f"Hãy tạo mã Python vẽ hình học cho đề bài sau: '{prompt}'. Hãy tính toán tọa độ các điểm thật chính xác bằng SymPy hoặc hình học vector trước khi vẽ bằng Matplotlib."
        else:
            user_prompt = f"Hãy tạo mã Python vẽ đồ thị hàm số cho đề bài sau: '{prompt}'. Xác định khoảng x phù hợp, vẽ đồ thị, thêm lưới (grid), xác định cực trị hoặc giao điểm nếu đề bài yêu cầu và đánh dấu chúng bằng điểm chấm."

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )
            
            # Trích xuất code block từ phản hồi
            match = re.search(r"```python\s+(.*?)\s+```", response.text, re.DOTALL)
            if match:
                generated_code = match.group(1)
                return {"error": None, "code": generated_code}
            else:
                return {"error": "Không thể trích xuất mã Python từ AI.", "code": response.text}
                
        except Exception as e:
            return {"error": f"Lỗi gọi Gemini API: {str(e)}", "code": ""}
