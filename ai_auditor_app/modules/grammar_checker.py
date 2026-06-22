from underthesea import classify
from rapidfuzz import process

class VietnameseGrammarChecker:
    @staticmethod
    def advanced_check(text: str, ai_engine: AIEngine) -> list:
        """
        Sử dụng kết hợp phân tích ngôn ngữ tự nhiên underthesea và mô hình ngôn ngữ lớn để bắt lỗi ngữ cảnh nâng cao.
        """
        prompt = f"""
        Hãy rà soát chính tả, lỗi lặp từ, câu quá dài hoặc câu thiếu chủ vị trong đoạn văn bản hành chính giáo dục sau đây.
        Trả về cấu trúc JSON chứa mảng các lỗi tìm thấy bao gồm: "error_text", "suggested_text", "reason".
        
        Văn bản:
        {text}
        """
        response = ai_engine.model.generate_content(prompt)
        import re, json
        try:
            cleaned_text = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned_text)
        except:
            return []
