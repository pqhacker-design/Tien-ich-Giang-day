import json
import os
from google import genai
from google.genai import types
from google.genai.errors import APIError

class GeminiService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key không được để trống.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def analyze_and_integrate(self, doc_text: str, cap_hoc: str) -> dict:
        prompt = f"""
Bạn là chuyên gia giáo dục và chuyển đổi số trong giáo dục phổ thông Việt Nam (Chương trình GDPT 2018).
Hãy phân tích nội dung giáo án dưới đây và xác định các vị trí thích hợp (Mục tiêu bài học, các Hoạt động dạy học) để tích hợp năng lực số.

Yêu cầu nghiêm ngặt:
1. Tìm ra chính xác cụm từ hoặc tiêu đề có sẵn trong giáo án gốc (ví dụ: "1. Về năng lực", "Hoạt động 1:", "b) Nội dung:", v.v.) để làm điểm neo (anchor_text).
2. Thiết kế nội dung năng lực số (khả thi với trường học Việt Nam) để chèn ngay phía sau hoặc phía dưới điểm neo đó.
3. Trả về kết quả CHỈ ở định dạng JSON theo cấu trúc mẫu sau:

{{
    "sua_doi": [
        {{
            "anchor_text": "Cụm từ gốc chính xác có trong giáo án để tìm kiếm",
            "insert_content": "Nội dung năng lực số bổ sung bằng tiếng Việt, viết ngắn gọn, thực tế."
        }},
        {{
            "anchor_text": "Cụm từ gốc thứ hai...",
            "insert_content": "Nội dung năng lực số bổ sung tiếp theo..."
        }}
    ]
}}

Nội dung giáo án gốc cần phân tích:
----------------------------------
{doc_text}
----------------------------------
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            
            result_json = json.loads(response.text)
            return result_json
            
        except APIError as ae:
            raise RuntimeError(f"Lỗi kết nối từ Gemini API: {str(ae)}")
        except json.JSONDecodeError:
            raise RuntimeError("Gemini phản hồi sai định dạng cấu trúc JSON yêu cầu.")
        except Exception as e:
            raise RuntimeError(f"Đã xảy ra lỗi không xác định khi gọi AI: {str(e)}")