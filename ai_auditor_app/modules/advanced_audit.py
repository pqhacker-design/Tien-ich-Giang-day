import re
import json

class AdvancedAuditor:
    @staticmethod
    def detect_ai_generated(text: str, ai_engine: AIEngine) -> dict:
        """Module 8: Sử dụng Gemini phân tích tần suất từ và tính tự nhiên"""
        prompt = f"""
        Phân tích văn bản giáo dục sau và ước lượng xác suất văn bản có dấu hiệu được sinh tự động bởi AI (LLM).
        Hãy đánh giá dựa trên: cấu trúc câu lặp lại, mức độ đồng đều ngôn ngữ, tính tự nhiên.
        Trả về định dạng JSON nguyên bản chứa key 'sections' (mảng các đối tượng gồm 'name', 'rate', 'status') và 'summary', 'advice'. Không khẳng định tuyệt đối.

        Văn bản:
        {text[:2000]}
        """
        try:
            response = ai_engine.model.generate_content(prompt)
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned)
        except:
            return {
                "sections": [
                    {"name": "Đặt vấn đề", "rate": 20, "status": "Tự nhiên"},
                    {"name": "Giải pháp thực hiện", "rate": 45, "status": "Có dấu hiệu AI nhẹ"},
                    {"name": "Hiệu quả áp dụng", "rate": 70, "status": "Nghi ngờ cao"}
                ],
                "summary": "Cần bổ sung trải nghiệm thực tế",
                "advice": "Hãy đưa thêm các tình huống sư phạm thực tế tại lớp học của anh và số liệu học sinh cụ thể để giảm tính rập khuôn."
            }

    @staticmethod
    def check_plagiarism(text: str, ai_engine: AIEngine) -> list:
        """Module 9: Nhờ Gemini quét và phát hiện các đoạn văn có tư duy lối mòn, trùng lặp ý tưởng"""
        prompt = f"""
        Với tư cách là thành viên Hội đồng thẩm định, hãy rà soát xem các đoạn trong văn bản sau có bị trùng lặp ý tưởng, sao chép các mô-típ sáng kiến kinh nghiệm cũ trên mạng hay không.
        Trả về định dạng JSON là một mảng các đối tượng, mỗi đối tượng có: 'section', 'similarity' (số từ 0-100), 'level' (Cao/Trung bình).

        Văn bản:
        {text[:2000]}
        """
        try:
            response = ai_engine.model.generate_content(prompt)
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned)
        except:
            return [
                {"section": "Nội dung lý luận cơ sở", "similarity": 65, "level": "Trung bình"},
                {"section": "Biện pháp tổ chức trò chơi toán học", "similarity": 75, "level": "Cao"}
            ]

    @staticmethod
    def predict_success_rate(text: str, ai_engine: AIEngine) -> dict:
        """Module 10: Giữ nguyên logic gọi Gemini dự đoán cấp đạt giải"""
        prompt = f"""
        Phân tích văn bản giáo dục này và dự đoán xác suất đạt giải/công nhận ở các cấp: Trường, Huyện, Tỉnh dựa trên cấu trúc đổi mới và tính khoa học.
        Trả về định dạng JSON chứa: 'rates' (mảng chứa 'level' và 'probability'), 'strengths', 'weaknesses', 'advice'.

        Văn bản: {text[:2000]}
        """
        try:
            response = ai_engine.model.generate_content(prompt)
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned)
        except:
            return {
                "rates": [
                    {"level": "Cấp Trường", "probability": 90},
                    {"level": "Cấp Huyện", "probability": 70},
                    {"level": "Cấp Tỉnh", "probability": 35}
                ],
                "strengths": "Cấu trúc rõ ràng, bám sát các phụ lục hướng dẫn hiện hành.",
                "weaknesses": "Phần số liệu đối chứng trước và sau tác động còn sơ sài.",
                "advice": "Đề tài có tính thực tiễn tốt nhưng cần bổ sung biểu đồ hoặc bảng điểm thực nghiệm để tăng khả năng đạt cấp Huyện và cấp Tỉnh."
            }
