import google.generativeai as genai
import json
import re

class AIEngine:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def extract_template_requirements(self, template_text: str) -> list:
        prompt = f"""
        Bạn là Chuyên gia Khảo thí và Đảm bảo Chất lượng Giáo dục của Bộ Giáo dục và Đào tạo Việt Nam.
        Hãy phân tích văn bản hướng dẫn/mẫu sau đây và trích xuất cấu trúc cấu thành bắt buộc cùng hệ thống tiêu chí.
        Trả về kết quả dưới dạng chuỗi JSON nguyên bản (Không nằm trong khối ký tự ```json), là một mảng các đối tượng chứa thuộc tính "criteria".

        Văn bản mẫu:
        {template_text}
        """
        response = self.model.generate_content(prompt)
        try:
            cleaned_text = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned_text)
        except:
            return [{"criteria": "Kiểm tra cấu trúc tổng thể"}, {"criteria": "Nội dung minh chứng số liệu"}]

    def audit_document(self, template_reqs: list, user_text: str, level: str) -> dict:
        prompt = f"""
        Thực hiện đối chiếu văn bản người dùng với danh sách tiêu chí mẫu sau đây. 
        Mức độ chuyên sâu yêu cầu: {level}.
        Yêu cầu nghiêm ngặt xuất ra định dạng JSON chuẩn (mảng đối tượng bên trong key "report"), mỗi đối tượng chứa:
        - "criteria": Tên tiêu chí đối chiếu
        - "status": Hiện trạng trong văn bản người dùng (Đầy đủ/Thiếu/Sơ sài)
        - "score": Điểm số (0-100)
        - "fix": Đề xuất câu chữ hoặc nội dung chỉnh sửa chi tiết bằng tiếng Việt hành chính giáo dục.

        Tiêu chí mẫu: {json.dumps(template_reqs, ensure_ascii=False)}
        Văn bản cần kiểm tra:
        {user_text}
        """
        response = self.model.generate_content(prompt)
        try:
            cleaned_text = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned_text)
        except:
            return {"report": [{"criteria": "Tổng thể", "status": "Cần xem lại", "score": 70, "fix": "Cần rà soát thủ công do lỗi cấu trúc dữ liệu."}]}
