import streamlit as st
# Khối import linh hoạt để tránh lỗi đường dẫn hệ thống
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

# BỔ SUNG: Thêm tham số api_key=None vào định nghĩa hàm để nhận Key truyền sang
def show_generator_module(api_key=None):
    st.subheader("💡 I. Tự Động Đề Xuất Đề Tài & Thiết Kế Đề Cương")
    st.info("Hệ thống hỗ trợ thầy cô tìm kiếm ý tưởng đề tài đột phá và xây dựng cấu trúc đề cương sáng kiến chuẩn hóa.")
    
    # 1. Khung nhập thông tin đầu vào
    subject = st.text_input("Nhập bộ môn / lĩnh vực giảng dạy (Ví dụ: Toán lớp 8, Khoa học tự nhiên lớp 6):")
    context_idea = st.text_area("Nhập ý tưởng sơ khởi hoặc khó khăn thực tế (nếu có):", 
                                placeholder="Ví dụ: Học sinh còn yếu phần hình học trực quan, muốn ứng dụng AI hoặc sơ đồ tư duy...")
    
    col1, col2 = st.columns(2)
    with col1:
        btn_topic = st.button("🧠 Bước 1: Gợi ý 3 Đề tài Đột phá")
    with col2:
        btn_outline = st.button("📋 Bước 2: Thiết kế Đề cương Chi tiết")
        
    # 2. Xử lý logic BƯỚC 1: TẠO ĐỀ TÀI
    if btn_topic:
        if not subject:
            st.error("❌ Vui lòng nhập bộ môn hoặc lĩnh vực giảng dạy.")
        else:
            with st.spinner("AI đang nghiên cứu xu hướng sư phạm và đề xuất đề tài..."):
                prompt_topic = f"Bạn là chuyên gia giáo dục. Hãy đề xuất 3 tên đề tài sáng kiến kinh nghiệm độc đáo, có tính mới và ứng dụng công nghệ/đổi mới cho bộ môn: {subject}. Ý tưởng bổ sung: {context_idea}."
                
                # Gọi AI lấy kết quả
                topic_res = call_ai_stream(prompt=prompt_topic, system_instruction="Bạn là Giáo sư Viện khoa học giáo dục.", api_key=api_key)
                
                # ÉP LƯU VÀO BỘ NHỚ HỆ THỐNG
                st.session_state["generated_topic"] = topic_res

    # 3. Xử lý logic BƯỚC 2: TẠO ĐỀ CƯƠNG
    if btn_outline:
        if not st.session_state["generated_topic"]:
            st.error("❌ Thầy vui lòng bấm tạo Đề tài ở Bước 1 trước, hoặc nhập tên đề tài cụ thể.")
        else:
            with st.spinner("AI đang xây dựng ma trận cấu trúc đề cương chi tiết..."):
                prompt_outline = f"Hãy thiết kế đề cương chi tiết (gồm Đặt vấn đề, Biện pháp thực hiện, Kết quả dự kiến) cho đề tài sau: {st.session_state['generated_topic']}."
                
                # Gọi AI lấy kết quả
                outline_res = call_ai_stream(prompt=prompt_outline, system_instruction="Bạn là Chuyên gia xây dựng khung chương trình giáo dục.", api_key=api_key)
                
                # ÉP LƯU VÀO BỘ NHỚ HỆ THỐNG
                st.session_state["generated_outline"] = outline_res

    # --- ĐOẠN CODE QUAN TRỌNG: LUÔN HIỂN THỊ DỮ LIỆU CŨ NẾU ĐÃ TỒN TẠI TRONG SESSION STATE ---
    st.markdown("---")
    if st.session_state["generated_topic"]:
        st.markdown("### 📌 Danh sách Đề tài đã khởi tạo:")
        st.markdown(st.session_state["generated_topic"])
        
    if st.session_state["generated_outline"]:
        st.markdown("### 📊 Cấu trúc Đề cương Chi tiết:")
        st.markdown(st.session_state["generated_outline"])
