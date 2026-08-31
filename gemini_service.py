import json
from google import genai
from google.genai import types
from google.genai.errors import APIError

class GeminiService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key không được để trống.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"

    def _get_tt02_framework_prompt(self, cap_hoc: str) -> str:
        base_framework = """
* Khung Năng lực số (TT 02/2025/TT-BGDĐT):
  1. Vận hành thiết bị và phần mềm
  2. Khai thác thông tin và dữ liệu
  3. Giao tiếp và hợp tác trong môi trường số
  4. Sáng tạo nội dung số
  5. An toàn và an ninh số
  6. Giải quyết vấn đề trong môi trường số
"""
        level_guide = {
            "Tiểu học": "\n- Cấp Tiểu học: Thao tác thiết bị cơ bản, tìm kiếm đơn giản, ý thức bảo vệ tư thế, mắt và thông tin cá nhân.",
            "THCS": "\n- Cấp THCS: Khai thác phần mềm môn học, đánh giá thông tin, làm việc nhóm trực tuyến an toàn, tôn trọng bản quyền.",
            "THPT": "\n- Cấp THPT: Phân tích dữ liệu, sáng tạo sản phẩm số đa phương tiện, an toàn thông tin và giải quyết vấn đề thực tế.",
            "Tự động nhận diện": "\n- Tự nhận diện cấp học theo từng bài để tích hợp nội dung phù hợp với đối tượng học sinh."
        }
        return base_framework + level_guide.get(cap_hoc, level_guide["Tự động nhận diện"])

    def analyze_and_integrate(self, doc_text: str, cap_hoc: str, integration_type: str) -> dict:
        tt02_info = self._get_tt02_framework_prompt(cap_hoc)

        if integration_type == "Năng lực số":
            focus_instruction = f"- Tích hợp Năng lực số (TT 02/2025/TT-BGDĐT):\n{tt02_info}"
        elif integration_type == "Năng lực AI":
            focus_instruction = "- Tích hợp Năng lực AI (QĐ 2422/QĐ-BGDĐT): Nhận thức AI, ứng dụng AI trong học tập, tư duy phản biện và đạo đức AI."
        else:
            focus_instruction = f"- Tích hợp cả Năng lực số (TT 02/2025/TT-BGDĐT) và Năng lực AI (QĐ 2422/QĐ-BGDĐT):\n{tt02_info}"

        prompt = f"""
Bạn là chuyên gia giáo dục và chuyển đổi số trong giáo dục phổ thông Việt Nam.
Hãy đọc toàn bộ tài liệu giáo án bên dưới (có thể có nhiều bài dạy). Duyệt lần lượt từng bài dạy từ trên xuống dưới và đề xuất nội dung tích hợp.

{focus_instruction}

QUY TẮC BẮT BUỘC VỀ anchor_text (Điểm neo để tìm vị trí chèn):
1. `anchor_text` PHẢI là một câu hoặc dòng chữ CÓ THẬT trong văn bản gốc.
2. Sao chép NGUYÊN VĂN (Plain text), TUYỆT ĐỐI KHÔNG thêm dấu markdown như **, *, #, gạch đầu dòng tự chế.
3. Không chọn cụm từ quá ngắn (như "Mục tiêu" hay "Hoạt động 1"). Hãy chọn một câu dài khoảng 5 - 15 từ chứa ngữ cảnh của bài đó để không bị nhầm lẫn giữa các bài.

Cấu trúc phản hồi JSON:
{{
    "sua_doi": [
        {{
            "anchor_text": "Trích nguyên văn một dòng hoặc câu có thật trong giáo án",
            "insert_content": "Nội dung tích hợp bổ sung ngắn gọn",
            "loai": "Năng lực số"
        }}
    ]
}}

Nội dung giáo án gốc:
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
                    temperature=0.2
                )
            )
            result_json = json.loads(response.text)
            if integration_type != "Cả hai":
                default_loai = "Năng lực số" if integration_type == "Năng lực số" else "Năng lực AI"
                for item in result_json.get('sua_doi', []):
                    if 'loai' not in item:
                        item['loai'] = default_loai
            return result_json
        except APIError as ae:
            raise RuntimeError(f"Lỗi kết nối Gemini API: {str(ae)}")
        except json.JSONDecodeError:
            raise RuntimeError("Gemini phản hồi sai cấu trúc JSON.")
        except Exception as e:
            raise RuntimeError(f"Đã xảy ra lỗi: {str(e)}")
