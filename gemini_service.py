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
        """Đặc tả tiêu chuẩn Năng lực số Thông tư 02/2025/TT-BGDĐT theo cấp học."""
        base_framework = """
* Khung Năng lực số (TT 02/2025/TT-BGDĐT) gồm 6 miền năng lực chính:
  1. Vận hành thiết bị và phần mềm (Quản lý dữ liệu, cài đặt, sử dụng thiết bị số).
  2. Khai thác thông tin và dữ liệu (Tìm kiếm, chọn lọc, đánh giá tính chính xác của dữ liệu số).
  3. Giao tiếp và hợp tác trong môi trường số (Chia sẻ dữ liệu, tương tác trực tuyến có văn hóa).
  4. Sáng tạo nội dung số (Tạo mới, chỉnh sửa nội dung đa phương tiện, bản quyền số).
  5. An toàn và an ninh số (Bảo vệ thông tin cá nhân, thiết bị, sức khỏe thể chất/tâm lý trên môi trường số).
  6. Giải quyết vấn đề trong môi trường số (Khắc phục sự cố kỹ thuật, ứng dụng công nghệ để giải quyết bài toán thực tế).
"""
        level_guide = {
            "Tiểu học": """
- Mục tiêu trình độ TIỂU HỌC:
  + Làm quen, nhận biết và thực hiện các thao tác đơn giản với thiết bị số (chuột, bàn phím, gõ chữ, vẽ hình).
  + Tìm kiếm thông tin đơn giản dưới sự định hướng của giáo viên.
  + Hình thành thói quen bảo vệ mắt, tư thế ngồi, không tự ý chia sẻ thông tin riêng tư và biết nhờ người lớn giúp đỡ khi gặp sự cố trên mạng.
""",
            "THCS": """
- Mục tiêu trình độ THCS:
  + Sử dụng thành thạo các ứng dụng học tập, phần mềm mô phỏng, bảng tính/xử lý văn bản.
  + Đánh giá, chọn lọc độ tin cậy của thông tin từ nhiều nguồn trực tuyến.
  + Làm việc nhóm, chia sẻ tài liệu trực tuyến an toàn, tôn trọng quy tắc ứng xử trên mạng và bản quyền tác giả.
  + Phát hiện và xử lý được các sự cố kỹ thuật thông thường khi sử dụng thiết bị.
""",
            "THPT": """
- Mục tiêu trình độ THPT:
  + Tự chủ trong việc lựa chọn công cụ/ứng dụng số để nghiên cứu, phân tích dữ liệu phức tạp.
  + Sáng tạo nội dung số nâng cao (video, infographic, mô hình trực quan, bài thuyết trình tương tác).
  + Tuân thủ chặt chẽ pháp luật số, an toàn thông tin, bảo vệ danh tính số và dữ liệu cá nhân.
  + Ứng dụng tư duy máy tính, tối ưu hóa quy trình học tập và giải quyết các bài toán thực tiễn.
""",
            "Tự động nhận diện": """
- Hãy tự động phân tích cấp học từ nội dung/tiêu đề giáo án (Lớp 1-5: Tiểu học, Lớp 6-9: THCS, Lớp 10-12: THPT) và áp dụng chuẩn mức độ phù hợp tương ứng:
  + Tiểu học: Thao tác trực quan đơn giản, nhận thức an toàn bước đầu.
  + THCS: Kỹ năng ứng dụng công cụ, đánh giá thông tin, làm việc nhóm trực tuyến.
  + THPT: Tự chủ, phân tích chuyên sâu, sáng tạo nội dung đa phương tiện và xử lý sự cố.
"""
        }
        
        return base_framework + level_guide.get(cap_hoc, level_guide["Tự động nhận diện"])

    def analyze_and_integrate(self, doc_text: str, cap_hoc: str, integration_type: str) -> dict:
        tt02_info = self._get_tt02_framework_prompt(cap_hoc)

        if integration_type == "Năng lực số":
            focus_instruction = f"""
- Tích hợp chuẩn **Năng lực số theo Thông tư số 02/2025/TT-BGDĐT**:
{tt02_info}
- Yêu cầu: Chọn lọc 1-2 miền năng lực sát nhất với nội dung bài học. Đảm bảo hành động của học sinh vừa sức theo cấp học đã chọn.
"""
        elif integration_type == "Năng lực AI":
            focus_instruction = """
- Chỉ tập trung tích hợp **Năng lực AI theo Quyết định số 2422/QĐ-BGDĐT**:
  - Nhận thức về AI (hiểu khái niệm, nguyên lý cơ bản, hạn chế của AI).
  - Ứng dụng AI (sử dụng công cụ AI như chatbot, nhận diện ảnh/giọng nói vào học tập).
  - Tư duy phản biện & Đạo đức AI (đánh giá độ tin cậy, phát hiện ảo giác/thiên kiến, trách nhiệm khi dùng AI).
- Nội dung tích hợp cần cụ thể, phù hợp với năng lực nhận thức của học sinh.
"""
        else:  # "Cả hai"
            focus_instruction = f"""
- Tích hợp đồng thời cả **Năng lực số (TT 02/2025/TT-BGDĐT)** và **Năng lực AI (QĐ 2422/QĐ-BGDĐT)**:
{tt02_info}
- Năng lực AI: Nhận thức AI, ứng dụng AI trong học tập, tư duy phản biện và đạo đức AI.
- Đảm bảo phân định rõ từng loại bằng trường "loai": "Năng lực số" hoặc "Năng lực AI".
"""

        prompt = f"""
Bạn là chuyên gia giáo dục và chuyển đổi số trong giáo dục phổ thông Việt Nam.
Hãy phân tích nội dung Kế hoạch bài dạy (KHBD) dưới đây và xác định các vị trí phù hợp để bổ sung yêu cầu cần đạt về năng lực (tại mục Mục tiêu) và các hoạt động trải nghiệm số/AI (tại các bước Hoạt động dạy học).

Cấp học chỉ định: {cap_hoc}

{focus_instruction}

Yêu cầu thực hiện:
1. Tìm chính xác cụm từ hoặc tiêu đề có sẵn trong giáo án gốc (ví dụ: "b) Về năng lực:", "Hoạt động 2: Hình thành kiến thức", "c) Sản phẩm:", "d) Tổ chức thực hiện:", v.v.) làm điểm neo (`anchor_text`).
2. Viết nội dung bổ sung (`insert_content`) ngắn gọn, thiết thực, diễn đạt theo chuẩn thuật ngữ sư phạm của Bộ GD&ĐT (bắt đầu bằng động từ hành động của HS: nhận biết, sử dụng, tra cứu, thiết kế, phân tích...).
3. Phản hồi CHỈ định dạng JSON theo mẫu sau:
{{
    "sua_doi": [
        {{
            "anchor_text": "Cụm từ gốc chính xác có trong giáo án",
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
                    temperature=0.25
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
            raise RuntimeError(f"Lỗi kết nối từ Gemini API: {str(ae)}")
        except json.JSONDecodeError:
            raise RuntimeError("Gemini phản hồi sai cấu trúc JSON.")
        except Exception as e:
            raise RuntimeError(f"Đã xảy ra lỗi không xác định khi gọi AI: {str(e)}")
