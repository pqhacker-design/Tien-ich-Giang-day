from google import genai
import os

class GeminiService:
    def __init__(self, api_keys: list):
        # Lọc các key hợp lệ
        self.api_keys = [k.strip() for k in api_keys if k and isinstance(k, str) and k.strip()]
        self.current_key_index = 0
        self.client = None
        self.setup_client()

    def setup_client(self):
        if self.api_keys:
            try:
                current_key = self.api_keys[self.current_key_index]
                # Sử dụng SDK chính thức mới nhất google-genai
                self.client = genai.Client(api_key=current_key)
            except Exception:
                self.client = None
        else:
            self.client = None

    def rotate_key(self):
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.setup_client()
            return True
        return False

    def generate_response(self, prompt: str) -> str:
        if not self.client:
            return "⚠️ Chưa cấu hình Gemini API Key! Vui lòng quay về Trang Chủ để nhập API Key."

        try:
            # Gọi model gemini-2.5-flash chuẩn SDK mới
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
                if self.rotate_key():
                    return self.generate_response(prompt)
            return f"❌ Lỗi AI: {str(e)}"
