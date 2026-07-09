import streamlit as st
# Khối import linh hoạt để tránh lỗi đường dẫn hệ thống
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

# BỔ SUNG: Thêm tham số api_key=None vào định nghĩa hàm để nhận Key truyền sang
def show_generator_module(api_key=None):
    st.markdown(
        """
        <div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #0369A1;">💡 Tự Động Đề Xuất Đề Tài & Thiết Kế Đề Cương</h4>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("**Môn học:**", value="Toán học", key="gen_subject")
            grade = st.text_input("**Khối lớp:**", value="Khối 8", key="gen_grade")
        with col2:
            target = st.text_input("**Đối tượng học sinh:**", value="Học sinh đại trà", key="gen_target")
            keywords = st.text_input("**Từ khóa**", value="AI, Chuyển đổi số, STEM", key="gen_keywords")
            
        problem = st.text_area("**Thực trạng / Vấn đề gặp phải tại trường học:**", 
                               value="Học sinh còn thụ động trong việc tiếp thu kiến thức mới.", key="gen_problem")
        
        doc_type = st.radio("**Chọn loại cấu trúc đề cương cần xuất:**", ["Sáng kiến kinh nghiệm (SKKN)", "NCKH Sư phạm Ứng dụng"], key="gen_doc_type")

    # --- TRONG FILE components/generator.py ---
# Tìm đến đoạn xử lý nút bấm và sửa lại như sau:

    if st.button("🚀 Khởi tạo Đề tài & Đề cương Chi tiết", type="primary"):
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
            
            try:
                result = call_ai_stream(prompt, "Bạn là Chuyên gia cao cấp thuộc Hội đồng Khoa học Giáo dục Việt Nam.", api_key=api_key)
                
                if result and any(k in str(result).lower() for k in ["quota", "insufficient_quota", "exceeded", "limit"]):
                    st.error("⚠️ **Thông báo:** API Key của bạn đã **hết quota**...")
                else:
                    # BỔ SUNG: Lưu kết quả vào session_state thay vì chỉ hiển thị đơn thuần
                    st.session_state["generator_result"] = result
                    
            except Exception as e:
                # (Giữ nguyên đoạn catch lỗi quota của thầy/cô ở đây...)
                error_msg = str(e).lower()
                if "quota" in error_msg or "limit" in error_msg or "429" in error_msg or "insufficient" in error_msg:
                    st.error("⚠️ **Thông báo:** API Key của bạn đã hết quota...")
                else:
                    st.error(f"❌ Đã xảy ra lỗi hệ thống khi gọi AI: {e}")

    # BỔ SUNG VÀO CUỐI HÀM: Luôn hiển thị lại kết quả cũ nếu đã có trong Session State
    if "generator_result" in st.session_state and st.session_state["generator_result"]:
        st.markdown("---")
        st.subheader("📋 Kết quả đã khởi tạo trước đó:")
        st.markdown(st.session_state["generator_result"])
