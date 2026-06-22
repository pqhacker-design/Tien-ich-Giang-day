import os
import re
from google import genai
from google.genai import types
from docx import Document
import io

class AIEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def read_docx(self, docx_bytes) -> str:
        """Trích xuất văn bản từ file Word"""
        doc = Document(io.BytesIO(docx_bytes))
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        return "\n".join(full_text)

    def analyze_and_generate_code(self, mode: str, user_request: str, uploaded_file=None) -> dict:
        """
        Phân tích đề bài từ Văn bản, Ảnh, PDF hoặc Word và sinh mã vẽ hình.
        """
        if not self.client:
            return {
                "error": "Chưa cấu hình GEMINI_API_KEY. Vui lòng nhập API key ở thanh bên.",
                "code": ""
            }

        system_instruction = """
        Bạn là một chuyên gia toán học và siêu lập trình viên Python. Nhiệm vụ của bạn là đọc đề bài toán (từ văn bản, hình ảnh, hoặc tài liệu đính kèm) và tạo ra đoạn mã Python để vẽ hình chính xác.
        
        YÊU CẦU QUAN TRỌNG:
        1. Chỉ trả về ĐOẠN MÃ PYTHON nằm trong khối ```python ... ```. Không giải thích thêm.
        2. Mã phải tạo đối tượng `fig, ax = plt.subplots()` và vẽ lên `ax`. KHÔNG CHỨA `plt.show()`.
        3. Tự động tính toán tọa độ hợp lý, chính xác bằng SymPy hoặc hình học vector. Nếu thiếu dữ kiện tọa độ cụ thể, tự giả định các tọa độ hợp lý sao cho hình đúng tính chất hình học và trực quan nhất.
        4. Luôn thêm nhãn (label) rõ ràng cho các điểm. Ẩn trục tọa độ (Oxy) đối với hình học thuần túy cấp 2 (THCS), giữ lại trục tọa độ cho hình học giải tích và đồ thị hàm số.
        """

        # Chuẩn bị nội dung gửi cho Gemini (Contents list)
        contents = []

        # Xử lý file đính kèm nếu có
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            file_name = uploaded_file.name.lower()

            if file_name.endswith(('.png', '.jpg', '.jpeg')):
                # Gửi ảnh trực tiếp cho Gemini
                contents.append(
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type="image/png" if file_name.endswith('.png') else "image/jpeg"
                    )
                )
            elif file_name.endswith('.pdf'):
                # Gửi file PDF trực tiếp cho Gemini (Gemini hỗ trợ đọc PDF)
                contents.append(
                    types.Part.from_bytes(
                        data=file_bytes,
                        mime_type="application/pdf"
                    )
                )
            elif file_name.endswith('.docx'):
                # Trích xuất text từ Word rồi gửi kèm dưới dạng văn bản
                docx_text = self.read_docx(file_bytes)
                contents.append(f"--- NỘI DUNG TÀI LIỆU WORD ĐÍNH KÈM ---\n{docx_text}\n--- HẾT TÀI LIỆU ---")

        # Thêm yêu cầu cụ thể của người dùng vào prompt
        base_prompt = f"Yêu cầu từ người dùng: {user_request}\n"
        if mode == 'geometry':
            base_prompt += "Hãy tìm bài toán hình học tương ứng trong tài liệu/hình ảnh trên, trích xuất dữ kiện, tính toán tọa độ chính xác và viết mã Python vẽ hình học."
        else:
            base_prompt += "Hãy tìm bài toán đồ thị/hàm số tương ứng trong tài liệu/hình ảnh trên, xác định công thức toán, khoảng x phù hợp và viết mã Python vẽ đồ thị."
        
        contents.append(base_prompt)

        try:
            # Sử dụng gemini-2.5-flash vì mô hình này xử lý Multimodal (Ảnh/PDF) cực kỳ nhanh và chuẩn xác
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )
            
            match = re.search(r"```python\s+(.*?)\s+```", response.text, re.DOTALL)
            if match:
                return {"error": None, "code": match.group(1)}
            else:
                return {"error": "AI đọc đề bài thành công nhưng không thể trích xuất ra mã Python hợp lệ.", "code": response.text}
                
        except Exception as e:
            return {"error": f"Lỗi xử lý AI: {str(e)}", "code": ""}
