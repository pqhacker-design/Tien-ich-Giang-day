import google.generativeai as genai
import os

class GeminiService:
    def __init__(self, api_keys: list):
        # Lọc bỏ các key rỗng nếu có
        self.api_keys = [k for k in api_keys if k and k.strip()]
        self.current_key_index = 0
        self.is_configured = False
        self.setup_client()

    def setup_client(self):
        if self.api_keys:
            genai.configure(api_key=self.api_keys[self.current_key_index])
            self.is_configured = True
        else:
            self.is_configured = False

    def rotate_key(self):
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.setup_client()
            return True
        return False

    def generate_response(self, prompt: str) -> str:
        if not self.is_configured:
            return "⚠️ Chưa cấu hình Gemini API Key! Vui lòng nhập API Key ở phần Cấu hình hoặc Trang chủ."

        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "quota" in str(e).lower() or "429" in str(e):
                if self.rotate_key():
                    return self.generate_response(prompt) # Thử lại với key tiếp theo
            return f"❌ Lỗi AI: {str(e)}"
