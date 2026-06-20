import streamlit as st
from ai_classroom_game.database.db_manager import DatabaseManager
from ai_classroom_game.services.ai_service import AIService
from ai_classroom_game.modules.interactives import render_lucky_wheel
from ai_classroom_game.services.exporters import DocumentExporter

# 1. Cấu hình trang & Giao diện chuẩn Enterprise
st.set_page_config(page_title="AI Thiết Kế Hoạt Động Lớp Học", layout="wide", initial_sidebar_state="expanded")
db = DatabaseManager()

# Khởi tạo Session State bảo vệ dữ liệu nền
if "generated_quiz" not in st.session_state:
    st.session_state.generated_quiz = None
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

# Nhúng Custom CSS giao diện tối ưu hóa hiển thị cho máy chiếu trường học
st.markdown("""
<style>
    .main .block-container { padding-top: 1.5rem; }
    .stTabs [data-baseweb="tab"] { font-size: 16px; font-weight: bold; padding: 10px 20px; }
    .stTabs [data-baseweb="tab"]:hover { color: #ff4b4b; }
    .stTabs [aria-selected="true"] { background-color: rgba(255,75,75,0.1); border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# 2. THANH THÔNG TIN BỔ TRỢ (SIDEBAR) - CẤU HÌNH TIÊU CHUẨN SƯ PHẠM
with st.sidebar:
    st.image("[https://img.icons8.com/fluent/96/000000/brainstorm-skill.png](https://img.icons8.com/fluent/96/000000/brainstorm-skill.png)", width=80)
    st.title("⚙️ CẤU HÌNH HOẠT ĐỘNG")
    st.markdown("---")
    
    # Form các tham số sư phạm đầu vào
    subject = st.selectbox("Môn học", ["Toán học", "Ngữ văn", "Tiếng Anh", "Khoa học tự nhiên", "Lịch sử & Địa lý", "Tin học", "STEM"])
    grade = st.selectbox("Khối lớp", [f"Lớp {i}" for i in range(1, 13)])
    duration = st.slider("Thời lượng hoạt động (Phút)", 5, 45, 15, step=5)
    difficulty = st.select_slider("Mức độ nhận thức", options=["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"])
    organization = st.radio("Hình thức tổ chức", ["Cá nhân", "Cặp đôi", "Hoạt động nhóm", "Toàn lớp"])
    
    st.markdown("---")
    st.subheader("🔑 Cổng Kết Nối AI Cloud")
    gemini_key = st.text_input("Gemini API Key", type="password", help="Dùng để sinh dữ liệu bài tập và thiết lập kịch bản.")
    openai_key = st.text_input("OpenAI API Key (Fallback)", type="password", help="Tự động kích hoạt khi cổng kết nối Gemini gặp sự cố.")

# Khởi tạo dịch vụ AI dựa trên Key đã nhập
ai_engine = AIService(gemini_key=gemini_key, openai_key=openai_key)

# 3. KHU VỰC ĐIỀU KHIỂN CHÍNH (MAIN DASHBOARD)
st.title("🚀 AI Thiết Kế Hoạt Động Tương Tác Trong Lớp Học")
st.caption("Giải pháp số hóa bài giảng, tạo trò chơi tương tác trực tiếp chuẩn Kahoot/Quizizz cho giáo viên hiện đại.")

# Khởi tạo hệ thống Tab chức năng chuyên sâu
tabs = st.tabs([
    "🎯 Khởi Động & Sinh Hoạt Trình", 
    "📘 Thiết Kế Câu Hỏi AI", 
    "🕹️ Trò Chơi Trực Tiếp", 
    "📑 Kịch Bản Sư Phạm", 
    "📦 Xuất Bản Tài Liệu"
])

# --- TAB 1: KHỞI ĐỘNG ---
with tabs[0]:
    st.header("⚡ Tạo Hoạt Động Khởi Động Sinh Động")
    col1, col2 = st.columns([1, 1])
    with col1:
        warmup_type = st.selectbox("Chọn loại trò chơi khởi động nhanh", [
            "Vòng quay may mắn", "Đuổi hình bắt chữ", "Ai nhanh hơn", "Mật mã bí mật", "Lật mảnh ghép"
        ])
        warmup_prompt = st.text_area("Yêu cầu bổ sung cho trò chơi", placeholder="Ví dụ: Thiết kế trò chơi khởi động liên quan đến kiến thức phân số...")
    with col2:
        if st.button("🔥 Tạo Kịch Bản Trò Chơi", type="primary"):
            if not gemini_key and not openai_key:
                st.error("Vui lòng cung cấp ít nhất một API Key tại Sidebar để kích hoạt AI.")
            else:
                with st.spinner("AI đang thiết kế cấu trúc trò chơi..."):
                    prompt_cmd = f"Tạo kịch bản chi tiết cho trò chơi khởi động '{warmup_type}' dành cho môn {subject}, {grade}. Yêu cầu: {warmup_prompt}. Gồm Luật chơi, Cách tính điểm."
                    res = ai_engine.generate_content(prompt_cmd)
                    st.success("Tạo thành công!")
                    st.markdown(res)

# --- TAB 2: THIẾT KẾ CÂU HỎI AI ---
with tabs[1]:
    st.header("🧠 Hệ Thống Sinh Câu Hỏi Tương Tác Đa Dạng")
    c1, c2 = st.columns([1, 2])
    with c1:
        topic_input = st.text_input("Tên bài học học tập", placeholder="Ví dụ: Định lý Pitago")
        goals_input = st.text_input("Mục tiêu cần đạt", placeholder="Ví dụ: Học sinh vận dụng tính cạnh huyền")
        content_input = st.text_area("Nội dung cốt lõi/Tóm tắt tài liệu", placeholder="Nhập nội dung bài học để AI bám sát...")
        
        generate_btn = st.button("✨ Kích hoạt Trí Tuệ Nhân Tạo", type="primary")
        
    with c2:
        if generate_btn:
            if not (topic_input and content_input):
                st.warning("Vui lòng nhập đầy đủ Tên bài và Nội dung cốt lõi.")
            else:
                with st.spinner("Hệ thống đang bóc tách nội dung và sinh bộ câu hỏi..."):
                    try:
                        quiz_res = ai_engine.generate_quiz(topic_input, content_input, goals_input)
                        st.session_state.generated_quiz = quiz_res
                        st.session_state.current_topic = topic_input
                        db.save_history(subject, grade, topic_input, "Quiz Tổng Hợp", quiz_res)
                    except Exception as err:
                        st.error(f"Lỗi hệ thống: {err}")
                        
        if st.session_state.generated_quiz:
            st.success(f"Dữ liệu bộ câu hỏi chuẩn hóa cho bài học: {st.session_state.current_topic}")
            q_data = st.session_state.generated_quiz
            
            # Hiển thị trực quan dữ liệu trắc nghiệm thu được từ AI
            if "trac_nghiem" in q_data:
                for idx, t in enumerate(q_data["trac_nghiem"]):
                    with st.expander(f"🔹 Câu hỏi trắc nghiệm {idx+1}: {t['cau_hoi']}"):
                        st.write(f"**Các phương án chọn:** {', '.join(t['options'])}")
                        st.info(f"✔ **Đáp án:** {t['dap_an']} | **Giải thích:** {t['giai_thich']}")

# --- TAB 3: TRÒ CHƠI TƯƠNG TÁC TRỰC TIẾP (BẢNG TRÌNH CHIẾU LỚP HỌC) ---
with tabs[2]:
    st.header("🎬 Đấu Trường Tương Tác Thời Gian Thực")
    st.info("Mẹo: Giáo viên nhấn F11 để toàn màn hình trình duyệt khi chiếu cho học sinh chơi trực tiếp tại lớp.")
    
    game_select = st.selectbox("Lựa chọn Game Engine vận hành", ["Vòng Quay May Mắn", "Ô Chữ Kỳ Diệu", "Ai Là Triệu Phú"])
    
    if game_select == "Vòng Quay May Mắn":
        col_g1, col_g2 = st.columns([1, 3])
        with col_g1:
            st.markdown("### 📋 Thiết lập phòng đấu")
            students_raw = st.text_area("Danh sách học sinh (Mỗi người một hàng)", "Nguyễn Văn A\nTrần Thị B\nLê Hoàng C\nPhạm Minh D\nĐỗ Hồng E")
            students_list = [s.strip() for s in students_raw.split("\n") if s.strip()]
            
            # Đồng bộ câu hỏi từ Tab 2 sang nếu có
            if st.session_state.generated_quiz and "trac_nghiem" in st.session_state.generated_quiz:
                q_list = [q['cau_hoi'] for q in st.session_state.generated_quiz['trac_nghiem']]
            else:
                q_list = ["Chủ đề 1: Trả bài cũ", "Chủ đề 2: Giải toán nhanh", "Chủ đề 3: Câu hỏi may mắn"]
        with col_g2:
            render_lucky_wheel(students_list, q_list)

# --- TAB 4: KỊCH BẢN SƯ PHẠM ---
with tabs[3]:
    st.header("📋 Khung Kịch Bản Bài Giảng Sư Phạm Cao Cấp")
    framework_type = st.selectbox("Chọn mô hình thiết kế", ["Mô hình 5E (Engage - Explore - Explain - Elaborate - Evaluate)", "Phương pháp giáo dục STEM/STEAM Integration", "Phát triển năng lực số"])
    if st.button("🛠 Sinh kịch bản sư phạm tổng thể"):
        if not st.session_state.current_topic:
            st.warning("Vui lòng qua Tab 'Thiết Kế Câu Hỏi AI' để tạo chủ đề bài học trước.")
        else:
            with st.spinner("AI đang biên soạn kịch bản chi tiết..."):
                script_prompt = f"Viết kịch bản dạy học chuẩn sư phạm cho bài học {st.session_state.current_topic} dựa trên {framework_type} cho học sinh {grade}."
                script_res = ai_engine.generate_content(script_prompt)
                st.markdown(script_res)

# --- TAB 5: XUẤT BẢN TÀI LIỆU ---
with tabs[4]:
    st.header("💾 Xuất Bản Học Liệu Số")
    if st.session_state.generated_quiz:
        st.write(f"Học liệu hiện hành sẵn có cho bài học: **{st.session_state.current_topic}**")
        
        c_down1, c_down2 = st.columns(2)
        with c_down1:
            docx_file = DocumentExporter.export_to_docx(st.session_state.current_topic, st.session_state.generated_quiz)
            st.download_button(
                label="📥 Tải xuống Giáo án Word (.docx)",
                data=docx_file,
                file_name=f"Giao_an_AI_{st.session_state.current_topic}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        with c_down2:
            pptx_file = DocumentExporter.export_to_pptx(st.session_state.current_topic, st.session_state.generated_quiz)
            st.download_button(
                label="📥 Tải xuống Slide Trình Chiếu (.pptx)",
                data=pptx_file,
                file_name=f"Slide_Game_{st.session_state.current_topic}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
    else:
        st.info("Chưa có dữ liệu học liệu được tạo từ AI. Hãy hoàn tất tạo câu hỏi ở Tab 2 để tiến hành xuất file.")

