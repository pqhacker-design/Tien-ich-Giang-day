import streamlit as st
from edu_research_assistant.ai_engine import call_ai_stream

def show_generator_module():
    st.subheader("💡 Tự Động Đề Xuất Đề Tài & Thiết Kế Đề Cương")
    
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            subject = st.text_input("Môn học (Generator)", value="Toán học")
            grade = st.text_input("Khối lớp (Generator)", value="Khối 8")
        with c2:
            target = st.text_input("Đối tượng học sinh (Generator)", value="Học sinh đại trà")
            keywords = st.text_input("Từ khóa", value="AI, Chuyển đổi số, STEM")
            
        problem = st.text_area("Thực trạng / Vấn đề gặp phải tại trường học:", 
                               value="Học sinh còn thụ động trong việc tiếp thu kiến thức mới.")
        
        doc_type = st.radio("Chọn loại cấu trúc đề cương cần xuất:", ["Sáng kiến kinh nghiệm (SKKN)", "NCKH Sư phạm Ứng dụng"])

    if st.button("🚀 Khởi tạo Đề tài & Đề cương Chi tiết"):
        with st.spinner("AI đang thiết lập ma trận đề tài..."):
            prompt = f"""
            Dựa trên thông tin: Môn {subject}, {grade}, Đối tượng: {target}, Từ khóa: {keywords}. Thực trạng: {problem}.
            Hãy:
            1. Đề xuất 20 tên đề tài {doc_type} bám sát thực tế kèm đánh giá tính mới.
            2. Xây dựng 01 khung đề cương chi tiết chuẩn Bộ GD&ĐT cho đề tài xuất sắc nhất trong số đó.
            """
            result = call_ai_stream(prompt, "Bạn là Chuyên gia Hội đồng Khoa học Giáo dục.")
            st.markdown(result)
