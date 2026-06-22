import random

class CommitteeEvaluator:
    @staticmethod
    def generate_committee_report(doc_name: str, score: float, criteria_weights: dict, members_count: int = 5) -> dict:
        names = ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D", "Vũ Xuân E"]
        roles = ["Chủ tịch Hội đồng", "Phản biện 1", "Phản biện 2", "Ủy viên Thư ký", "Ủy viên"]
        
        committee_reviews = {}
        base_score = score
        
        for i in range(min(members_count, len(names))):
            deviation = random.uniform(-5, 5)
            member_score = max(0, min(100, round(base_score + deviation, 1)))
            
            if member_score >= 90: rating = "Xuất sắc"
            elif member_score >= 75: rating = "Tốt"
            elif member_score >= 50: rating = "Đạt"
            else: rating = "Không đạt - Cần hoàn thiện lại"
            
            committee_reviews[names[i]] = {
                "role": roles[i],
                "score": member_score,
                "rating": rating,
                "comment": f"Hồ sơ {doc_name} có tính thực tiễn cao, đáp ứng tốt cấu trúc cốt lõi. Tuy nhiên cần cập nhật chuẩn xác danh mục minh chứng phụ lục."
            }
        return committee_reviews
