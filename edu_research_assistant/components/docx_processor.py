import streamlit as st
from docx import Document

# Khối import linh hoạt để tránh lỗi đường dẫn hệ thống trên Streamlit Cloud
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

def show_docx_processor_module(api_key=None):
    st.subheader("📂 Trợ Lý AI Phân Tích & Thẩm Định Bản Nháp Word")
    st.info("Hỗ trợ đọc file .docx, tự động phát hiện lỗi chính tả, câu từ sư phạm và đánh giá cấu trúc theo quy chuẩn.")
    
    # Tải file Word lên hệ thống
    uploaded_file = st.file_uploader("Tải lên bản nháp Sáng kiến kinh nghiệm của thầy (.docx)", type=["docx"])
    
    if uploaded_file is not None:
        st.success("✅ Đã tải tệp lên thành công!")
        
        # Nút bấm kích hoạt AI quét văn bản
        if st.button("🧠 Kích hoạt AI quét và kiểm tra toàn diện"):
            with st.spinner("AI đang đọc dữ liệu văn bản và tiến hành thẩm định..."):
                try:
                    # 1. Tiến hành đọc toàn bộ nội dung từ file Word
                    doc = Document(uploaded_file)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            full_text.append(paragraph.text)
                    
                    text_content = "\n".join(full_text)
                    
                    # Giới hạn ký tự gửi lên AI để tránh vượt ngưỡng (Token Limit) nếu file quá dài
                    # Lấy khoảng 8000 ký tự đầu tiên (đủ quét phần Đặt vấn đề và các biện pháp cốt lõi)
                    preview_text = text_content[:8000]
                    
                    if len(text_content) == 0:
                        st.error("❌ File Word của thầy không có nội dung chữ hoặc nội dung nằm hoàn toàn trong bảng biểu/hình ảnh.")
                        return

                    st.info(f"📋 Hệ thống đã ghi nhận đoạn văn bản dài {len(text_content)} ký tự.")
                    
                    # 2. Xây dựng câu lệnh (Prompt) chi tiết gửi cho AI
                    prompt = f"""
                    Bạn là Thư ký Hội đồng Khoa học Giáo dục kiêm chuyên gia hiệu đính văn bản học thuật.
                    Hãy phân tích và kiểm tra đoạn văn bản trích từ bản nháp Sáng kiến kinh nghiệm dưới đây:
                    
                    --- NỘI DUNG VĂN BẢN ---
                    {preview_text}
                    ------------------------
                    
                    Hãy đưa ra báo cáo thẩm định chi tiết theo các mục sau (sử dụng định dạng Markdown):
                    1. 📝 ĐÁNH GIÁ VĂN PHONG SƯ PHẠM: (Kiểm tra xem câu từ đã chuẩn hành chính chưa, có bị sáo rỗng hoặc dùng ngôn ngữ nói không? Chỉ ra từ ngữ cần sửa nếu có).
                    2. 📐 ĐÁNH GIÁ CẤU TRÚC KHOA HỌC: (Các phần Đặt vấn đề, Biện pháp đã logic chưa? Các biện pháp có tính mới, tính đột phá và ứng dụng công nghệ/AI/chuyển đổi số không?).
                    3. 📈 ĐÁNH GIÁ TÍNH MINH CHỨNG: (Số liệu thực nghiệm, kết quả giả định hoặc các biểu mẫu đi kèm đã đủ thuyết phục hội đồng chấm chưa?).
                    4. 🛠️ ĐỀ XUẤT HƯỚNG SỬA ĐỔI: (Đưa ra ít nhất 3 gợi ý cụ thể để thầy cô bổ sung, chỉnh sửa nhằm nâng cao tỷ lệ đạt giải cao).
                    """
                    
                    # 3. Gọi AI xử lý truyền kèm API Key từ trang chủ sang
                    ai_response = call_ai_stream(
                        prompt=prompt,
                        system_instruction="Bạn là Giáo sư, Viện trưởng Viện Khoa học Giáo dục Việt Nam.",
                        api_key=api_key
                    )
                    
                    # 4. Hiển thị kết quả đánh giá của AI ra giao diện
                    st.markdown("### 📊 Kết quả Thẩm định từ Trợ lý AI:")
                    st.markdown(ai_response)
                    
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra khi xử lý cấu trúc file Word: {str(e)}")
