import os
import time
import json
import re
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted

class AIEngine:
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.5-flash"):
        # Sử dụng API Key truyền vào hoặc lấy từ biến môi trường hệ thống
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        # Khởi tạo client theo SDK google-genai mới
        self.client = genai.Client(api_key=self.api_key)

    def _generate_with_retry(self, prompt: str, is_json: bool = False) -> str:
        """Hàm nội bộ bọc lỗi Quota Exceeded và tự động sleep thử lại"""
        config = types.GenerateContentConfig()
        if is_json:
            config.response_mime_type = "application/json"

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                return response.text
            except ResourceExhausted:
                if attempt < 2:
                    # Lần 1 lỗi đợi 6 giây, lần 2 lỗi đợi 12 giây để hồi hạn mức (Quota RPM)
                    time.sleep(6 * (attempt + 1))
                    continue
                else:
                    # Nếu thử lại cả 3 lần vẫn nghẽn, trả về chuỗi thông báo lỗi định dạng cụ thể
                    return "LỖI_QUOTA: API Key của bạn hiện tại đã cạn kiệt hạn mức miễn phí trong phút này. Vui lòng đợi 1 phút rồi nhấn thử lại."
            except Exception as e:
                return f"LỖI_HỆ_THỐNG: {str(e)}"
        return "LỖI_HỆ_THỐNG: Không thể kết nối tới Google Gemini API."

    def extract_template_requirements(self, text: str):
        """Phân tích văn bản quy chuẩn và trích xuất danh sách tiêu chí dưới dạng danh sách JSON"""
        prompt = f"""
        Bạn là Chuyên gia Khảo thí và Kiểm định Giáo dục. Hãy phân tích văn bản quy chuẩn/hướng dẫn sau và trích xuất ra các tiêu chí cốt lõi cần phải có.
        Yêu cầu trả về cấu trúc mảng JSON các chuỗi ký tự tiêu chí ngắn gọn (ví dụ: ["Tiêu chí 1", "Tiêu chí 2"]).

        Văn bản mẫu:
        {text[:4000]}
        """
        raw_response = self._generate_with_retry(prompt, is_json=True)
        
        # Nếu gặp mã lỗi Quota hoặc Lỗi hệ thống, chuyển tiếp thông tin ra ngoài hiển thị
        if "LỖI_QUOTA" in raw_response or "LỖI_HỆ_THỐNG" in raw_response:
            return [raw_response]
            
        try:
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", raw_response).strip()
            return json.loads(cleaned)
        except:
            return ["Không thể phân tích dữ liệu JSON cấu trúc mẫu. Vui lòng thử lại."]

    def audit_document(self, template_reqs, user_text: str, audit_level: str) -> dict:
        """Rà soát đối chiếu hồ sơ người dùng với tập tiêu chí chuẩn"""
        prompt = f"""
        Dựa trên danh sách tiêu chí chuẩn: {json.dumps(template_reqs, ensure_ascii=False)}
        Hãy rà soát văn bản sau theo cấp độ '{audit_level}'.
        Yêu cầu trả về một đối tượng JSON chứa thuộc tính 'report' là một mảng các đối tượng gồm:
        'criteria' (tên tiêu chí), 'status' (Đạt/Chưa đạt/Cần chỉnh sửa), 'score' (thang điểm 100), 'fix' (hướng dẫn sửa chi tiết).

        Văn bản cần kiểm tra:
        {user_text[:3000]}
        """
        raw_response = self._generate_with_retry(prompt, is_json=True)
        
        if "LỖI_QUOTA" in raw_response or "LỖI_HỆ_THỐNG" in raw_response:
            return {"report": [{"criteria": "Lỗi kết nối API", "status": "Thất bại", "score": 0, "fix": raw_response}]}
            
        try:
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", raw_response).strip()
            return json.loads(cleaned)
        except:
            return {"report": []}
