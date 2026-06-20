import streamlit as st
# Sửa lại đường dẫn import tùy thuộc vào cấu trúc thư mục thực tế của thầy
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

# Thêm tham số api_key=None vào định nghĩa hàm để nhận Key truyền sang
def show_content_writer_module(api_key=None):
    st.subheader("📝 Trợ Lý AI Biên Soạn Nội Dung Chuyên Sâu")
    
    title = st.text_input("Nhập tên đề tài chính thức cần viết bài:", value="Ứng dụng sơ đồ tư duy kết hợp công nghệ AI nhằm nâng cao năng lực tự học hình học của học sinh lớp 8")
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
        if not title.strip():
            st.error("Vui lòng nhập tên đề tài trước khi viết.")
            return
            
        with st.spinner("AI đang tra cứu thuật ngữ chuyên ngành và biên soạn văn bản..."):
            prompt = f"""
            Tên đề tài: {title}
            Yêu cầu: {action} phần '{section}' theo chế độ '{mode}'.
            Ý tưởng bổ sung từ tác giả: {context_note}
            
            Tiêu chuẩn bắt buộc: 
            - Sử dụng đúng văn phong sư phạm, ngôn ngữ hành chính học thuật của ngành giáo dục Việt Nam.
            - Lập luận logic, chặt chẽ, có số liệu thực tế giả định thuyết phục.
            - Không viết sáo rỗng, bám sát các thông tư đổi mới phương pháp dạy học của Bộ GD&ĐT.
            """
            
            # TRUYỀN api_key VÀO ĐÂY ĐỂ GỌI SỬ DỤNG
            result = call_ai_stream(prompt, "Bạn là Giáo sư, chuyên gia viết các bài báo khoa học Giáo dục Việt Nam.", api_key=api_key)
            st.markdown(result)
