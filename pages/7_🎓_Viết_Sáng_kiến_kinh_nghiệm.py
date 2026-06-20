import streamlit as st
import os
import sys

# Tự động cấu hình sys.path để nhận diện các module ở thư mục cha nếu chạy trong thư mục pages/
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import trực tiếp từ thư mục gốc hoặc qua gói components nội bộ
try:
    from database import init_db, save_project, get_all_projects
    from ai_engine import call_ai_stream, get_council_critique
    from components.generator import show_generator_module
    from components.content_writer import show_content_writer_module
    from components.data_analysis import show_data_analysis_module
    from components.docx_processor import show_docx_processor_module
    from components.library import show_library_module
    from components.evidence_creator import show_evidence_creator_module
except ModuleNotFoundError:
    # Dự phòng nếu thầy bọc dự án trong gói edu_research_assistant
    from edu_research_assistant.database import init_db, save_project, get_all_projects
    from edu_research_assistant.ai_engine import call_ai_stream, get_council_critique
    from edu_research_assistant.components.generator import show_generator_module
    from edu_research_assistant.components.content_writer import show_content_writer_module
    from edu_research_assistant.components.data_analysis import show_data_analysis_module
    from edu_research_assistant.components.docx_processor import show_docx_processor_module
    from edu_research_assistant.components.library import show_library_module
    from edu_research_assistant.components.evidence_creator import show_evidence_creator_module

# Cấu hình Page cấu trúc hiện đại
st.set_page_config(
    page_title="Hệ thống Trợ lý Hồ sơ Khoa học Giáo dục AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🔑 LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    user_api_key = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.stop()

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
    try:
        projects = get_all_projects()
        if projects:
            for p in projects:
                st.info(f"ID: {p[0]} - Đề tài: **{p[1]}** - Bộ môn: {p[2]} ({p[3]})")
        else:
            st.write("Chưa có dự án nào được lưu. Hãy bắt đầu tạo đề tài tại thanh điều hướng bên trái.")
    except Exception as e:
        st.error(f"Không thể kết nối cơ sở dữ liệu: {e}")

elif menu == "💡 I. Tạo Đề tài Thông minh":
    show_generator_module()

elif menu == "📝 II & III. Thiết kế Đề cương & Viết nội dung":
    show_content_writer_module()

elif menu == "📊 IV & XI. Xử lý Thống kê & Sinh Minh chứng":
    show_data_analysis_module()
    st.markdown("---")
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
    show_library_module()
