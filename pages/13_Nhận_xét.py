import streamlit as st
import pandas as pd
import os
from ai_school_evaluator.database.db_manager import DBManager
from ai_school_evaluator.services.rule_engine import RuleEngine
from ai_school_evaluator.services.gemini_service import GeminiService
from ai_school_evaluator.components.dashboard_view import render_dashboard

# 1. Cấu hình trang
st.set_page_config(page_title="AI School Evaluator Pro", page_icon="🎓", layout="wide")

# 2. Khởi tạo Service hệ thống
db = DBManager()
engine = RuleEngine()

# 3. LẤY API KEY AN TOÀN TỪ TRANG CHỦ
current_api_key = st.session_state.get("gemini_api_key") or st.session_state.get("saved_api_key") or ""

# Khởi tạo AI Service an toàn (Lưu vào session_state để tránh khởi tạo lại liên tục)
if "ai_service_instance" not in st.session_state or st.session_state.get("last_used_key") != current_api_key:
    api_keys_list = [current_api_key] if current_api_key else []
    st.session_state.ai_service_instance = GeminiService(api_keys_list)
    st.session_state.last_used_key = current_api_key

ai_service = st.session_state.ai_service_instance

if "user_role" not in st.session_state:
    st.session_state.user_role = "Giáo viên"

# --- Tiêu đề chính ---
st.markdown("## 🎓 13. AI Nhận xét & Đánh giá Học sinh")
st.caption("Ứng dụng phân tích điểm số, tự động tạo nhận xét học bạ cá nhân hóa bám sát Thông tư 27 & Thông tư 22.")

# 4. CẤU HÌNH THÔNG TIN LỚP HỌC
with st.expander("⚙️ CẤU HÌNH THÔNG TIN LỚP HỌC & TÀI KHOẢN", expanded=False):
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
        st.markdown("##### 👤 Vai trò người dùng")
        st.session_state.user_role = st.selectbox("Vai trò", ["Giáo viên", "Tổ trưởng", "Hiệu trưởng", "Admin"])
        
        if current_api_key:
            st.success("🟢 API Key: Đã kết nối từ Trang chủ")
        else:
            st.warning("🔴 API Key: Chưa có (Vui lòng nhập tại Trang chủ)")

if not current_api_key:
    st.warning("⚠️ Bạn chưa nhập Gemini API Key. Hãy quay về **Trang Chủ** nhập API Key để kích hoạt tính năng AI.")
    if st.button("🏠 Đến Trang Chủ nhập API Key"):
        st.switch_page("🏠_Trang_Chủ.py")

st.markdown("---")

# 5. GIAO DIỆN CHÍNH (TABS)
tabs = st.tabs(["📊 1. Tổng quan lớp học", "👥 2. Quản lý học sinh & Nhập điểm", "🤖 3. Trợ lý AI nhận xét"])

# TAB 1: DASHBOARD
with tabs[0]:
    try:
        conn = db.get_connection()
        render_dashboard(conn, school_level)
        conn.close() # Đóng kết nối an toàn
    except Exception as e:
        st.error(f"Lỗi hiển thị bảng điều khiển: {e}")

# TAB 2: QUẢN LÝ HỌC SINH
# --- HÀM CHUẨN HÓA DỮ LIỆU IMPORT TỪ VNEDU / SMAS ---
def process_vnedu_file(uploaded_file):
    """Tự động phát hiện và đọc đúng định dạng file sổ điểm vnEdu/SMAS"""
    file_name = uploaded_file.name.lower()
    
    # 1. Đọc file thô
    if file_name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file, header=None)
    else:
        df_raw = pd.read_excel(uploaded_file, header=None)
        
    # 2. Tìm dòng chứa danh sách học sinh (thường chứa cột Họ tên hoặc Mã học sinh)
    header_idx = None
    for idx, row in df_raw.iterrows():
        row_str = " ".join([str(val) for val in row.values]).lower()
        if "họ" in row_str and "tên" in row_str or "mã học sinh" in row_str or "mã hs" in row_str:
            header_idx = idx
            break
            
    if header_idx is not None:
        # Đọc lại từ dòng tiêu đề thực sự
        uploaded_file.seek(0)
        if file_name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, skiprows=header_idx)
        else:
            df = pd.read_excel(uploaded_file, skiprows=header_idx)
    else:
        # Nếu không tìm thấy dòng tiêu đề đặc trưng, đọc mặc định
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file) if file_name.endswith('.csv') else pd.read_excel(uploaded_file)
        
    # 3. Làm sạch tên cột & lọc bỏ các dòng rỗng/dòng tổng kết
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how='all')
    
    return df

# --- XỬ LÝ TRONG TAB 2 (QUẢN LÝ & NHẬP ĐIỂM) ---
with tabs[1]:
    st.markdown("### 👥 Quản lý & Nhập điểm học sinh")
    
    uploaded_file = st.file_uploader("Import danh sách học sinh (File Excel, CSV xuất từ vnEdu / SMAS)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            # Gọi hàm xử lý tự động lọc bỏ tiêu đề hành chính
            df_upload = process_vnedu_file(uploaded_file)
            
            # Lưu/Đồng bộ vào CSDL
            db.import_dataframe(df_upload)
            st.success(f"🎉 Import thành công dữ liệu từ file {uploaded_file.name}!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi định dạng file import: {e}")
            
    # Lấy dữ liệu an toàn và đóng kết nối ngay
    df_students = pd.DataFrame()
    try:
        conn = db.get_connection()
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()
    except Exception as e:
        st.warning("Chưa thể kết nối CSDL hoặc CSDL rỗng.")

    if not df_students.empty:
        st.markdown("#### 📝 Bảng điểm chi tiết lớp học")
        edited_df = st.data_editor(df_students, num_rows="dynamic", key="data_editor_students")
        if st.button("💾 Lưu thay đổi điểm số", use_container_width=True):
            try:
                conn = db.get_connection()
                edited_df.to_sql("students", conn, if_exists="replace", index=False)
                conn.close()
                st.success("Đã đồng bộ dữ liệu vào CSDL!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi lưu CSDL: {e}")
    else:
        if st.button("✨ Khởi tạo dữ liệu mẫu lớp học để test thử", use_container_width=True):
            try:
                demo_data = pd.DataFrame([
                    {"id": "HS001", "name": "Nguyễn Văn An", "tx_scores": "8,9,8", "gk_score": 8.5, "ck_score": 9.0, "ai_comment": "", "evaluation_level": ""},
                    {"id": "HS002", "name": "Trần Thị Bình", "tx_scores": "5,6,5", "gk_score": 5.0, "ck_score": 4.5, "ai_comment": "", "evaluation_level": ""},
                    {"id": "HS003", "name": "Lê Hoàng Long", "tx_scores": "7,8,7", "gk_score": 7.5, "ck_score": 8.0, "ai_comment": "", "evaluation_level": ""}
                ])
                conn = db.get_connection()
                demo_data.to_sql("students", conn, if_exists="replace", index=False)
                conn.close()
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khởi tạo dữ liệu mẫu: {e}")

# TAB 3: TRỢ LÝ AI
with tabs[2]:
    st.markdown("### 🤖 AI Sinh nhận xét tự động cá nhân hóa")
    
    col_style, _ = st.columns([2, 1])
    with col_style:
        style_mode = st.radio("Phong cách viết nhận xét của AI:", ["Trang trọng", "Tích cực", "Ngắn gọn", "Chi tiết"], horizontal=True)
    
    df_eval = pd.DataFrame()
    try:
        conn = db.get_connection()
        df_eval = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()
    except Exception:
        pass

    if not df_eval.empty:
        student_options = [f"{row['id']} - {row['name']}" for _, row in df_eval.iterrows()]
        selected_student_option = st.selectbox("Chọn học sinh cần sinh nhận xét:", student_options)
        
        student_id = selected_student_option.split(" - ")[0]
        student_row = df_eval[df_eval['id'] == student_id].iloc[0]
        
        # Đọc prompt an toàn
        prompt_template = (
            "Hãy viết nhận xét học tập cho học sinh {name} (Cấp: {level}).\n"
            "Điểm TX: {tx_scores}, Giữa kỳ: {gk_score}, Cuối kỳ: {ck_score}, ĐTB: {final_score}.\n"
            "Xếp loại: {level_eval}. Phong cách: {style_mode}.\n"
            "Yêu cầu: Viết nhận xét khách quan, khích lệ. Sau đó thêm thẻ [GIAI_THICH] giải thích lý do sư phạm."
        )
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.normpath(os.path.join(current_dir, "..", "prompts", "comment_prompt.txt")),
            os.path.normpath(os.path.join(current_dir, "..", "ai_school_evaluator", "prompts", "comment_prompt.txt")),
            os.path.normpath(os.path.join(current_dir, "prompts", "comment_prompt.txt"))
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        prompt_template = f.read()
                    break
                except Exception:
                    pass

        # Xử lý tính toán điểm
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
        except Exception:
            formatted_prompt = f"Viết nhận xét cho học sinh {student_row['name']} đạt điểm trung bình {final_calculated_score} ({suggested_rank})."
        
        if st.button("🔮 Kích hoạt Gemini Sinh Nhận Xét & Đề xuất biện pháp", use_container_width=True):
            if not current_api_key:
                st.error("⚠️ Chưa có API Key! Vui lòng quay về Trang chủ nhập Gemini API Key.")
            else:
                with st.spinner("Gemini đang phân tích bảng điểm..."):
                    try:
                        ai_result = ai_service.generate_response(formatted_prompt)
                        
                        st.markdown("#### 📝 Kết quả nhận xét học bạ đề xuất:")
                        comment_main = ai_result.split("[GIAI_THICH]")[0]
                        st.info(comment_main)
                        
                        if "[GIAI_THICH]" in ai_result:
                            with st.expander("🔬 Lý do sư phạm & Minh chứng đánh giá"):
                                st.write(ai_result.split("[GIAI_THICH]")[1])
                                
                        # Cập nhật DB và đóng ngay
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE students SET ai_comment = ?, evaluation_level = ? WHERE id = ?", (comment_main.strip(), suggested_rank, student_id))
                        conn.commit()
                        conn.close()
                        st.success("Đã ghi nhận xét vào Cơ sở dữ liệu!")
                    except Exception as err:
                        st.error(f"Có lỗi xảy ra trong quá trình xử lý: {err}")
    else:
        st.warning("Vui lòng khởi tạo hoặc import dữ liệu học sinh ở Tab 2 trước.")
