import streamlit as st
from database import init_db, save_project, get_all_projects
from ai_engine import call_ai_stream, get_council_critique
from components.evidence_creator import show_evidence_creator_module

# Cấu hình Page cấu trúc hiện đại
st.set_page_config(
    page_title="Hệ thống Trợ lý Hồ sơ Khoa học Giáo dục AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Khởi tạo DB nội bộ
init_db()

# --- SIDEBAR ĐIỀU HƯỚNG ---
with st.sidebar:
    st.title("🎓 TRỢ LÝ SƯ PHẠM AI")
    st.subheader("Hệ thống Phát triển Hồ sơ Chuyên môn")
    st.markdown("---")
    
    menu = st.radio(
        "DANH MỤC CHỨC NĂNG:",
        [
            "🏠 Tổng quan hệ thống",
            "💡 I. Tạo Đề tài Thông minh",
            "📝 II & III. Thiết kế Đề cương & Viết nội dung",
            "📊 IV & XI. Xử lý Thống kê & Sinh Minh chứng",
            "🕵️‍♂️ Trợ lý Hội đồng Phản biện AI",
            "📚 Thư viện Mẫu Sáng kiến"
        ]
    )
    st.markdown("---")
    st.caption("⚡ Phát triển bởi Chuyên gia Công nghệ Giáo dục Việt Nam. Phiên bản tối ưu hóa 2026.")

# --- MÀN HÌNH CHÍNH ---
if menu == "🏠 Tổng quan hệ thống":
    st.title("Hệ thống Trợ lý AI Hỗ trợ Phát triển & Quản lý Hồ sơ Khoa học Sư phạm Toàn diện")
    st.markdown("""
    Chào mừng thầy/cô đến với nền tảng số hóa tối ưu năng lực nghiên cứu sư phạm ứng dụng. Hệ thống hỗ trợ xử lý toàn diện chu trình vòng đời một sáng kiến, giải pháp giáo dục:
    * **Tối ưu hóa thời gian biên soạn văn bản hành chính sư phạm.**
    * **Đo lường chính xác các chỉ số định lượng e-T, độ lệch chuẩn, mức độ tăng trưởng của học sinh trước và sau tác động.**
    * **Phản biện giả thuyết khoa học chặt chẽ nhờ mô hình AI chuyên sâu ngành giáo dục.**
    """)
    
    # Hiển thị các dự án đã lưu trong hệ thống SQLite địa phương
    st.subheader("📂 Danh sách dự án nghiên cứu hiện hành trong cơ sở dữ liệu")
    projects = get_all_projects()
    if projects:
        for p in projects:
            st.info(f"ID: {p[0]} - Đề tài: **{p[1]}** - Bộ môn: {p[2]} ({p[3]})")
    else:
        st.write("Chưa có dự án nào được lưu. Hãy bắt đầu tạo đề tài tại thanh điều hướng bên trái.")

elif menu == "💡 I. Tạo Đề tài Thông minh":
    st.header("💡 Khởi Tạo & Đề Xuất Tên Đề Tài Khoa Học Thông Minh")
    
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            subject = st.text_input("Môn học", value="Toán học")
            level = st.selectbox("Cấp học", ["Tiểu học", "THCS", "THPT"])
        with c2:
            grade = st.text_input("Khối lớp", value="Khối 8")
            target = st.text_input("Đối tượng học sinh", value="Học sinh đại trà và học sinh yếu kém")
        with c3:
            keywords = st.text_input("Từ khóa nghiên cứu", value="Ứng dụng công nghệ, AI, sơ đồ tư duy")
            
        problem = st.text_area("Vấn đề thực tế gặp phải tại cơ sở giáo dục", 
                               value="Học sinh lười suy nghĩ, gặp khó khăn khi học các định lý hình học và thiếu tính chủ động trong học tập hợp tác.")
        
        btn_generate = st.button("🚀 AI Đề xuất 80 Đề tài & Đánh giá Tính mới")
        
        if btn_generate:
            with st.spinner("AI đang nghiên cứu thực trạng và tạo danh sách đề tài..."):
                prompt = f"""Dựa trên thực trạng: {problem}, môn {subject}, lớp {grade}, đối tượng: {target}, từ khóa: {keywords}.
                Hãy đề xuất danh sách chính xác gồm:
                - 20 tên đề tài SKKN.
                - 20 tên giải pháp nghiên cứu khoa học sư phạm ứng dụng.
                - 20 tên sáng kiến chuyển đổi số trong dạy học.
                - 20 tên giải pháp nâng cao chất lượng dạy và học.
                Mỗi đề tài kèm theo 1 câu nhận xét ngắn gọn về 'Mức độ mới và Khả năng áp dụng thực tế' đúng văn phong giáo dục Việt Nam."""
                
                result = call_ai_stream(prompt, "Bạn là giáo sư đầu ngành nghiên cứu phương pháp dạy học của Viện Khoa học Giáo dục Việt Nam.")
                st.markdown(result)

elif menu == "📝 II & III. Thiết kế Đề cương & Viết nội dung":
    st.header("📝 Thiết Kế Cấu Trúc Đề Cương & Viết Nội Dung Tự Động")
    
    doc_type = st.selectbox("Chọn loại hình hồ sơ", ["Sáng kiến kinh nghiệm (SKKN)", "Nghiên cứu khoa học sư phạm ứng dụng (NCKHSPƯD)"])
    writing_style = st.select_slider("Mức độ chuyên sâu của nội dung viết", options=["Viết ngắn", "Viết tiêu chuẩn", "Viết chi tiết", "Viết chuyên sâu"])
    
    title_research = st.text_input("Nhập tên đề tài chính thức để viết", value="Ứng dụng sơ đồ tư duy kết hợp công nghệ AI nhằm nâng cao năng lực tự học hình học của học sinh lớp 8")
    
    section_to_write = st.selectbox("Lựa chọn phạm vi viết bài", ["Viết toàn bộ đề tài", "Mở đầu / Đặt vấn đề", "Cơ sở lý luận", "Thực trạng giải pháp", "Phân tích hiệu quả tác động", "Kết luận kiến nghị"])
    
    if st.button("✍️ Ra lệnh cho Trợ lý AI viết văn bản chuyên sâu"):
        with st.spinner("AI đang xử lý ngôn ngữ học thuật chuyên sâu..."):
            prompt = f"Hãy soạn thảo nội dung mục '{section_to_write}' cho đề tài: '{title_research}' theo chế độ '{writing_style}' đúng chuẩn văn phong nghị luận khoa học giáo dục."
            content_output = call_ai_stream(prompt, "Bạn là chuyên gia viết báo cáo khoa học sư phạm, sử dụng thuật ngữ chuẩn của Bộ Giáo dục.")
            st.markdown(content_output)
            
            # Nút bấm lưu trữ vào DB
            if st.button("💾 Lưu dự án này vào Hệ thống"):
                save_project(title_research, "Toán", "Lớp 8", doc_type, "", "", "", "", content_output)
                st.toast("Đã lưu nội dung thành công!")

elif menu == "📊 IV & XI. Xử lý Thống kê & Sinh Minh chứng":
    show_evidence_creator_module()

elif menu == "🕵️‍♂️ Trợ lý Hội đồng Phản biện AI":
    st.header("🕵️‍♂️ Trợ Lý AI Phản Biện Đề Tài - Đóng vai Hội đồng chấm Sáng kiến")
    st.warning("Hãy dán nội dung bản nháp đề tài của thầy vào đây để Hội đồng AI chấm điểm thử nghiệm trước khi nộp chính thức lên cấp trên.")
    
    critique_title = st.text_input("Tên đề tài cần thẩm định", value="Ứng dụng sơ đồ tư duy kết hợp công nghệ AI nhằm nâng cao năng lực tự học hình học của học sinh lớp 8")
    critique_content = st.text_area("Nội dung chi tiết các chương/biện pháp đã viết", height=300, placeholder="Dán toàn bộ nội dung văn bản tại đây...")
    council_level = st.selectbox("Cấp hội đồng chấm duyệt", ["Cấp Trường / Cơ sở", "Cấp Quận / Huyện / Phòng GDĐT", "Cấp Tỉnh / Thành phố / Sở GDĐT"])
    
    if st.button("⚖️ Bắt đầu Thẩm định & Chấm điểm"):
        if critique_content:
            with st.spinner("Hội đồng đang thảo luận, phản biện kín và chấm điểm..."):
                critique_res = get_council_critique(critique_title, critique_content, council_level)
                st.markdown(critique_res)
        else:
            st.error("Vui lòng cung cấp nội dung văn bản đề tài để hội đồng phân tích.")

elif menu == "📚 Thư viện Mẫu Sáng kiến":
    st.header("📚 Thư Viện Tra Cứu Đề Tài Mẫu & Khung Đề Cương Quy Chuẩn")
    st.markdown("""
    Dưới đây là khung cấu trúc thư viện cốt lõi hỗ trợ thầy/cô tra cứu nhanh theo tổ bộ môn:
    * **SKKN Toán học:** Biện pháp khắc phục sai lầm toán học, mô hình hình học trực quan, STEM toán.
    * **SKKN Khoa học tự nhiên:** Thiết kế hoạt động trải nghiệm, phòng thí nghiệm ảo, học tập dự án.
    * **SKKN Ngữ văn:** Đổi mới kiểm tra đánh giá đọc hiểu, phương pháp dạy học tích hợp văn bản văn học.
    """)
    st.json({
        "Khung cấu trúc SKKN chuẩn": ["Mở đầu", "Nội dung (Cơ sở lý luận, Thực trạng, Biện pháp, Hiệu quả)", "Kết luận và kiến nghị"],
        "Khung cấu trúc NCKHSPƯD chuẩn": ["Khách thể nghiên cứu", "Thiết kế nghiên cứu", "Đo lường & Công cụ thu thập dữ liệu", "Phân tích dữ liệu & Bàn luận kết quả"]
    })
