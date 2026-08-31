import json
from pydantic import BaseModel, Field
from typing import List, Literal
from google import genai
from google.genai import types
from google.genai.errors import APIError

# Định nghĩa Schema cấu trúc dữ liệu trả về chuẩn mực
class SuaDoiItem(BaseModel):
    anchor_text: str = Field(description="Trích dẫn nguyên văn một câu hoặc đoạn ngắn có thật trong giáo án để làm điểm neo chèn.")
    insert_content: str = Field(description="Nội dung tích hợp ngắn gọn, chuẩn sư phạm, bắt đầu bằng hành động của HS.")
    loai: Literal["Năng lực số", "Năng lực AI"] = Field(description="Loại năng lực được tích hợp: 'Năng lực số' hoặc 'Năng lực AI'.")

class TichHopResult(BaseModel):
    sua_doi: List[SuaDoiItem]


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
            "Tiểu học": "\n- Tiểu học: Thao tác đơn giản, tìm kiếm cơ bản, ý thức bảo vệ mắt, tư thế và an toàn riêng tư.",
            "THCS": "\n- THCS: Sử dụng phần mềm học tập, đánh giá thông tin, làm việc nhóm trực tuyến an toàn, bản quyền.",
            "THPT": "\n- THPT: Xử lý và phân tích dữ liệu, tạo sản phẩm số, an toàn thông tin và giải quyết bài toán thực tế.",
            "Tự động nhận diện": "\n- Nhận diện cấp học của từng bài để đưa ra mức độ yêu cầu phù hợp."
        }
        return base_framework + level_guide.get(cap_hoc, level_guide["Tự động nhận diện"])

    def analyze_and_integrate(self, doc_text: str, cap_hoc: str, integration_type: str) -> dict:
        tt02_info = self._get_tt02_framework_prompt(cap_hoc)

        ai_framework_info = """
* Khung Năng lực AI (QĐ 2422/QĐ-BGDĐT):
  - Nhận thức về AI: Nhận diện công nghệ AI quanh ta, hiểu cách AI học từ dữ liệu.
  - Ứng dụng AI: Sử dụng AI để hỗ trợ tìm kiếm ý tưởng, tóm tắt bài đọc, dịch thuật, gợi ý giải bài tập, tạo hình ảnh minh họa.
  - Tư duy phản biện & Đạo đức AI: Nhận biết AI có thể sai (ảo giác), kiểm chứng lại nguồn tin, sử dụng AI có trách nhiệm, trung thực trong học tập.
"""

        if integration_type == "Năng lực số":
            focus_instruction = f"""
YÊU CẦU: CHỈ TÍCH HỢP NĂNG LỰC SỐ (TT 02/2025/TT-BGDĐT).
{tt02_info}
Trường 'loai' trong JSON TẤT CẢ phải là 'Năng lực số'.
"""
        elif integration_type == "Năng lực AI":
            focus_instruction = f"""
YÊU CẦU: CHỈ TÍCH HỢP NĂNG LỰC AI (QĐ 2422/QĐ-BGDĐT).
{ai_framework_info}
Trường 'loai' trong JSON TẤT CẢ phải là 'Năng lực AI'.
"""
        else:  # "Cả hai"
            focus_instruction = f"""
YÊU CẦU BẮT BUỘC KHI CHỌN 'CẢ HAI':
Bạn PHẢI tích hợp CẢ 2 NHÓM NĂNG LỰC trong bài học:
1. NĂNG LỰC SỐ (theo TT 02/2025/TT-BGDĐT):
{tt02_info}

2. NĂNG LỰC AI (theo QĐ 2422/QĐ-BGDĐT):
{ai_framework_info}

QUY TẮC PHÂN BỔ BẮT BUỘC:
- Danh sách `sua_doi` trả về PHẢI CÓ CẢ CÁC MỤC có `"loai": "Năng lực số"` VÀ CÁC MỤC có `"loai": "Năng lực AI"`. Tuyệt đối không được bỏ quên Năng lực AI.
- Ví dụ:
  + Ở mục Mục tiêu bài học: Đề xuất 1 mục Năng lực số và 1 mục Năng lực AI.
  + Ở các Hoạt động học: Tích hợp hoạt động dùng công cụ số (tra cứu/vẽ hình/bảng tính) cho Năng lực số, và hoạt động dùng AI (nhờ chatbot gợi ý ý tưởng, đối chiếu kết quả của AI, phản biện nội dung do AI tạo ra) cho Năng lực AI.
"""

        prompt = f"""
Bạn là chuyên gia giáo dục và chuyển đổi số trong giáo dục phổ thông Việt Nam.
Hãy phân tích tài liệu giáo án dưới đây và đề xuất các vị trí tích hợp.

{focus_instruction}

QUY TẮC QUAN TRỌNG VỀ anchor_text (Điểm neo để tìm vị trí):
1. `anchor_text` PHẢI trích dẫn NGUYÊN VĂN một câu/dòng chữ có thật trong tài liệu giáo án (Plain text, không thêm dấu `**` hay markdown).
2. Trích đoạn dài từ 5 - 15 từ đặc trưng cho bài học đó để thuật toán tìm kiếm chính xác vị trí.

Nội dung giáo án gốc cần tích hợp:
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
                    response_schema=TichHopResult,
                    temperature=0.3
                )
            )
            result_json = json.loads(response.text)
            return result_json
        except APIError as ae:
            raise RuntimeError(f"Lỗi kết nối Gemini API: {str(ae)}")
        except json.JSONDecodeError:
            raise RuntimeError("Gemini phản hồi sai cấu trúc JSON.")
        except Exception as e:
            raise RuntimeError(f"Đã xảy ra lỗi: {str(e)}")
