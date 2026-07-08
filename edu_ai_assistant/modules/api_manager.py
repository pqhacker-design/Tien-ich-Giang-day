import google.generativeai as genai
import streamlit as st

class APIManager:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or st.session_state.get("gemini_api_key", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
    def get_model(self, model_name: str = "gemini-2.5-flash", temperature: float = 0.2):
        if not self.api_key:
            raise ValueError("Chưa cấu hình Gemini API Key. Vui lòng nhập key trong Cài đặt hoặc file .env")
        return genai.GenerativeModel(
            model_name=model_name,
            generation_config={"temperature": temperature}
        )

    def generate_response(self, prompt: str, system_instruction: str = None, temperature: float = 0.2) -> str:
        if not self.api_key:
            return "⚠️ Lỗi: Chưa cấu hình Gemini API Key!"
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction,
                generation_config={"temperature": temperature}
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"❌ Lỗi xử lý AI: {str(e)}"
