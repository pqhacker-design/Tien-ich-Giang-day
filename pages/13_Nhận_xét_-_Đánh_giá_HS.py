import streamlit as st
import pandas as pd
from ai_school_evaluator.database.db_manager import DBManager
from ai_school_evaluator.services.rule_engine import RuleEngine
from ai_school_evaluator.services.gemini_service import GeminiService
from ai_school_evaluator.components.dashboard_view import render_dashboard

# Cấu hình giao diện Streamlit hiện đại
st.set_page_config(page_title="AI School Evaluator Pro", page_icon="🎓", layout="wide")

# Khởi tạo các Service hệ thống
db = DBManager()
engine = RuleEngine()

# Quản lý Trạng thái Session
if "api_keys" not in st.session_state:
    st.session_state.api_keys = ["YOUR_DEFAULT_GEMINI_API_KEY"] # Điền Key mặc định nếu có
if "user_role" not in st.session_state:
    st.session_state.user_role = "Giáo viên"

# Giao diện Thanh bên (Sidebar)
with st.sidebar:
    st.title("🎓 AI School Evaluator")
    st.markdown("---")
    
    # Module 14: Phân quyền nhanh trên UI
    st.session_state.user_role = st.selectbox("Vai trò thành viên", ["Giáo viên", "Tổ trưởng", "Hiệu trưởng", "Admin"])
    
    # Module 1: Thông tin lớp học
    st.markdown("### 🏫 Cấu hình lớp học")
    school_level = st.selectbox("Cấp học", ["PRIMARY", "SECONDARY_HIGH"], format_func=lambda x: "Tiểu học (TT 27)" if x=="PRIMARY" else "THCS & THPT (TT 22)")
    school_name = st.text_input("Tên trường", "THPT Chuyên Nguyễn Trãi")
    class_name = st.text_input("Lớp", "10A1")
    subject_name = st.text_input("Môn học", "Toán học")
    
    # Module 15: Cấu hình API Key trực tiếp trên UI
    st.markdown("### 🔑 AI Config")
    user_key = st.text_input("Gemini API Key", type="password", help="Nhập API key của bạn để kích hoạt tính năng AI")
    if user_key:
        st.session_state.api_keys = [user_key]

# Khởi tạo AI Service động từ Key đã nhập
ai_service = GeminiService(st.session_state.api_keys)

# Giao diện chính phân phối Tabs (Layout điều hướng đa nhiệm)
tabs = st.tabs(["📊 Tổng quan lớp học", "👥 Quản lý học sinh & Nhập điểm", "🤖 Trợ lý AI nhận xét"])

with tabs[0]:
    render_dashboard(db.get_connection(), school_level)

with tabs[1]:
    st.markdown("## 👥 Quản lý & Nhập điểm học sinh")
    
    # Tính năng Import dữ liệu nhanh từ Excel/CSV/VnEdu (Giả lập Module 2 & 3)
    uploaded_file = st.file_uploader("Import danh sách học sinh (Excel, CSV, xuất từ vnEdu/SMAS)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            db.import_dataframe(df_upload)
            st.success("🎉 Import dữ liệu học sinh thành công!")
        except Exception as e:
            st.error(f"Lỗi định dạng file import: {e}")
            
    # Hiển thị bảng nhập liệu tương tác trực tiếp dữ liệu hiện tại
    conn = db.get_connection()
    df_students = pd.read_sql_query("SELECT * FROM students", conn)
    
    if not df_students.empty:
        st.markdown("### 📝 Bảng điểm chi tiết")
        edited_df = st.data_editor(df_students, num_rows="dynamic", key="data_editor_students")
        if st.button("💾 Lưu thay đổi điểm số"):
            with db.get_connection() as c:
                edited_df.to_sql("students", c, if_exists="replace", index=False)
            st.success("Đã đồng bộ dữ liệu vào SQLite database!")
    else:
        # Dữ liệu demo để kiểm thử ngay nếu chưa có file import
        if st.button("✨ Khởi tạo dữ liệu mẫu lớp học để test"):
            demo_data = pd.DataFrame([
                {"id": "HS001", "name": "Nguyễn Văn An", "tx_scores": "8,9,8", "gk_score": 8.5, "ck_score": 9.0, "ai_comment": "", "evaluation_level": ""},
                {"id": "HS002", "name": "Trần Thị Bình", "tx_scores": "5,6,5", "gk_score": 5.0, "ck_score": 4.5, "ai_comment": "", "evaluation_level": ""},
                {"id": "HS003", "name": "Lê Hoàng Long", "tx_scores": "7,8,7", "gk_score": 7.5, "ck_score": 8.0, "ai_comment": "", "evaluation_level": ""}
            ])
            with db.get_connection() as c:
                demo_data.to_sql("students", c, if_exists="replace", index=False)
            st.rerun()

with tabs[2]:
    st.markdown("## 🤖 AI Sinh nhận xét tự động cá nhân hóa")
    
    # Bộ điều khiển phong cách viết nhận xét (Module 22)
    col_style, col_action = st.columns([2, 1])
    with col_style:
        style_mode = st.radio("Phong cách viết của AI:", ["Trang trọng", "Tích cực", "Ngắn gọn", "Chi tiết"], horizontal=True)
    
    conn = db.get_connection()
    df_eval = pd.read_sql_query("SELECT * FROM students", conn)
    
    if not df_eval.empty:
        selected_student_id = st.selectbox("Chọn học sinh cần xử lý nhận xét:", df_eval['id'] + " - " + df_eval['name'])
        student_id = selected_student_id.split(" - ")[0]
        student_row = df_eval[df_eval['id'] == student_id].iloc[0]
        
        # Đọc cấu trúc Prompt mẫu
        with open("prompts/comment_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
            
        # Tính toán điểm trung bình động bằng Rule Engine trước khi đưa vào Prompt
        tx_list = [float(i) for i in str(student_row['tx_scores']).split(',') if i.strip() != '']
        final_calculated_score = engine.calculate_average(school_level, tx_list, student_row['gk_score'], student_row['ck_score'])
        suggested_rank = engine.suggest_level(school_level, final_calculated_score)
        
        formatted_prompt = prompt_template.format(
            name=student_row['name'],
            level=school_level,
            tx_scores=student_row['tx_scores'],
            gk_score=student_row['gk_score'],
            ck_score=student_row['ck_score'],
            final_score=final_calculated_score,
            level_eval=suggested_rank,
            style_mode=style_mode
        )
        
        if st.button("🔮 Kích hoạt Gemini Sinh Nhận Xét & Đề xuất biện pháp"):
            with st.spinner("Gemini đang phân tích bảng điểm số học tập..."):
                ai_result = ai_service.generate_response(formatted_prompt)
                
                # Tách phần nhận xét học bạ và phần giải thích sư phạm ẩn
                st.markdown("### 📝 Kết quả nhận xét học bạ đề xuất:")
                st.info(ai_result.split("[GIAI_THICH]")[0])
                
                if "[GIAI_THICH]" in ai_result:
                    with st.expander("🔬 Lý do sư phạm & Minh chứng đánh giá (AI Engine Explained)"):
                        st.write(ai_result.split("[GIAI_THICH]")[1])
                        
                # Cập nhật kết quả ngược lại DB
                with db.get_connection() as c:
                    c.execute("UPDATE students SET ai_comment = ?, evaluation_level = ? WHERE id = ?", (ai_result.split("[GIAI_THICH]")[0], suggested_rank, student_id))
    else:
        st.warning("Vui lòng khởi tạo dữ liệu học sinh ở Tab 2 trước.")
