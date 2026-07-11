from google import genai
from google.genai import types
import streamlit as st

class APIManager:
    def __init__(self, api_key: str = None):
        # Lấy API Key từ tham số hoặc tự động lấy từ Trang chủ (session_state)
        self.api_key = api_key or st.session_state.get("gemini_api_key") or st.session_state.get("saved_api_key") or ""
        self.client = None
        
        if self.api_key and isinstance(self.api_key, str) and self.api_key.strip():
            try:
                self.client = genai.Client(api_key=self.api_key.strip())
            except Exception:
                self.client = None

    def generate_response(self, prompt: str, system_instruction: str = None, temperature: float = 0.2) -> str:
        """Sinh nội dung từ Gemini API an toàn, không crash app nếu thiếu key"""
        if not self.client:
            return "⚠️ Lỗi: Chưa cấu hình Gemini API Key! Vui lòng quay về Trang chủ để nhập API Key."
            
        try:
            config = types.GenerateContentConfig(
                temperature=temperature,
                system_instruction=system_instruction
            )
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            return f"❌ Lỗi xử lý AI: {str(e)}"
