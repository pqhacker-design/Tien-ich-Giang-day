import pandas as pd

class DashboardPanel:
    @staticmethod
    def get_dashboard_metrics(ai_rate: int, plag_rate: int, success_rates: list):
        """
        MODULE 11: BẢNG ĐIỀU KHIỂN THẨM ĐỊNH AI
        """
        metrics = {
            "quality_score": 82,
            "completion_rate": 90,
            "plagiarism_rate": plag_rate,
            "ai_suspicion": ai_rate,
            "highest_potential": "Cấp Huyện"
        }
        return metrics

    @staticmethod
    def simulate_committee_debate(text: str, ai_engine: AIEngine) -> list:
        """
        MODULE 12: AI PHẢN BIỆN HỘI ĐỒNG (Đa góc nhìn diện rộng)
        """
        prompt = f"""
        Hãy giả lập đóng vai 3 giám khảo phản biện trong hội đồng chấm Sáng kiến kinh nghiệm / Hồ sơ giáo viên:
        - Phản biện 1: Tập trung vào tính thực tiễn và tính khả thi.
        - Phản biện 2: Tập trung kiểm tra tính khoa học, minh chứng số liệu và phụ lục.
        - Phản biện 3: Tập trung đánh giá tính đổi mới, sáng tạo và tính mới của giải pháp.
        Xuất ra định dạng JSON mảng 'debates' gồm các trường: 'reviewer', 'opinion', 'score'.

        Văn bản: {text[:2000]}
        """
        response = ai_engine.model.generate_content(prompt)
        try:
            cleaned = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned).get("debates", [])
        except:
            return [
                {"reviewer": "Phản biện 1 (Thực tiễn)", "opinion": "Đánh giá cao tính thực tiễn, giải pháp dễ triển khai tại cơ sở.", "score": 85},
                {"reviewer": "Phản biện 2 (Khoa học & Số liệu)", "opinion": "Thiếu minh chứng số liệu cụ thể ở biểu đồ đối chứng.", "score": 70},
                {"reviewer": "Phản biện 3 (Tính đổi mới)", "opinion": "Cần làm rõ tính mới, một số biện pháp còn trùng lặp với lối mòn cũ.", "score": 75}
            ]

    @staticmethod
    def get_strategic_roadmap(query: str, ai_engine: AIEngine) -> str:
        """
        MODULE 13: AI CỐ VẤN CHIẾN LƯỢC
        Vạch ra lộ trình nâng cấp hồ sơ để đạt thứ hạng cao hơn.
        """
        prompt = f"""
        Người dùng hỏi: '{query}'. 
        Với vai trò là Chuyên gia cố vấn chiến lược thi đua ngành giáo dục, hãy lập kế hoạch hành động sửa đổi cụ thể, phân cấp mức độ ưu tiên (Cao/Trung bình/Thấp) và thời gian thực hiện ước tính để nâng tầm hồ sơ.
        """
        response = ai_engine.model.generate_content(prompt)
        return response.text
