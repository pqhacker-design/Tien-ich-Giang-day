import streamlit as st
import json
import sqlite3
from datetime import datetime

# Import các mô-đun nghiệp vụ đã xây dựng
from modules.doc_reader import read_docx, read_pdf, analyze_metadata
from modules.digital_competency import get_digital_competency_framework
from modules.lesson_ai import generate_lesson_plan_ai
from modules.cv5512_generator import format_html_preview
from modules.rubric_generator import generate_matrices
from modules.worksheet_generator import generate_digital_worksheet
from modules.word_export import export_lesson_to_word

# 1. Đoạn CSS tùy chỉnh màu sắc cho st.page_link
st.markdown(
    """
    <style>
    /* Tuỳ chỉnh kiểu dáng cho tất cả các nút st.page_link */
    div[data-testid="stPageLink"] a {
        background-color: #0284C7 !important; /* Màu nền (Xanh dương) */
        color: white !important;              /* Màu chữ */
        border-radius: 8px !important;         /* Bo góc */
        padding: 8px 16px !important;          /* Khoảng cách lề trong */
        text-decoration: none !important;      /* Bỏ gạch chân */
        font-weight: bold !important;          /* Chữ in đậm */
        border: 1px solid #0369A1 !important;  /* Màu viền */
        display: inline-flex !important;
        align-items: center !important;
        transition: all 0.3s ease !important;  /* Hiệu ứng chuyển mượt */
    }

    /* Hiệu ứng khi rê chuột (Hover) vào nút */
    div[data-testid="stPageLink"] a:hover {
        background-color: #0369A1 !important; /* Màu nền đậm hơn khi hover */
        color: #F0F9FF !important;              /* Màu chữ khi hover */
        border-color: #075985 !important;
        transform: translateY(-2px);           /* Hiệu ứng nổi nhẹ */
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Cấu hình cài đặt trang giao diện Streamlit tiên tiến
st.set_page_config(
    page_title="AI KHBD Thông Minh 4.0",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown(
    """
    <style>
        /* Nhắm mục tiêu vào văn bản bên trong các nút Tab của Streamlit */
        button[data-baseweb="tab"] div p {
            font-weight: bold !important;
            font-size: 1.05em !important; /* Có thể phóng to chữ lên một chút nếu muốn */
        }
    </style>
    """,
    unsafe_allow_html=True
)
# Khởi tạo Cơ sở dữ liệu SQLite cục bộ để lưu trữ lịch sử soạn giáo án của giáo viên
conn = sqlite3.connect('lessons_history.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS history 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, topic TEXT, subject TEXT, grade TEXT, content TEXT)''')
conn.commit()

# --- Thân Giao Diện Chính Ứng Dụng ---
st.markdown("## 🚀 Soạn KHBD tự động theo 5512")
st.info("Giúp GV soạn KHBD theo công văn 5512 có tích hợp năng lực số.")

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    # Nếu chưa nhập key ở trang chủ, hiển thị thông báo nhắc nhở và dừng app con lại
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="**Nhấn vào đây để Quay lại Trang chủ**", icon="🔄")
    st.stop() # Dừng không chạy các đoạn code phía dưới để tránh lỗi crash

# --- CẤU HÌNH NHẬN DIỆN BÀI DẠY (ĐƯỢC ĐƯA LÊN TRANG CHÍNH) ---
with st.expander("⚙️ **CẤU HÌNH NHẬN DIỆN BÀI DẠY**", expanded=False):
    col_sub, col_grd, col_dur = st.columns(3)
    
    with col_sub:
        subject_select = st.text_input("**Môn học giáo viên giảng dạy:**", value="Toán học")
    with col_grd:
        grade_select = st.selectbox("**Khối lớp áp dụng:**", [f"Lớp {i}" for i in range(1, 13)], index=7)
    with col_dur:
        duration_select = st.text_input("**Thời lượng tiết dạy:**", value="2 Tiết")
# Bổ sung tùy chọn định dạng giáo án
        lesson_format = st.radio(
            "**Định dạng Tiến trình dạy học (Mục III):**",
            options=["Loại thường (Không chia cột)", "Loại 2 cột (Hoạt động của GV & HS | Nội dung)", "Loại 3 cột (Tiến trình | Hoạt động của GV & HS | Nội dung)"],
            index=0,
            horizontal=True
        )
    # Xác định cấp học tự động phục vụ cấu hình phân phối năng lực số thích ứng
    grade_num = int(''.join(filter(str.isdigit, grade_select)))
    if grade_num <= 5: 
        level_detected = "Tiểu học"
    elif grade_num <= 9: 
        level_detected = "THCS"
    else: 
        level_detected = "THPT"

    st.info(f"Hệ thống tự động kích hoạt Khung năng lực số cấp: **{level_detected}**")

st.write("**Tải KHBD cũ (.docx, .pdf) hoặc nhập văn bản thô để AI tự động chuyển đổi số hóa hành chính học tập.**")
# Thiết kế Tab phân vùng các tính năng xử lý đầu vào dữ liệu khác nhau
tab_upload, tab_direct, tab_history = st.tabs(["**| 📂 Chuẩn hóa KHBD từ KHBD đã có**", "**| 📝 Tạo KHBD bất kì theo yêu cầu**", "**| 📜 Lịch sử soạn thảo số**"])

raw_input_text = ""

with tab_upload:
    uploaded_file = st.file_uploader("**Kéo và thả file Word (.docx) hoặc tài liệu PDF của KHBD cũ vào đây:**", type=["docx", "pdf"])
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        if uploaded_file.name.endswith(".docx"):
            raw_input_text = read_docx(file_bytes)
        elif uploaded_file.name.endswith(".pdf"):
            raw_input_text = read_pdf(file_bytes)
            
        st.success(f"Đọc thành công file: {uploaded_file.name}. Hệ thống đã nạp nội dung thô phân tích.")
        with st.expander("Xem trước dữ liệu văn bản thô trích xuất từ file"):
            st.text_area("Nội dung gốc đọc được:", value=raw_input_text, height=150, disabled=True)

with tab_direct:
    direct_text = st.text_area("**Nếu không tải file, hãy copy nội dung bài dạy hoặc chuỗi ý tưởng bài dạy vào đây:**", height=100, 
                               placeholder="Ví dụ: Bài 3: Khái niệm liên kết hóa học hóa học lớp 10, thời lượng 2 tiết...")
    if direct_text:
        raw_input_text = direct_text

with tab_history:
    st.markdown("### Nhật ký các KHBD đã tạo trên hệ thống máy tính giáo viên")
    history_data = c.execute("SELECT id, time, topic, subject, grade FROM history ORDER BY id DESC").fetchall()
    if history_data:
        for item in history_data:
            if st.button(f"🔄 Khôi phục: {item[2]} ({item[3]} - {item[4]}) | Tạo lúc: {item[1]}", key=f"hist_{item[0]}"):
                stored_content = c.execute("SELECT content FROM history WHERE id=?", (item[0],)).fetchone()[0]
                st.session_state["processed_json"] = json.loads(stored_content)
                st.success("Đã khôi phục dữ liệu KHBD thành công từ SQLite nội bộ! Hãy chuyển qua xem kết quả biên soạn.")
    else:
        st.write("Chưa có lịch sử KHBD nào được lưu trữ cục bộ.")

# Nút lệnh cốt lõi kích hoạt AI điều phối hoạt động chuyển dịch cấu trúc giáo án số
if st.button("🔥 KÍCH HOẠT TRỢ LÝ AI BIÊN SOẠN KHBD 4.0", type="primary", use_container_width=True):
    if not raw_input_text.strip():
        st.warning("Cảnh báo nghiệp vụ: Chưa có dữ liệu đầu vào. Vui lòng tải file KHBD cũ hoặc nhập nội dung ý tưởng bài học.")
    else:
        with st.spinner("Trợ lý AI đang phân tích chuỗi sư phạm, đồng bộ hóa Công văn 5512 và tích hợp Khung năng lực số..."):
            my_bar = st.progress(10)
            
            # Cấu hình Metadata định danh và khung năng lực thích ứng tương thích cấp học
            meta_config = {
                "subject": subject_select,
                "grade": grade_select,
                "level": level_detected,
                "duration": duration_select,
                "topic": "Bài học phát triển số"
            }
            
            framework = get_digital_competency_framework(level_detected)
            my_bar.progress(40)
            
            # Thực thi tác vụ gọi AI Gemini Pro sử dụng biến api_key_input đồng bộ
            result_json = generate_lesson_plan_ai(api_key_input, raw_input_text, meta_config, framework)
            my_bar.progress(80)
            
            if "error" in result_json:
                st.error(result_json["error"])
                if "raw_response" in result_json:
                    st.text_area("Dữ liệu phản hồi thô lỗi:", value=result_json["raw_response"], height=200)
            else:
                st.session_state["processed_json"] = result_json
                
                # Lưu trữ bản ghi vào Database cục bộ SQLite bảo mật thông tin
                topic_name = result_json.get("thong_tin_chung", {}).get("ten_bai_hoc", "Chưa rõ tên bài")
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT INTO history (time, topic, subject, grade, content) VALUES (?, ?, ?, ?, ?)",
                          (now_str, topic_name, subject_select, grade_select, json.dumps(result_json, ensure_ascii=False)))
                conn.commit()
                
                my_bar.progress(100)
                st.success("🎉 AI đã chuyển đổi và chuẩn hóa thành công kế hoạch bài dạy chuẩn 4.0!")

# --- KHÔNG GIAN HIỂN THỊ KẾT QUẢ ĐẦU RA SƯ PHẠM ---
if "processed_json" in st.session_state:
    lesson_data = st.session_state["processed_json"]
    
    st.markdown("---")
    st.header("🎯 KẾT QUẢ KHBD CHUẨN HÓA SỐ")
    
    # Chia tab kết quả đầu ra: Giáo án, Bảng Ma trận năng lực, Phiếu bài tập số hóa cá nhân hóa học sinh
    tab_res_plan, tab_res_matrix, tab_res_sheet = st.tabs(["📋 Kế hoạch bài dạy (CV 5512)", "📊 Ma trận mục tiêu & Đánh giá", "📝 Phiếu học tập số"])
    
    with tab_res_plan:
        html_preview = format_html_preview(lesson_data)
        st.markdown(html_preview, unsafe_allow_html=True)
        
    with tab_res_matrix:
        st.subheader("1. Ma trận phân phối các mức độ nhận thức bài học")
        df_m, df_r = generate_matrices(lesson_data)
        st.dataframe(df_m, use_container_width=True, hide_index=True)
        
        st.subheader("2. Tiêu chí kiểm tra, đánh giá định lượng hoạt động học (Rubrics)")
        st.dataframe(df_r, use_container_width=True, hide_index=True)
        
    with tab_res_sheet:
        st.subheader("Hệ thống học liệu bổ trợ Phiếu học tập đa phương tiện sinh từ AI")
        worksheet_data = generate_digital_worksheet(lesson_data)
        st.write(f"### {worksheet_data['title']}")
        
        st.markdown("**📌 Các nhiệm vụ phân hóa cá nhân học sinh:**")
        for p_task in worksheet_data["phieu_ca_nhan"]:
            st.info(p_task)
            
        st.markdown("**👥 Nhiệm vụ chuyển đổi số và hợp tác nhóm:**")
        for g_task in worksheet_data["phieu_nhom"]:
            st.warning(g_task)
            
    # --- PHẦN XUẤT BẢN THÀNH PHẨM WORD HÀNH CHÍNH CHUẨN ---
    st.markdown("---")
    st.subheader("💾 ĐÓNG GÓI VÀ XUẤT BẢN FILE ĐẦU RA")
    
    # Chỉ tạo file Word một lần và lưu vào session_state để tránh sinh lại mỗi khi di chuột/re-run
    if "word_file_bytes" not in st.session_state or st.button("🔄 Tạo lại file Word"):
        with st.spinner("Đang đóng gói file Word chuẩn hành chính..."):
            df_m_export, df_r_export = generate_matrices(lesson_data)
            worksheet_export = generate_digital_worksheet(lesson_data)
            
            # Tạo stream và lưu dạng bytes để không bị lock bộ nhớ
# Tìm đến dòng gọi export_lesson_to_word ở gần cuối file và sửa lại:
    stream = export_lesson_to_word(lesson_data, df_m_export, df_r_export, worksheet_export, lesson_format=lesson_format)            st.session_state["word_file_bytes"] = stream.getvalue()

    filename_export = f"Giao_An_4.0_{lesson_data.get('thong_tin_chung',{}).get('ten_bai_hoc','Bai_Hoc')}.docx"
    
    st.download_button(
        label="📥 TẢI XUỐNG FILE WORD (.DOCX) CHUẨN HÀNH CHÍNH GIÁO DỤC",
        data=st.session_state["word_file_bytes"],
        file_name=filename_export,
        type="primary",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )
    st.caption("Ghi chú định dạng: File Word đầu ra tự động cấu hình Font chữ Times New Roman, Cỡ 13, Dãn dòng 1.15, Biên lề trang (2cm-2cm-3cm-2cm) đúng tuyệt đối quy định văn bản hành chính Việt Nam.")

# --- FOOTER CỐ ĐỊNH ---
st.divider()

# Chân trang (Footer)
col_left, col_right = st.columns(2)
with col_left:
    st.caption("Phát triển bởi Ngo Thanh Hung © 2026")
with col_right:
    st.markdown(
        "<div style='text-align: right; color: gray; font-size: 0.85em;'>"
        "AI có thể mắc lỗi. Cần kiểm tra kỹ các thông tin quan trọng."
        "</div>", 
        unsafe_allow_html=True
    )
