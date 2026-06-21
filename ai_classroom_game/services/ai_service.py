import google.generativeai as genai
from openai import OpenAI
import json

class AIService:
    def __init__(self, gemini_key=None, openai_key=None):
        self.gemini_key = gemini_key
        self.openai_key = openai_key

    def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        """Gọi API sinh nội dung với cơ chế Fallback: Thử Gemini trước -> Nếu lỗi chuyển sang OpenAI"""
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
            }}
          ]
        }}
        """
        return json.loads(self.generate_content(prompt, instruction))

    def generate_warmup_game(self, warmup_type, subject, grade, warmup_prompt):
        """Sinh kịch bản trò chơi khởi động kèm ma trận câu hỏi trắc nghiệm dưới dạng JSON để xuất Excel"""
        instruction = "Bạn là chuyên gia thiết kế trò chơi học đường và phương pháp sư phạm tích cực."
        prompt = f"""
        Thiết kế một trò chơi khởi động loại '{warmup_type}' cho môn {subject}, {grade}. 
        Yêu cầu bổ sung: {warmup_prompt}.
        
        Bạn PHẢI trả về định dạng JSON cấu trúc chính xác như sau (Không bọc trong ký tự markdown ```json):
        {{
          "kich_ban_chu": "Văn bản chi tiết về Luật chơi, Cách tính điểm, Hướng dẫn giáo viên dẫn dắt trò chơi...",
          "trac_nghiem": [
            {{
              "cau_hoi": "Câu hỏi trắc nghiệm số 1 liên quan đến phần khởi động này?",
              "options": ["Phương án A", "Phương án B", "Phương án C", "Phương án D"],
              "dap_an": "Phương án A",
              "giai_thich": "Giải thích ngắn gọn"
            }},
            {{
              "cau_hoi": "Câu hỏi trắc nghiệm số 2?",
              "options": ["A", "B", "C", "D"],
              "dap_an": "B",
              "giai_thich": "Giải thích"
            }}
          ]
        }}
        """
        return json.loads(self.generate_content(prompt, instruction))
