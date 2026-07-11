import streamlit as st
import pandas as pd
import os
from ai_school_evaluator.database.db_manager import DBManager
from ai_school_evaluator.services.rule_engine import RuleEngine
from ai_school_evaluator.services.gemini_service import GeminiService
from ai_school_evaluator.components.dashboard_view import render_dashboard

# 1. Cấu hình trang Streamlit
st.set_page_config(page_title="AI School Evaluator Pro", page_icon="🎓", layout="wide")

# 2. Khởi tạo các Service hệ thống
db = DBManager()
engine = RuleEngine()

# 3. LẤY & ĐỒNG BỘ API KEY TỪ TRANG CHỦ (session_state)
if "saved_api_key" not in st.session_state:
    st.session_state["saved_api_key"] = ""

# Ưu tiên lấy API key đã lưu ở trang chủ
shared_api_key = st.session_state.get("gemini_api_key") or st.session_state.get("saved_api_key") or ""

if "user_role" not in st.session_state:
    st.session_state.user_role = "Giáo viên"

# --- Tiêu đề chính của ứng dụng ---
st.markdown("## 🎓 13. AI Nhận xét & Đánh giá Học sinh")
st.caption("Ứng dụng phân tích điểm số, tự động tạo nhận xét học bạ cá nhân hóa bám sát Thông tư 27 (Tiểu học) & Thông tư 22 (THCS/THPT).")

# 4. CHUYỂN TOÀN BỘ CẤU HÌNH TỪ SIDEBAR VÀO GIAO DIỆN CHÍNH (EXPANDER)
with st.expander("⚙️ CẤU HÌNH HỆ THỐNG & THÔNG TIN LỚP HỌC", expanded=False):
    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    
    with col_cfg1:
        st.markdown("##### 🏫 Thông tin lớp học")
        school_level = st.selectbox(
            "Cấp học", 
            ["PRIMARY", "SECONDARY_HIGH"], 
            format_func=lambda x: "Tiểu học (TT 27/2020)" if x == "PRIMARY" else "THCS & THPT (TT 22/2021)"
        )
        school_name = st.text_input("Tên trường", "THPT Chuyên Nguyễn Trãi")

    with col_cfg2:
        st.markdown("##### 📚 Chi tiết môn học")
        class_name = st.text_input("Lớp", "10A1")
        subject_name = st.text_input("Môn học", "Toán học")

    with col_cfg3:
        st.markdown("##### 👤 Tải khoản & AI Config")
        st.session_state.user_role = st.selectbox("Vai trò người dùng", ["Giáo viên", "Tổ trưởng", "Hiệu trưởng", "Admin"])
        
        # Ô nhập API Key đồng bộ 2 chiều với Trang chủ
        user_key = st.text_input(
            "Gemini API Key (Dùng chung toàn hệ thống)", 
            value=shared_api_key, 
            type="password", 
            help="API Key được tự động lấy từ Trang chủ. Bạn có thể thay đổi tại đây."
        )
        if user_key != shared_api_key:
            st.session_state["saved_api_key"] = user_key
            st.session_state["gemini_api_key"] = user_key
            st.success("✔️ Đã cập nhật API Key cho toàn bộ hệ thống!")

# Lấy key hiện tại để khởi tạo AI Service
current_api_key = st.session_state.get("gemini_api_key") or st.session_state.get("saved_api_key") or ""
ai_service = GeminiService([current_api_key] if current_api_key else [])

st.markdown("---")

# 5. GIAO DIỆN CHÍNH (ĐIỀU HƯỚNG TABS)
tabs = st.tabs(["📊 1. Tổng quan lớp học", "👥 2. Quản lý học sinh & Nhập điểm", "🤖 3. Trợ lý AI nhận xét"])

# TAB 1: DASHBOARD THỐNG KÊ
with tabs[0]:
    render_dashboard(db.get_connection(), school_level)

# TAB 2: QUẢN LÝ & NHẬP ĐIỂM HỌC SINH
with tabs[1]:
    st.markdown("### 👥 Quản lý & Nhập điểm học sinh")
    
    # Import dữ liệu từ Excel / CSV
    uploaded_file = st.file_uploader("Import danh sách học sinh (File Excel, CSV xuất từ vnEdu / SMAS)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            db.import_dataframe(df_upload)
            st.success("🎉 Import dữ liệu học sinh thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi định dạng file import: {e}")
            
    # Hiển thị bảng nhập liệu tương tác
    conn = db.get_connection()
    df_students = pd.read_sql_query("SELECT * FROM students", conn)
    
    if not df_students.empty:
        st.markdown("#### 📝 Bảng điểm chi tiết lớp học")
        edited_df = st.data_editor(df_students, num_rows="dynamic", key="data_editor_students")
        if st.button("💾 Lưu thay đổi điểm số", use_container_width=True):
            with db.get_connection() as c:
                edited_df.to_sql("students", c, if_exists="replace", index=False)
            st.success("Đã đồng bộ dữ liệu vào CSDL!")
            st.rerun()
    else:
        if st.button("✨ Khởi tạo dữ liệu mẫu lớp học để test thử", use_container_width=True):
            demo_data = pd.DataFrame([
                {"id": "HS001", "name": "Nguyễn Văn An", "tx_scores": "8,9,8", "gk_score": 8.5, "ck_score": 9.0, "ai_comment": "", "evaluation_level": ""},
                {"id": "HS002", "name": "Trần Thị Bình", "tx_scores": "5,6,5", "gk_score": 5.0, "ck_score": 4.5, "ai_comment": "", "evaluation_level": ""},
                {"id": "HS003", "name": "Lê Hoàng Long", "tx_scores": "7,8,7", "gk_score": 7.5, "ck_score": 8.0, "ai_comment": "", "evaluation_level": ""}
            ])
            with db.get_connection() as c:
                demo_data.to_sql("students", c, if_exists="replace", index=False)
            st.rerun()

# TAB 3: TRỢ LÝ AI SINH NHẬN XÉT
with tabs[2]:
    st.markdown("### 🤖 AI Sinh nhận xét tự động cá nhân hóa")
    
    # Cấu hình phong cách viết
    col_style, _ = st.columns([2, 1])
    with col_style:
        style_mode = st.radio("Phong cách viết nhận xét của AI:", ["Trang trọng", "Tích cực", "Ngắn gọn", "Chi tiết"], horizontal=True)
    
    conn = db.get_connection()
    df_eval = pd.read_sql_query("SELECT * FROM students", conn)
    
    if not df_eval.empty:
        student_options = [f"{row['id']} - {row['name']}" for _, row in df_eval.iterrows()]
        selected_student_option = st.selectbox("Chọn học sinh cần sinh nhận xét:", student_options)
        
        student_id = selected_student_option.split(" - ")[0]
        student_row = df_eval[df_eval['id'] == student_id].iloc[0]
        
        # --- XỬ LÝ ĐƯỜNG DẪN PROMPT AN TOÀN ---
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.normpath(os.path.join(current_dir, "..", "prompts", "comment_prompt.txt")),
            os.path.normpath(os.path.join(current_dir, "..", "ai_school_evaluator", "prompts", "comment_prompt.txt")),
            os.path.normpath(os.path.join(current_dir, "prompts", "comment_prompt.txt")),
            "prompts/comment_prompt.txt"
        ]
        
        prompt_template = None
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        prompt_template = f.read()
                    break
                except Exception:
                    pass
        
        # Prompt dự phòng nếu không tìm thấy file
        if not prompt_template:
            prompt_template = (
                "Hãy viết nhận xét học tập cho học sinh {name} (Cấp: {level}).\n"
                "Điểm TX: {tx_scores}, Giữa kỳ: {gk_score}, Cuối kỳ: {ck_score}, ĐTB: {final_score}.\n"
                "Xếp loại: {level_eval}. Phong cách: {style_mode}.\n"
                "Yêu cầu: Viết nhận xét khách quan, khích lệ. Sau đó thêm thẻ [GIAI_THICH] giải thích lý do sư phạm."
            )
            
        # Xử lý tính toán điểm trung bình
        tx_raw = str(student_row['tx_scores']) if pd.notnull(student_row['tx_scores']) else ""
        tx_list = [float(i.strip()) for i in tx_raw.split(',') if i.strip() != '' and i.strip().replace('.','',1).isdigit()]
        
        gk_val = float(student_row['gk_score']) if pd.notnull(student_row['gk_score']) else None
        ck_val = float(student_row['ck_score']) if pd.notnull(student_row['ck_score']) else None
        
        final_calculated_score = engine.calculate_average(school_level, tx_list, gk_val, ck_val)
        suggested_rank = engine.suggest_level(school_level, final_calculated_score)
        
        try:
            formatted_prompt = prompt_template.format(
                name=student_row['name'],
                level=school_level,
                tx_scores=tx_raw,
                gk_score=gk_val if gk_val is not None else "Chưa có",
                ck_score=ck_val if ck_val is not None else "Chưa có",
                final_score=final_calculated_score,
                level_eval=suggested_rank,
                style_mode=style_mode
            )
        except Exception as e:
            formatted_prompt = f"Viết nhận xét cho học sinh {student_row['name']} đạt điểm trung bình {final_calculated_score} ({suggested_rank})."
        
        if st.button("🔮 Kích hoạt Gemini Sinh Nhận Xét & Đề xuất biện pháp", use_container_width=True):
            if not current_api_key:
                st.error("⚠️ Chưa có API Key! Vui lòng nhập Gemini API Key ở phần Cấu hình đầu trang hoặc ở Trang chủ.")
            else:
                with st.spinner("Gemini đang phân tích bảng điểm số học tập..."):
                    ai_result = ai_service.generate_response(formatted_prompt)
                    
                    st.markdown("#### 📝 Kết quả nhận xét học bạ đề xuất:")
                    comment_main = ai_result.split("[GIAI_THICH]")[0]
                    st.info(comment_main)
                    
                    if "[GIAI_THICH]" in ai_result:
                        with st.expander("🔬 Lý do sư phạm & Minh chứng đánh giá (AI Engine Explained)"):
                            st.write(ai_result.split("[GIAI_THICH]")[1])
                            
                    with db.get_connection() as c:
                        cursor = c.cursor()
                        cursor.execute("UPDATE students SET ai_comment = ?, evaluation_level = ? WHERE id = ?", (comment_main.strip(), suggested_rank, student_id))
                        c.commit()
                    st.success("Đã ghi nhận xét vào Cơ sở dữ liệu!")
    else:
        st.warning("Vui lòng khởi tạo hoặc import dữ liệu học sinh ở Tab 2 trước.")
