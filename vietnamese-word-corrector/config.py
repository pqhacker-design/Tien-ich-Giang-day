import os
import toml

class ConfigManager:
    @staticmethod
    def get_shared_api_key():
        """Tự động quét và lấy API Key dùng chung từ các dự án Streamlit hiện tại"""
        # Thử tìm trong thư mục cấu hình Streamlit mặc định của thầy
        possible_paths = [
            os.path.expanduser("~/.streamlit/secrets.toml"),
            "D:/Ung dung day va hoc/ai-lesson-plan/.streamlit/secrets.toml",
            "./.streamlit/secrets.toml"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    data = toml.load(path)
                    if "GEMINI_API_KEY" in data:
                        return data["GEMINI_API_KEY"]
                except:
                    pass
        return os.environ.get("GEMINI_API_KEY", "")

    @staticmethod
    def save_api_key(api_key):
        """Lưu API Key xuống file cấu hình cục bộ nếu cần"""
        os.makedirs("./.streamlit", exist_ok=True)
        with open("./.streamlit/secrets.toml", "w", encoding="utf-8") as f:
            f.write(f'GEMINI_API_KEY = "{api_key}"\n')