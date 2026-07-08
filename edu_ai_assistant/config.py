import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    APP_NAME: str = "AI Trợ lý Xử lý Văn bản Giáo dục"
    APP_VERSION: str = "2.0.0 Pro"
    PAGE_ICON: str = "🎓"
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Vector DB
    CHROMA_PERSIST_DIR: str = os.path.join(os.path.dirname(__file__), "data", "chroma_db")
    
    # Roles
    ROLE_ADMIN: str = "Quản trị viên"
    ROLE_TEACHER: str = "Giáo viên"
    ROLE_GUEST: str = "Khách"

    # Supported Document Types
    DOC_TYPES = [
        "Kế hoạch giáo dục (KHBD/Giáo án)",
        "Kế hoạch công tác/HKPĐ",
        "Báo cáo thành tích/SKKN",
        "Công văn/Thông báo/Quyết định",
        "Đề kiểm tra/Ma trận/Đáp án/Rubric",
        "Biên bản họp"
    ]

config = Config()
