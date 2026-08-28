import json
from google import genai
from google.genai import types
from google.genai.errors import APIError

class GeminiService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key không được để trống.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-3.6-flash"

    def analyze_and_integrate(self, doc_text: str, cap_hoc: str, integration_type: str) -> dict:
        """
        integration_type: 'Năng lực số', 'Năng lực AI', 'Cả hai'
        """
        # Xây dựng phần hướng dẫn dựa trên loại tích hợp
        if integration_type == "Năng lực số":
            focus_instruction = """
- Chỉ tập trung tích hợp Năng lực số theo Chương trình GDPT 2018.
- Nội dung cần nhấn mạnh kỹ năng sử dụng công nghệ thông tin, xử lý dữ liệu, an toàn số, giao tiếp trực tuyến,...
"""
        elif integration_type == "Năng lực AI":
            focus_instruction = """
- Chỉ tập trung tích hợp Năng lực AI theo Quyết định số 2422/QĐ-BGDĐT.
- Khung năng lực AI bao gồm: 
  - Nhận thức về AI (hiểu khái niệm, nguyên lý cơ bản).
  - Ứng dụng AI (sử dụng công cụ AI vào học tập, giải quyết vấn đề).
  - Tư duy phản biện về AI (đánh giá độ tin cậy, tác động xã hội, đạo đức).
- Nội dung tích hợp cần cụ thể, sát với môn học và cấp học, khuyến khích học sinh trải nghiệm và suy ngẫm.
"""
        else:  # "Cả hai"
            focus_instruction = """
- Tích hợp đồng thời cả Năng lực số (CT GDPT 2018) và Năng lực AI (QĐ 2422/QĐ-BGDĐT).
- Mỗi vị trí tích hợp có thể chỉ tập trung một loại hoặc kết hợp cả hai, nhưng cần rõ ràng loại nào.
- Nếu kết hợp, nội dung cần thể hiện cả hai khía cạnh (ví dụ: sử dụng công cụ AI để phân tích dữ liệu, vừa là kỹ năng số vừa là ứng dụng AI).
- Trong kết quả JSON, mỗi mục cần có trường "loai": "Năng lực số" hoặc "Năng lực AI" để phân biệt.
"""

        prompt = f"""
Bạn là chuyên gia giáo dục và chuyển đổi số trong giáo dục phổ thông Việt Nam.
Hãy phân tích nội dung giáo án dưới đây và xác định các vị trí thích hợp (Mục tiêu bài học, các Hoạt động dạy học) để tích hợp năng lực theo yêu cầu.

{focus_instruction}

Yêu cầu nghiêm ngặt:
1. Tìm ra chính xác cụm từ hoặc tiêu đề có sẵn trong giáo án gốc (ví dụ: "1. Về năng lực", "Hoạt động 1:", "b) Nội dung:", v.v.) để làm điểm neo (anchor_text).
2. Thiết kế nội dung tích hợp (khả thi với trường học Việt Nam) để chèn ngay phía sau hoặc phía dưới điểm neo đó. Nội dung phải ngắn gọn, rõ ràng, sát với môn học và cấp học.
3. Trả về kết quả CHỈ ở định dạng JSON theo cấu trúc mẫu sau:
{{
    "sua_doi": [
        {{
            "anchor_text": "Cụm từ gốc chính xác có trong giáo án để tìm kiếm",
            "insert_content": "Nội dung tích hợp bổ sung bằng tiếng Việt, viết ngắn gọn, thực tế.",
            "loai": "Năng lực số"  // hoặc "Năng lực AI" (nếu integration_type là 'Cả hai' thì cần ghi rõ loại)
        }},
        ...
    ]
}}
Lưu ý: Nếu integration_type = 'Cả hai', mỗi mục phải có trường "loai" để phân biệt.
Nếu chỉ một loại, có thể bỏ qua trường "loai" hoặc ghi mặc định.

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
            # Đảm bảo mỗi mục có trường 'loai' nếu cần
            if integration_type != "Cả hai":
                default_loai = "Năng lực số" if integration_type == "Năng lực số" else "Năng lực AI"
                for item in result_json.get('sua_doi', []):
                    if 'loai' not in item:
                        item['loai'] = default_loai
            return result_json
        except APIError as ae:
            raise RuntimeError(f"Lỗi kết nối từ Gemini API: {str(ae)}")
        except json.JSONDecodeError:
            raise RuntimeError("Gemini phản hồi sai định dạng cấu trúc JSON yêu cầu.")
        except Exception as e:
            raise RuntimeError(f"Đã xảy ra lỗi không xác định khi gọi AI: {str(e)}")
