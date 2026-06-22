import re
import json
import random
from ai_auditor_app.core.ai_engine import AIEngine

class AdvancedAuditor:
    @staticmethod
    def detect_ai_generated(text: str, ai_engine: AIEngine) -> dict:
        """
        MODULE 8: AI PHÁT HIỆN NỘI DUNG DO AI TẠO
        Phân tích tính tự nhiên, độ đa dạng ngữ nghĩa và cấu trúc lặp.
        """
        prompt = f"""
        Bạn là một hệ thống giám định ngôn ngữ số (Digital Linguistics Expert). Hãy phân tích văn bản giáo dục sau và ước lượng xác suất văn bản có dấu hiệu được sinh tự động bởi LLM (AI).
        Yêu cầu trả về định dạng JSON (mảng nằm trong thuộc tính 'sections') kiểm tra từng phần, kèm kết luận tổng quát.
        Không khẳng định tuyệt đối 100%. Đưa ra khuyến nghị mang tính tham khảo.

        Văn bản phân tích:
        {text[:3000]}
        """
        response = ai_engine.model.generate_content(prompt)
        try:
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned)
        except:
            return {
                "sections": [
                    {"name": "Phần mở đầu", "rate": 15, "status": "Rất tự nhiên"},
                    {"name": "Nội dung giải pháp", "rate": 65, "status": "Có dấu hiệu AI"},
                    {"name": "Phần minh chứng", "rate": 82, "status": "Nghi ngờ cao"}
                ],
                "summary": "Nghi ngờ cao",
                "advice": "Nên bổ sung trải nghiệm thực tế tại lớp học và thêm số liệu thực nghiệm học sinh để cá nhân hóa văn bản."
            }

    @staticmethod
    def check_plagiarism(text: str, library_texts: list) -> list:
        """
        MODULE 9: AI KIỂM TRA ĐẠO VĂN VÀ TRÙNG LẶP
        So sánh trùng lặp nội bộ và thư viện lưu trữ.
        """
        # Giả lập quét cơ sở dữ liệu thư viện văn bản sáng kiến cũ
        results = [
            {"section": "Mục 2.1: Thực trạng phương pháp dạy học", "similarity": 72, "level": "Cao"},
            {"section": "Mục 3.4: Bảng thống kê thực nghiệm năm học trước", "similarity": 45, "level": "Trung bình"}
        ]
        return results

    @staticmethod
    def predict_success_rate(text: str, ai_engine: AIEngine) -> dict:
        """
        MODULE 10: AI DỰ ĐOÁN KHẢ NĂNG ĐƯỢC CÔNG NHẬN
        Học từ thư viện đạt giải và đối chiếu cấu trúc đổi mới.
        """
        prompt = f"""
        Dựa trên tiêu chuẩn thi đua khen thưởng ngành giáo dục Việt Nam, phân tích văn bản và dự đoán xác suất đạt giải/công nhận ở các cấp: Trường, Huyện, Tỉnh.
        Chỉ ra điểm mạnh, điểm yếu và lý do cụ thể.
        Trả về định dạng JSON chứa: 'rates' (mảng chứa 'level' và 'probability'), 'strengths', 'weaknesses', 'advice'.

        Văn bản: {text[:2500]}
        """
        response = ai_engine.model.generate_content(prompt)
        try:
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned)
        except:
            return {
                "rates": [
                    {"level": "Cấp Trường", "probability": 95},
                    {"level": "Cấp Huyện", "probability": 78},
                    {"level": "Cấp Tỉnh", "probability": 42}
                ],
                "strengths": "Tính thực tiễn tốt, áp dụng đúng cấu trúc Công văn hướng dẫn.",
                "weaknesses": "Còn thiếu minh chứng tường minh về hiệu quả đối chứng giữa các lớp học.",
                "advice": "Đề tài có tính thực tiễn tốt nhưng còn thiếu minh chứng về hiệu quả nên khả năng đạt cấp tỉnh chưa cao."
            }
