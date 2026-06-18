import google.generativeai as genai
import json

class AICorrector:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Sử dụng mô hình flash tối ưu cho tốc độ phân tích văn bản lớn
        self.model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})

    def analyze_text_block(self, text):
        """Phân tích một khối văn bản và tìm ra các lỗi chính tả, ngữ pháp, diễn đạt"""
        if not text.strip():
            return []

        prompt = f"""
        Bạn là một chuyên gia ngôn ngữ Tiếng Việt, biên tập viên cao cấp cho các văn bản hành chính, giáo án và công văn.
        Hãy rà soát đoạn văn bản sau để tìm các lỗi chính tả, lỗi ngữ pháp, lỗi dùng từ chưa chuẩn, câu văn rườm rà.
        
        Văn bản cần rà soát:
        \"\"\"{text}\"\"\"

        Trả về kết quả duy nhất ở cấu trúc JSON dưới đây (Không thêm bất kỳ từ ngữ nào ngoài JSON):
        {{
            "errors": [
                {{
                    "sai": "Từ hoặc cụm từ bị sai hoặc diễn đạt kém",
                    "dung": "Đề xuất sửa lại cho đúng hoặc hay hơn bám sát văn bản hành chính",
                    "loai": "Chính tả" hoặc "Ngữ pháp" hoặc "Diễn đạt",
                    "ly_do": "Giải thích ngắn gọn lý do sai"
                }}
            ]
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            res_json = json.loads(response.text)
            return res_json.get("errors", [])
        except Exception as e:
            print(f"Lỗi gọi Gemini AI: {str(e)}")
            return []