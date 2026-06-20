import google.generativeai as genai
from openai import OpenAI
import json

class AIService:
    def __init__(self, gemini_key=None, openai_key=None):
        self.gemini_key = gemini_key
        self.openai_key = openai_key

    def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        """Gọi API sinh nội dung với cơ chế Fallback: Thử Gemini trước -> Nếu lỗi chuyển sang OpenAI"""
        # Thử nghiệm với Gemini API
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    generation_config={"response_mime_type": "application/json"} if "json" in prompt.lower() else None,
                    system_instruction=system_instruction
                )
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                print(f"[Warning] Gemini API Error: {e}. Switching to Fallback OpenAI...")
        
        # Cơ chế Fallback sang OpenAI API
        if self.openai_key:
            try:
                client = OpenAI(api_key=self.openai_key)
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    response_format={"type": "json_object"} if "json" in prompt.lower() else None
                )
                return response.choices[0].message.content
            except Exception as e:
                raise RuntimeError(f"[Critical Error] Cả hai cổng dịch vụ AI (Gemini & OpenAI) đều thất bại: {e}")
        
        raise ValueError("Chưa thiết lập cấu hình API Key hợp lệ trong hệ thống.")

    def generate_quiz(self, topic, content, goals):
        instruction = "Bạn là chuyên gia khảo thí ngôn ngữ và sư phạm. Hãy tạo bộ câu hỏi trắc nghiệm và ma trận ô chữ từ khóa dựa trên nội dung bài học."
        
        # CHÚ Ý: Mẹo sử dụng dấu ngoặc nhọn đôi {{ }} trong f-string của Python để không bị lẫn với cú pháp biến
        prompt = f"""
        Hãy tạo bộ câu hỏi tương tác và ô chữ cho bài học: '{topic}' với nội dung: '{content}'. Mục tiêu: '{goals}'.
        
        YÊU CẦU RIÊNG CHO Ô CHỮ:
        - Chọn ra từ 4 đến 6 từ khóa cốt lõi xuất hiện trong bài học.
        - Viết hoa toàn bộ từ khóa, KHÔNG CHỨA DẤU TIẾNG VIỆT, KHÔNG CÓ KHOẢNG TRẮNG (Ví dụ: "PITAGO", "DIENTICH", "LUYENTAP").
        - Tạo câu hỏi gợi ý ngắn gọn, rõ ràng cho từng từ khóa đó.

        Trả về định dạng JSON thuần túy theo cấu trúc mẫu sau (không chứa markdown ```json):
        {{
          "trac_nghiem": [
            {{
              "cau_hoi": "Nội dung câu hỏi?",
              "options": ["A", "B", "C", "D"],
              "dap_an": "A",
              "giai_thich": "Lý do"
            }}
          ],
          "o_chu": [
            {{
              "hang": 1,
              "tu_khoa": "TUKHOAONE",
              "goi_y": "Gợi ý cho từ khóa số 1"
            }},
            {{
              "hang": 2,
              "tu_khoa": "TUKHOATWO",
              "goi_y": "Gợi ý cho từ khóa số 2"
            }}
          ]
        }}
        """
        return json.loads(self.generate_content(prompt, instruction))
        """
        return json.loads(self.generate_content(prompt, instruction))
