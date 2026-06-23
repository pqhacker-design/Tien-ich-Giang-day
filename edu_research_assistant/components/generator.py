import streamlit as st
# Khối import linh hoạt để tránh lỗi đường dẫn hệ thống
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

# BỔ SUNG: Thêm tham số api_key=None vào định nghĩa hàm để nhận Key truyền sang
def show_generator_module(api_key=None):
    st.subheader("💡 Tự Động Đề Xuất Đề Tài & Thiết Kế Đề Cương")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Môn học (Generator)", value="Toán học")
            grade = st.text_input("Khối lớp (Generator)", value="Khối 8")
        with col2:
            target = st.text_input("Đối tượng học sinh (Generator)", value="Học sinh đại trà")
            keywords = st.text_input("Từ khóa", value="AI, Chuyển đổi số, STEM")
            
        problem = st.text_area("Thực trạng / Vấn đề gặp phải tại trường học:", 
                               value="Học sinh còn thụ động trong việc tiếp thu kiến thức mới.")
        
        doc_type = st.radio("Chọn loại cấu trúc đề cương cần xuất:", ["Sáng kiến kinh nghiệm (SKKN)", "NCKH Sư phạm Ứng dụng"])

    if st.button("🚀 Khởi tạo Đề tài & Đề cương Chi tiết"):
        if not problem.strip():
            st.error("Vui lòng nhập thực trạng hoặc vấn đề thực tế gặp phải.")
            return
            
        with st.spinner("AI đang thiết lập ma trận đề tài và phân tích bối cảnh giáo dục..."):
            prompt = f"""
            Dựa trên thông tin bối cảnh: Môn {subject}, {grade}, Đối tượng học sinh: {target}, Từ khóa định hướng: {keywords}. 
            Thực trạng tại cơ sở: {problem}.
            
            Hãy tự động đề xuất cấu trúc danh mục bao gồm đầy đủ:
            1. 20 tên đề tài SKKN bám sát thực tế.
            2. 20 tên giải pháp nghiên cứu khoa học sư phạm ứng dụng.
            3. 20 tên sáng kiến chuyển đổi số mạnh mẽ trong dạy học.
            4. 20 tên giải pháp nâng cao chất lượng dạy và học cốt lõi.
            
            Mỗi đề tài yêu cầu ghi rõ định lượng về: 'Mức độ mới' và 'Khả năng áp dụng thực tế'.
            Cuối cùng, tự động xây dựng 01 khung đề cương chi tiết chuẩn cấu trúc {doc_type} của Bộ GD&ĐT cho 01 đề tài xuất sắc nhất trong danh sách trên.
            """
            
            # TRUYỀN api_key VÀO ĐÂY ĐỂ ĐỒNG BỘ VỚI TRANG CHỦ
            result = call_ai_stream(prompt, "Bạn là Chuyên gia cao cấp thuộc Hội đồng Khoa học Giáo dục Việt Nam.", api_key=api_key)
            st.markdown(result)
