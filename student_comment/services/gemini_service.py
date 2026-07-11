import os
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from pydantic import BaseModel

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def is_ready(self) -> bool:
        return self.client is not None

    def generate_comments(
        self, 
        student_data: Dict[str, Any], 
        model_name: str = "gemini-2.5-flash", 
        temperature: float = 0.7,
        num_variants: int = 10
    ) -> list[str]:
        """Sinh 10 nhận xét khác nhau dựa trên điểm số và quy định BGD"""
        if not self.is_ready():
            raise ValueError("Chưa cấu hình Gemini API Key!")

        prompt = f"""
        Bạn là giáo viên THCS Việt Nam giàu kinh nghiệm. Hãy phân tích bảng điểm sau của học sinh:
        - Họ và tên: {student_data.get('name')}
        - Điểm Thường xuyên: {student_data.get('tx_scores')}
        - Điểm Giữa kỳ: {student_data.get('gk_score')}
        - Điểm Cuối kỳ: {student_data.get('ck_score')}
        - Điểm Trung bình: {student_data.get('tb_score')}

        Nhiệm vụ: Tạo ra đúng {num_variants} câu nhận xét ĐÁNH GIÁ HỌC TẬP khác nhau hoàn toàn về vần điệu, cấu trúc câu, và góc nhìn.
        Yêu cầu:
        1. Bám sát Thông tư 22/2021/TT-BGDĐT.
        2. Tích cực, mang tính xây dựng, chỉ rõ điểm mạnh và hướng cải thiện.
        3. Không lặp từ ngữ giữa các lựa chọn.
        4. Trả về định dạng danh sách câu (mỗi câu một dòng).
        """

        config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=2048,
            system_instruction="Bạn là AI hỗ trợ Giáo viên THCS Việt Nam đạt chuẩn mực sư phạm."
        )

        response = self.client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        comments = [c.strip("- ").strip() for c in response.text.strip().split("\n") if c.strip()]
        return comments[:num_variants]

    def detect_anomalies(self, df_dict: list[dict]) -> str:
        """Phát hiện bất thường dữ liệu (Module 10)"""
        prompt = f"""
        Phân tích danh sách điểm số sau và phát hiện các bất thường (Ví dụ: nhảy điểm đột ngột từ 2 lên 10, thiếu điểm, sai định dạng, bất hợp lý):
        Dữ liệu: {df_dict}
        
        Trả về kết quả ngắn gọn, chỉ rõ Tên học sinh + Môn học + Bất thường cụ thể. KHÔNG TỰ SỬA DỮ LIỆU.
        """
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
