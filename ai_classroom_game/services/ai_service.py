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
        instruction = "Bạn là chuyên gia khảo thí ngôn ngữ và sư phạm. Hãy tạo bộ câu hỏi trắc nghiệm, đúng sai, điền khuyết cấu trúc chuẩn."
        prompt = f"""
        Hãy tạo bộ câu hỏi tương tác cho bài học: '{topic}' với nội dung: '{content}'. Mục tiêu: '{goals}'.
        Trả về định dạng JSON thuần túy theo cấu trúc mẫu sau (không chứa markdown ```json):
        {{
          "trac_nghiem": [
            {{"cau_hoi": "Nội dung câu hỏi?", "options": ["A", "B", "C", "D"], "dap_an": "A", "giai_thich": "Lý do"}}
          ],
          "dung_sai": [
            {{"cau_hoi": "Mệnh đề đúng hay sai?", "dap_an": true, "giai_thich": "Giải thích"}}
          ],
          "dien_khuyen": [
            {{"cau_hoi": "Học sinh điền vào chỗ trống [...]", "tu_can_dien": "từ khóa"}}
          ]
        }}
        """
        return json.loads(self.generate_content(prompt, instruction))
