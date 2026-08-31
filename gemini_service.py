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
* Khung Năng lực số (TT 02/2025/TT-BGDĐT) gồm 6 miền:
  1. Vận hành thiết bị và phần mềm
  2. Khai thác thông tin và dữ liệu
  3. Giao tiếp và hợp tác trong môi trường số
  4. Sáng tạo nội dung số
  5. An toàn và an ninh số
  6. Giải quyết vấn đề trong môi trường số
"""
        level_guide = {
            "Tiểu học": "\n- Tiểu học: Thao tác đơn giản, tìm kiếm cơ bản, ý thức bảo vệ mắt, tư thế và an toàn riêng tư.",
            "THCS": "\n- THCS: Ứng dụng công cụ học tập, đánh giá thông tin, làm việc nhóm trực tuyến an toàn, tôn trọng bản quyền.",
            "THPT": "\n- THPT: Phân tích dữ liệu nâng cao, sáng tạo sản phẩm số đa phương tiện, tuân thủ pháp luật số và an ninh mạng.",
            "Tự động nhận diện": "\n- Tự động nhận diện lớp/cấp học trong từng bài để tích hợp mức độ chuẩn xác tương ứng."
        }
        return base_framework + level_guide.get(cap_hoc, level_guide["Tự động nhận diện"])

    def analyze_and_integrate(self, doc_text: str, cap_hoc: str, integration_type: str) -> dict:
        tt02_info = self._get_tt02_framework_prompt(cap_hoc)

        if integration_type == "Năng lực số":
            focus_instruction = f"- Tích hợp Năng lực số theo TT 02/2025/TT-BGDĐT:\n{tt02_info}"
        elif integration_type == "Năng lực AI":
            focus_instruction = "- Tích hợp Năng lực AI theo QĐ 2422/QĐ-BGDĐT: Nhận thức AI, ứng dụng AI trong học tập, tư duy phản biện và đạo đức AI."
        else:
            focus_instruction = f"- Tích hợp đồng thời cả Năng lực số (TT 02/2025/TT-BGDĐT) và Năng lực AI (QĐ 2422/QĐ-BGDĐT):\n{tt02_info}"

        prompt = f"""
Bạn là chuyên gia giáo dục và chuyển đổi số trong giáo dục phổ thông Việt Nam.
Hãy đọc toàn bộ tài liệu giáo án bên dưới. File có thể chứa MỘT hoặc NHIỀU BÀI DẠY/KẾ HOẠCH BÀI DẠY KHÁC NHAU.

Nhiệm vụ: Duyệt lần lượt từng bài dạy từ đầu đến cuối file và đề xuất vị trí tích hợp phù hợp cho TẤT CẢ CÁC BÀI có trong file.

{focus_instruction}

YÊU CẦU ĐẶC BIỆT VỀ ĐIỂM NEO (anchor_text):
1. Không được dùng các cụm từ quá ngắn hoặc chung chung như "b) Về năng lực" hay "Hoạt động 1" một mình, vì sẽ gây nhầm lẫn giữa các bài.
2. `anchor_text` phải trích dẫn NGUYÊN VĂN một câu hoặc đoạn văn cụ thể, đặc trưng của từng hoạt động/mục trong bài đó (đủ dài và độc nhất trong ngữ cảnh bài đó) để chương trình tìm kiếm chính xác vị trí của từng bài.
3. Thứ tự các mục trong JSON trả về phải đi theo thứ tự xuất hiện từ trên xuống dưới của tài liệu.

Cấu trúc JSON yêu cầu:
{{
    "sua_doi": [
        {{
            "anchor_text": "Câu văn/dòng tiêu đề chính xác và đặc trưng trong bài học",
            "insert_content": "Nội dung tích hợp bổ sung ngắn gọn, chuẩn sư phạm",
            "loai": "Năng lực số" // hoặc "Năng lực AI"
        }}
    ]
}}

Nội dung giáo án:
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
