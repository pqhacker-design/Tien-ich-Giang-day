import os
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def is_ready(self) -> bool:
        return self.client is not None

    def generate_text(
        self, 
        prompt: str, 
        system_instruction: str = "Bạn là chuyên gia giáo dục THCS Việt Nam.",
        model_name: str = "gemini-2.5-flash", 
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        if not self.is_ready():
            raise ValueError("Chưa cấu hình Gemini API Key!")

        config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=0.95,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction
        )

        response = self.client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        return response.text

    def generate_10_unique_comments(self, student_info: Dict[str, Any], detail_level: str) -> List[str]:
        """Module 4: Sinh 10 nhận xét khác nhau, không lặp câu"""
        prompt = f"""
        Dữ liệu học sinh:
        - Họ tên: {student_info.get('full_name')}
        - Môn: {student_info.get('subject', 'Chung')}
        - Điểm TX: {student_info.get('score_tx')}
        - Điểm Giữa kỳ: {student_info.get('score_gk')}
        - Điểm Cuối kỳ: {student_info.get('score_ck')}
        - Điểm TB: {student_info.get('score_tb')}
        - Độ chi tiết yêu cầu: {detail_level}

        Hãy sinh ĐÚNG 10 nhận xét đánh giá học tập KHÁC NHAU HOÀN TOÀN về cấu trúc câu, từ ngữ và góc nhìn sư phạm.
        Yêu cầu:
        1. Tuân thủ Thông tư 22/2021/TT-BGDĐT.
        2. Tích cực, nêu bật ưu điểm và chỉ rõ hướng khắc phục.
        3. Không trùng lặp câu chữ giữa các nhận xét.
        4. Trả về đúng 10 dòng, mỗi dòng là một nhận xét bắt đầu bằng chữ số (1., 2., ...).
        """
        raw_text = self.generate_text(
            prompt, 
            system_instruction="Bạn là Trợ lý AI giáo viên chuyên sinh nhận xét học tập không dùng mẫu cứng."
        )
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        comments = [line.split(".", 1)[-1].strip() for line in lines if line[0].isdigit()]
        return comments[:10]
