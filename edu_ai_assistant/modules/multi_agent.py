from modules.api_manager import APIManager
from modules.rag import KnowledgeHubRAG
import streamlit as st

class MultiAgentWorkflow:
    def __init__(self, api_key: str, rag_system: KnowledgeHubRAG = None):
        self.api_mgr = APIManager(api_key=api_key)
        self.rag = rag_system

    def agent_legal_checker(self, document_text: str, rag_context: str) -> str:
        prompt = f"""Bạn là Chuyên gia Legal Agent (Kiểm tra Pháp lý Giáo dục).
Căn cứ pháp lý chuẩn trong Knowledge Base:
{rag_context}

Tài liệu cần kiểm tra:
{document_text[:3000]}

Nhiệm vụ: Phân tích các căn cứ pháp lý, Nghị định, Thông tư được dẫn chiếu trong văn bản. Chỉ ra căn cứ nào đã hết hiệu lực, thiếu căn cứ nào, hoặc đề xuất sửa đổi bổ sung theo đúng chuẩn Ngành Giáo dục."""
        return self.api_mgr.generate_response(prompt, temperature=0.1)

    def agent_format_checker(self, document_text: str) -> str:
        prompt = f"""Bạn là Chuyên gia Format Agent (Thể thức văn bản hành chính theo Nghị định 30/2020/NĐ-CP & Quyết định Ngành GD).
Soát lỗi thể thức văn bản sau:
{document_text[:3000]}

Nhiệm vụ: Nhận xét chi tiết về Quốc hiệu, Tên cơ quan, Số/Ký hiệu, Tiêu đề, Bố cục, Nơi nhận, Chữ ký. Chỉ ra các lỗi sai cụ thể."""
        return self.api_mgr.generate_response(prompt, temperature=0.1)

    def agent_pedagogy_editor(self, document_text: str, user_instruction: str) -> str:
        prompt = f"""Bạn là Chuyên gia Pedagogy & Language Agent (Tối ưu Giáo dục & Văn phong).
Yêu cầu chỉnh sửa từ người dùng: "{user_instruction}"

Tài liệu gốc:
{document_text}

Nhiệm vụ: Chỉnh sửa lại nội dung văn bản cho đúng chuyên môn sư phạm, diễn đạt chuẩn hành chính, mạch lạc, chính xác. Nếu có yêu cầu chuyển đổi (ví dụ: đổi nội dung môn học, đổi mẫu) hãy cập nhật toàn bộ thuật ngữ liên quan."""
        return self.api_mgr.generate_response(prompt, temperature=0.3)

    def agent_lead_coordinator(self, original_text: str, legal_feedback: str, format_feedback: str, edited_text: str) -> dict:
        prompt = f"""Bạn là Trưởng nhóm Agent (Chief Educational AI Editor).
Hãy tổng hợp đánh giá và tạo báo cáo hoàn chỉnh dựa trên phân tích của các Agent:

1. Phân tích Pháp lý:
{legal_feedback}

2. Phân tích Thể thức:
{format_feedback}

3. Văn bản đã đề xuất tối ưu:
{edited_text}

YÊU CẦU ĐẦU RA (Trả về định dạng rõ ràng):
---BÁO CÁO ĐÁNH GIÁ CHẤT LƯỢNG---
- Điểm Thể thức: [X/10]
- Điểm Pháp lý: [X/10]
- Điểm Nội dung & Sư phạm: [X/10]
- Khả năng được Phê duyệt: [Rất Cao / Cao / Trung Bình / Cần Sửa]
- Chi tiết các thay đổi chính & Lý do:
(Liệt kê rõ ràng)

---VĂN BẢN HOÀN CHỈNH ĐÃ XỬ LÝ---
(Chép lại toàn bộ văn bản mới hoàn thiện ở đây)
"""
        final_out = self.api_mgr.generate_response(prompt, temperature=0.2)
        return final_out

    def execute_full_workflow(self, document_text: str, user_prompt: str, progress_bar, status_text) -> str:
        status_text.text("🔍 [Bước 1/5] Tra cứu Tri thức ngành Giáo dục (RAG Knowledge Hub)...")
        progress_bar.progress(20)
        rag_context = self.rag.query_relevant_context(document_text[:500]) if self.rag else ""

        status_text.text("⚖️ [Bước 2/5] Agent Pháp lý đang kiểm tra Căn cứ & Thông tư...")
        progress_bar.progress(40)
        legal_res = self.agent_legal_checker(document_text, rag_context)

        status_text.text("📐 [Bước 3/5] Agent Thể thức đang rà soát chuẩn Nghị định 30...")
        progress_bar.progress(60)
        format_res = self.agent_format_checker(document_text)

        status_text.text("✍️ [Bước 4/5] Agent Chuyên môn đang thực hiện biên tập & mở rộng Prompt...")
        progress_bar.progress(80)
        pedagogy_res = self.agent_pedagogy_editor(document_text, user_prompt)

        status_text.text("👑 [Bước 5/5] Trưởng nhóm Agent tổng hợp ý kiến & đánh giá chất lượng...")
        progress_bar.progress(100)
        final_result = self.agent_lead_coordinator(document_text, legal_res, format_res, pedagogy_res)

        return final_result
