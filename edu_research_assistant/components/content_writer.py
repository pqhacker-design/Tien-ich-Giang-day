import streamlit as st
from edu_research_assistant.ai_engine import call_ai_stream

def show_content_writer_module():
    st.subheader("📝 Trợ Lý AI Biên Soạn Nội Dung Chuyên Sâu")
    
    title = st.text_input("Nhập tên đề tài chính thức cần viết bài:", value="Ứng dụng AI trong dạy học Toán lớp 8")
    mode = st.selectbox("Chế độ viết:", ["Viết ngắn", "Viết tiêu chuẩn", "Viết chi tiết", "Viết chuyên sâu"])
    action = st.selectbox("Hành động:", ["Viết mới từ đầu", "Viết mở rộng ý", "Tóm tắt/Rút gọn", "Chuyển đổi văn phong sư phạm"])
    
    section = st.selectbox("Chọn chương/phần mục:", [
        "Lý do chọn đề tài / Đặt vấn đề",
        "Cơ sở lý luận khoa học",
        "Thực trạng và nguyên nhân khó khăn",
        "Các biện pháp thực hiện (Nội dung cốt lõi)",
        "Kết quả đạt được và bài học kinh nghiệm"
    ])
    
    context_note = st.text_area("Ý tưởng cốt lõi hoặc tài liệu tham khảo bổ sung (nếu có):")

    if st.button("✍️ Bắt đầu sinh nội dung học thuật"):
        with st.spinner("AI đang tra cứu thuật ngữ và biên soạn văn bản..."):
            prompt = f"""
            Tên đề tài: {title}
            Yêu cầu: {action} phần '{section}' theo định dạng '{mode}'.
            Ý tưởng bổ sung: {context_note}
            Tiêu chuẩn: Sử dụng đúng văn phong sư phạm Việt Nam, lập luận chặt chẽ, logic, không nói sáo rỗng.
            """
            result = call_ai_stream(prompt, "Bạn là Giáo sư, chuyên gia viết các bài báo khoa học Giáo dục.")
            st.markdown(result)
