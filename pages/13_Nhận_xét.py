import streamlit as st
import pandas as pd
import os
import re
from ai_school_evaluator.database.db_manager import DBManager
from ai_school_evaluator.services.rule_engine import RuleEngine
from ai_school_evaluator.services.gemini_service import GeminiService
from ai_school_evaluator.components.dashboard_view import render_dashboard

# 1. Cấu hình trang Streamlit
st.set_page_config(page_title="AI School Evaluator Pro", page_icon="🎓", layout="wide")

# 2. Khởi tạo Service
db = DBManager()
engine = RuleEngine()

# 3. LẤY API KEY TRỰC TIẾP TỪ TRANG CHỦ
current_api_key = st.session_state.get("gemini_api_key") or st.session_state.get("saved_api_key") or ""

if "ai_service_instance" not in st.session_state or st.session_state.get("last_used_key") != current_api_key:
    api_keys_list = [current_api_key] if current_api_key else []
    st.session_state.ai_service_instance = GeminiService(api_keys_list)
    st.session_state.last_used_key = current_api_key

ai_service = st.session_state.ai_service_instance

# --- Tiêu đề ứng dụng ---
st.markdown("## 🎓 13. AI Nhận xét & Đánh giá Học sinh")
st.caption("Ứng dụng phân tích điểm số, tự động tạo nhận xét học bạ cá nhân hóa bám sát Thông tư 27 & Thông tư 22.")

# 4. KHU VỰC CẤU HÌNH GIAO DIỆN CHÍNH
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
        st.markdown("##### 👤 Vai trò & Kết nối AI")
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

# --- HÀM XỬ LÝ & CHUẨN HÓA DỮ LIỆU VNEDU / EXCEL ---
def parse_vnedu_file(uploaded_file):
    file_name = uploaded_file.name.lower()
    
    # Đọc file thô không header
    if file_name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file, header=None)
    else:
        df_raw = pd.read_excel(uploaded_file, header=None)
        
    # Tìm dòng chứa thông tin cột (thường chứa 'mã học sinh' hoặc 'họ' và 'tên')
    header_row_idx = None
    for idx, row in df_raw.iterrows():
        row_str = " ".join([str(v) for v in row.values]).lower()
        if ("mã" in row_str and "học sinh" in row_str) or ("họ" in row_str and "tên" in row_str):
            header_row_idx = idx
            break
            
    uploaded_file.seek(0)
    if header_row_idx is not None:
        df = pd.read_csv(uploaded_file, skiprows=header_row_idx) if file_name.endswith('.csv') else pd.read_excel(uploaded_file, skiprows=header_row_idx)
    else:
        df = pd.read_csv(uploaded_file) if file_name.endswith('.csv') else pd.read_excel(uploaded_file)

    # Làm sạch tên cột
    df.columns = [str(c).strip() for c in df.columns]
    
    # Tìm và map tên cột chính xác về chuẩn CSDL (id, name, tx_scores, gk_score, ck_score)
    col_map = {}
    tx_cols = []
    
    for c in df.columns:
        c_lower = c.lower()
        if "mã" in c_lower or "id" in c_lower:
            col_map[c] = "id"
        elif "họ" in c_lower and "tên" in c_lower or "name" in c_lower:
            col_map[c] = "name"
        elif "tx" in c_lower or "đgtx" in c_lower or "thường xuyên" in c_lower:
            tx_cols.append(c)
        elif "gk" in c_lower or "giữa kỳ" in c_lower or "ddggk" in c_lower:
            col_map[c] = "gk_score"
        elif "ck" in c_lower or "cuối kỳ" in c_lower or "ddgck" in c_lower:
            col_map[c] = "ck_score"

    df = df.rename(columns=col_map)
    
    # Gộp các cột điểm thường xuyên thành chuỗi cách nhau bởi dấu phẩy
    if tx_cols:
        def merge_tx(row):
            vals = [str(row[c]).strip() for c in tx_cols if pd.notnull(row[c]) and str(row[c]).strip() not in ['', 'nan']]
            return ",".join(vals)
        df['tx_scores'] = df.apply(merge_tx, axis=1)
    elif 'tx_scores' not in df.columns:
        df['tx_scores'] = ""

    # Bổ sung các cột bắt buộc nếu thiếu
    for req_col in ['id', 'name', 'gk_score', 'ck_score', 'ai_comment', 'evaluation_level']:
        if req_col not in df.columns:
            df[req_col] = ""

    # Nếu không tìm thấy ID, tự sinh ID
    if df['id'].astype(str).str.strip().eq("").all():
        df['id'] = [f"HS{i+1:03d}" for i in range(len(df))]

    # Giữ đúng các cột định dạng chuẩn của CSDL
    final_cols = ['id', 'name', 'tx_scores', 'gk_score', 'ck_score', 'ai_comment', 'evaluation_level']
    df_result = df[final_cols].copy()
    df_result = df_result.dropna(subset=['name']) # Bỏ các dòng rỗng tên
    return df_result

# 5. ĐIỀU HƯỚNG TABS
tabs = st.tabs(["📊 1. Tổng quan lớp học", "👥 2. Quản lý học sinh & Nhập điểm", "🤖 3. Trợ lý AI nhận xét"])

# TAB 1: DASHBOARD
with tabs[0]:
    try:
        conn = db.get_connection()
        render_dashboard(conn, school_level)
        conn.close()
    except Exception as e:
        st.info("Nhập hoặc khởi tạo dữ liệu ở Tab 2 để hiển thị thống kê.")

# TAB 2: QUẢN LÝ HỌC SINH
with tabs[1]:
    st.markdown("### 👥 Quản lý & Nhập điểm học sinh")
    
    uploaded_file = st.file_uploader("Import danh sách học sinh (File Excel/CSV từ vnEdu/SMAS)", type=["csv", "xlsx"])
    if uploaded_file:
        try:
            df_standardized = parse_vnedu_file(uploaded_file)
            conn = db.get_connection()
            df_standardized.to_sql("students", conn, if_exists="replace", index=False)
            conn.close()
            st.success(f"🎉 Import và chuẩn hóa thành công {len(df_standardized)} học sinh từ file!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi đọc file: {e}")
            
    # Hiển thị bảng dữ liệu
    df_students = pd.DataFrame()
    try:
        conn = db.get_connection()
        df_students = pd.read_sql_query("SELECT * FROM students", conn)
        conn.close()
    except Exception:
        pass

    if not df_students.empty:
        st.markdown("#### 📝 Bảng điểm chi tiết lớp học")
        edited_df = st.data_editor(df_students, num_rows="dynamic", key="data_editor_students")
        if st.button("💾 Lưu thay đổi điểm số", use_container_width=True):
            try:
                conn = db.get_connection()
                edited_df.to_sql("students", conn, if_exists="replace", index=False)
                conn.close()
                st.success("Đã lưu thay đổi vào CSDL!")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi lưu: {e}")
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
                st.error(f"Lỗi khởi tạo: {e}")

# TAB 3: AI NHẬN XÉT
with tabs[2]:
    st.markdown("### 🤖 AI Sinh nhận xét tự động cá nhân hóa")
    
    col_style, _ = st.columns([2, 1])
    with col_style:
        style_mode = st.radio("Phong cách viết nhận xét:", ["Trang trọng", "Tích cực", "Ngắn gọn", "Chi tiết"], horizontal=True)
    
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

        # Tính toán điểm trung bình
        tx_raw = str(student_row['tx_scores']) if pd.notnull(student_row['tx_scores']) else ""
        tx_list = [float(i.strip()) for i in tx_raw.split(',') if i.strip() != '' and i.strip().replace('.','',1).isdigit()]
        
        gk_val = float(student_row['gk_score']) if pd.notnull(student_row['gk_score']) and str(student_row['gk_score']).replace('.','',1).isdigit() else None
        ck_val = float(student_row['ck_score']) if pd.notnull(student_row['ck_score']) and str(student_row['ck_score']).replace('.','',1).isdigit() else None
        
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
                                
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE students SET ai_comment = ?, evaluation_level = ? WHERE id = ?", (comment_main.strip(), suggested_rank, student_id))
                        conn.commit()
                        conn.close()
                        st.success("Đã ghi nhận xét vào Cơ sở dữ liệu!")
                    except Exception as err:
                        st.error(f"Có lỗi trong quá trình sinh nhận xét: {err}")
    else:
        st.warning("Vui lòng khởi tạo hoặc import dữ liệu học sinh ở Tab 2 trước.")
