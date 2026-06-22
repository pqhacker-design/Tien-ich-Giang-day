# ai_auditor_app/modules/grammar_checker.py
import re
import json

class VietnameseGrammarChecker:
    @staticmethod
    def advanced_check(text: str, ai_engine) -> list:
        """
        Sử dụng trực tiếp Gemini API để rà soát lỗi chính tả và ngữ pháp tiếng Việt 
        Không phụ thuộc vào các thư viện local như underthesea hay rapidfuzz.
        """
        if not ai_engine:
            return []
            
        prompt = f"""
        Hãy rà soát lỗi chính tả, lỗi lặp từ, dấu câu hoặc câu quá dài, diễn đạt lủng củng trong đoạn văn bản giáo dục sau đây.
        Yêu cầu trả về kết quả dưới dạng cấu trúc JSON nguyên bản (không bọc trong khối ```json), là một mảng các đối tượng chứa:
        - "error_text": Từ ngữ hoặc đoạn bị lỗi
        - "suggested_text": Đề xuất sửa lại cho đúng chuẩn hành chính
        - "reason": Giải thích ngắn gọn nguyên nhân lỗi

        Văn bản cần rà soát:
        {text[:2000]}
        """
        try:
            response = ai_engine.model.generate_content(prompt)
            # Làm sạch chuỗi phản hồi tránh lỗi ký tự markdown bọc JSON
            cleaned_text = re.sub(r"```[a-zA-Z]*\n|```", "", response.text).strip()
            return json.loads(cleaned_text)
        except:
            # Trả về mảng rỗng nếu có lỗi kết nối hoặc parse JSON lỗi
            return []
