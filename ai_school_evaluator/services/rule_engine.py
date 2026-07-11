import json

class RuleEngine:
    def __init__(self, config_path="config/evaluation_rules.json"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def calculate_average(self, level, tx_list, gk, ck):
        if level in ["SECONDARY", "HIGH"]:
            if not tx_list or gk is None or ck is None:
                return 0.0
            # Áp dụng công thức động từ file cấu hình
            total_tx = sum(tx_list)
            count_tx = len(tx_list)
            avg = (total_tx + gk * 2 + ck * 3) / (count_tx + 5)
            return round(avg, 1)
        else:
            # Tiểu học đánh giá bằng nhận xét kết hợp điểm số định kỳ
            return ck if ck is not None else 0.0

    def suggest_level(self, level, avg_score):
        if level in ["SECONDARY", "HIGH"]:
            if avg_score >= 8.0: return "Tốt"
            if avg_score >= 6.5: return "Khá"
            if avg_score >= 5.0: return "Đạt"
            return "Chưa đạt"
        else:
            if avg_score >= 9.0: return "Hoàn thành xuất sắc"
            if avg_score >= 7.0: return "Hoàn thành tốt"
            if avg_score >= 5.0: return "Hoàn thành"
            return "Chưa hoàn thành"
