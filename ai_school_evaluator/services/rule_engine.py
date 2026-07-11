import json
import os

class RuleEngine:
    def __init__(self, config_path=None):
        if config_path is None:
            # Lấy đường dẫn tuyệt đối của thư mục chứa file rule_engine.py
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Đi ngược ra thư mục cha (ai_school_evaluator) rồi trỏ vào config/evaluation_rules.json
            config_path = os.path.join(base_dir, "..", "config", "evaluation_rules.json")
        
        # Đảm bảo đường dẫn chuẩn hóa theo hệ điều hành (Windows/Linux/Streamlit Cloud)
        config_path = os.path.normpath(config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Không tìm thấy file cấu hình tại: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def calculate_average(self, level, tx_list, gk, ck):
        if level in ["SECONDARY", "HIGH"]:
            if not tx_list or gk is None or ck is None:
                return 0.0
            total_tx = sum(tx_list)
            count_tx = len(tx_list)
            avg = (total_tx + gk * 2 + ck * 3) / (count_tx + 5)
            return round(avg, 1)
        else:
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
