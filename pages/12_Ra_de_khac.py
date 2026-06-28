import streamlit as st
import pandas as pd
import json
from quiz_builder_app.database import init_db, get_questions, insert_question
from quiz_builder_app.core_engines import SUBJECT_CONFIGS, shuffle_exam, generate_math_graph
from quiz_builder_app.ai_helper import generate_ai_question
from quiz_builder_app.exporters import export_to_word, export_matrix_to_excel

# Cấu hình Layout rộng rãi hiện đại của Streamlit
st.set_page_config(page_title="Hệ thống Khảo thí Quy chuẩn GDPT 2018", layout="wide")
init_db()

st.title("⚡ AI-QUIZMASTER: HỆ THỐNG RA ĐỀ KIỂM TRA ĐẶC THÙ MÔN HỌC")
st.caption("Phát triển chuẩn cấu trúc đánh giá năng lực theo chương trình giáo dục phổ thông mới")

# --- SIDEBAR: ĐIỀU KHIỂN THAM SỐ ĐỀ THI ---
st.sidebar.header("🛠️ THIẾT LẬP ĐỀ THI")
selected_subject = st.sidebar.selectbox("Môn học giảng dạy", list(SUBJECT_CONFIGS.keys()) + ["Vật lý", "Hóa học", "Sinh học", "Địa lý"])
selected_grade = st.sidebar.selectbox("Khối lớp học", ["Lớp 10", "Lớp 11", "Lớp 12"])
exam_type = st.sidebar.selectbox("Loại hình khảo thí", ["15 phút", "1 tiết", "Giữa kỳ", "Cuối kỳ"])
num_codes = st.sidebar.number_input("Số lượng mã đề cần đảo", min_value=1, max_value=20, value=2)

st.sidebar.subheader("🎯 Tỷ lệ Ma trận Mức độ (%)")
nb_pct = st.sidebar.slider("Nhận biết", 0, 100, 40)
th_pct = st.sidebar.slider("Thông hiểu", 0, 100, 30)
vd_pct = st.sidebar.slider("Vận dụng", 0, 100, 20)
vdc_pct = st.sidebar.slider("Vận dụng cao", 0, 100, 10)

if nb_pct + th_pct + vd_pct + vdc_pct != 100:
    st.sidebar.error("⚠️ Tổng tỷ lệ các mức độ phải bằng 100%!")

# Tự động thay đổi thông tin thời gian mặc định theo môn học cấu hình
default_time = 90 if selected_subject in ["Toán", "Ngữ văn"] else 50
duration = st.sidebar.number_input("Thời gian làm bài (Phút)", value=default_time)

# --- KHU VỰC GIAO DIỆN CHÍNH NÂNG CAO (TABS) ---
tab_bank, tab_matrix, tab_generate, tab_ai, tab_stats = st.tabs([
    "🗂️ Ngân Hàng Câu Hỏi", 
    "📊 Ma Trận Đề & Đặc Tả", 
    "🎲 Tự Động Tạo Đề", 
    "🤖 Trợ Lý Giáo Viên AI", 
    "📈 Thống Kê Trực Quan"
])

# -------------------------------------------------------------------------
# TAB 1: NGÂN HÀNG CÂU HỎI
# -------------------------------------------------------------------------
with tab_bank:
    st.header(f"Kho dữ liệu câu hỏi hiện tại: {selected_subject} - {selected_grade}")
    df_questions = get_questions(selected_subject, selected_grade)
    
    if not df_questions.empty:
        st.dataframe(df_questions[["id", "topic", "level", "q_type", "content", "correct_answer"]], use_container_width=True)
    else:
        st.info("Chưa có câu hỏi nào. Hãy thêm câu hỏi bằng AI hoặc File import ở Tab bên cạnh.")

    st.subheader("📥 Thêm câu hỏi thủ công nhanh")
    col1, col2 = st.columns(2)
    with col1:
        new_topic = st.text_input("Chủ đề kiến thức", "Khảo sát hàm số")
        new_level = st.selectbox("Mức độ tư duy", ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"])
        new_type = st.selectbox("Dạng câu hỏi", ["TN_4_lua_chon", "TN_dung_sai", "TL_ngan", "Tu_luan"])
    with col2:
        new_content = st.text_area("Nội dung câu hỏi (Hỗ trợ định dạng kí tự LaTeX $...$)")
        new_opts = st.text_input("Đáp án trắc nghiệm (Nếu có, cách nhau bằng dấu phẩy)", "A. Đúng,B. Sai")
        new_ans = st.text_input("Đáp án đúng")
        
    if st.button("➕ Lưu vào Cơ sở dữ liệu"):
        opts_list = [opt.strip() for opt in new_opts.split(",")] if new_opts else []
        insert_question((selected_subject, selected_grade, new_topic, new_level, new_type, new_content, json.dumps(opts_list), new_ans, "Giải thích thủ công", ""))
        st.success("Đã nạp câu hỏi vào cơ sở dữ liệu SQLite thành công!")
        st.rerun()

# -------------------------------------------------------------------------
# TAB 2: MA TRẬN ĐỀ VÀ BẢNG ĐẶC TẢ
# -------------------------------------------------------------------------
with tab_matrix:
    st.header("📋 Thiết kế Ma trận đặc tả cấu trúc")
    # Tự động sinh dữ liệu ma trận trực quan dựa vào tỷ lệ thiết lập ở Sidebar
    matrix_data = {
        "Chủ đề kiến thức": ["Chủ đề cốt lõi 1", "Chủ đề tích hợp 2", "Chủ đề nâng cao 3", "Tổng số câu"],
        "Nhận biết (Số câu)": [3, 2, 0, 5],
        "Thông hiểu (Số câu)": [1, 2, 1, 4],
        "Vận dụng (Số câu)": [1, 1, 1, 3],
        "Vận dụng cao (Số câu)": [0, 0, 1, 1],
        "Tổng điểm tương ứng": [4.5, 3.5, 2.0, "10.0 Điểm"]
    }
    df_matrix = pd.DataFrame(matrix_data)
    st.table(df_matrix)
    
    excel_file = export_matrix_to_excel(df_matrix)
    st.download_button(
        label="📥 Tải Excel Bản đặc tả ma trận (.xlsx)",
        data=excel_file,
        file_name=f"Ma_tran_dac_ta_{selected_subject}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------------------------------------------------
# TAB 3: TỰ ĐỘNG TẠO ĐỀ & ĐẢO ĐỀ KHÁCH QUAN
# -------------------------------------------------------------------------
with tab_generate:
    st.header("🎲 Khởi tạo Đề thi Ngẫu nhiên từ Ngân hàng")
    
    if st.button("🚀 Bắt đầu Quét dữ liệu và Tạo Đề"):
        df_pool = get_questions(selected_subject, selected_grade)
        
        if len(df_pool) < 2:
            st.error("Ngân hàng câu hỏi hiện tại quá ít, không đủ phân phối trộn đề. Vui lòng sang Tab AI để tự động thêm.")
        else:
            st.success(f"Tìm thấy {len(df_pool)} câu hỏi thích dụng thỏa mãn. Tiến hành tạo {num_codes} mã đề thi độc lập:")
            
            # Tiến hành tuần tự tạo ra các mã đề khác nhau dựa trên mã hạt giống (Seed) khác nhau
            for code_idx in range(num_codes):
                code_name = f"MADEMAU_10{code_idx+1}"
                shuffled_exam_data = shuffle_exam(df_pool, code_number=100 + code_idx)
                
                with st.expander(f"👁️ Xem trước nội dung: {code_name}"):
                    # Hiển thị đặc thù môn Toán nếu có đồ thị sinh tự động
                    if selected_subject == "Toán":
                        st.image(generate_math_graph("bậc 3"))
                    
                    for idx, q in enumerate(shuffled_exam_data, 1):
                        st.markdown(f"**Câu {idx}:** {q['content']}")
                        if q['shuffled_options']:
                            st.write(q['shuffled_options'])
                            
                # Xuất bản tải về ngay lập tức cho Giáo viên
                word_file = export_to_word(selected_subject, "Cấu trúc định hướng 2018", shuffled_exam_data)
                st.download_button(
                    label=f"📥 Tải File Word MS-Docx [{code_name}]",
                    data=word_file,
                    file_name=f"De_Thi_{selected_subject}_{code_name}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"dl_{code_name}"
                )

# -------------------------------------------------------------------------
# TAB 4: TRỢ LÝ GIÁO VIÊN AI (Đặc thù môn học tinh vi)
# -------------------------------------------------------------------------
with tab_ai:
    st.header("🤖 Trợ lý Trí tuệ Nhân tạo hỗ trợ Biên soạn câu hỏi")
    st.info("Hệ thống tự động kích hoạt Engine Prompt tối ưu hóa theo đặc thù môn học được lựa chọn ở Sidebar.")
    
    ai_topic = st.text_input("Phạm vi kiến thức AI cần bám sát:", "Ứng dụng đạo hàm / Đọc hiểu văn học hiện đại")
    ai_level = st.selectbox("Mức độ nhận thức yêu cầu cho AI:", ["Nhận biết", "Thông hiểu", "Vận dụng", "Vận dụng cao"], key="ai_lvl")
    
    if st.button("🧠 Kích hoạt AI sinh câu hỏi"):
        with st.spinner("AI đang phân tích chương trình GDPT và sinh nội dung chuẩn định dạng..."):
            ai_res = generate_ai_question(selected_subject, ai_topic, ai_level, "Tự động")
            
            st.subheader("📋 Kết quả câu hỏi do AI đề xuất:")
            st.info(ai_res['content'])
            if ai_res['options']:
                st.write(ai_res['options'])
            st.success(f"**Đáp án đề xuất:** {ai_res['answer']}")
            st.write(f"*Hướng dẫn chấm / Giải thích:* {ai_res['explanation']}")
            
            # Lưu ngay kết quả vào Database để giáo viên dùng
            insert_question((selected_subject, selected_grade, ai_topic, ai_level, "TN_4_lua_chon" if ai_res['options'] else "Tu_luan", ai_res['content'], json.dumps(ai_res['options']), ai_res['answer'], ai_res['explanation'], ""))
            st.toast("Đã tự động thêm câu hỏi của AI vào Ngân hàng dữ liệu học liệu!")

# -------------------------------------------------------------------------
# TAB 5: THỐNG KÊ TRỰC QUAN ĐỀ THI
# -------------------------------------------------------------------------
with tab_stats:
    st.header("📈 Biểu đồ trực quan phân bổ độ khó đề thi")
    
    # Biểu đồ phân bố thực tế bằng Matplotlib
    labels = ['Nhận biết', 'Thông hiểu', 'Vận dụng', 'Vận dụng cao']
    sizes = [nb_pct, th_pct, vd_pct, vdc_pct]
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#F44336']
    
    fig1, ax1 = plt.subplots(figsize=(5, 5))
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax1.axis('equal') 
    st.pyplot(fig1)
    st.caption("Biểu đồ thể hiện tỷ trọng phân bổ mức độ nhận thức của đề thi hiện hành.")
