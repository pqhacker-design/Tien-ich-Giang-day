import streamlit as st
import pandas as pd
import plotly.express as px
from database.connection import init_db
from services.gemini_service import GeminiService
from modules.import_wizard import AIImportWizard
from modules.ai_anomaly import AIAnomalyDetector
from utils.exporters import ExportEngine

# 1. Cấu hình Trang & Giao diện
st.set_page_config(
    page_title="AI Nhận Xét Học Sinh PRO 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode & CSS
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #1E88E5; font-weight: bold; text-align: center; }
    .sub-header { font-size: 1.1rem; text-align: center; color: #555; margin-bottom: 2rem; }
    .card { background-color: #f8f9fa; border-radius: 10px; padding: 1rem; border-left: 5px solid #1E88E5; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo DB
init_db()

# Session State Setup
if "gemini_service" not in st.session_state:
    st.session_state["gemini_service"] = GeminiService()
if "current_df" not in st.session_state:
    st.session_state["current_df"] = None
if "mapping" not in st.session_state:
    st.session_state["mapping"] = {}

# 2. Thanh Sidebar Cấu hình (Module 18)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429402.png", width=70)
    st.title("PRO 2026 v2.5")
    
    api_key = st.text_input("🔑 Google Gemini API Key", type="password")
    if api_key:
        st.session_state["gemini_service"] = GeminiService(api_key)
        st.success("API Key đã hoạt động!")
    else:
        st.warning("Vui lòng nhập Gemini API Key để dùng tính năng AI.")
        
    st.divider()
    st.subheader("⚙️ Cấu hình Gemini")
    selected_model = st.selectbox("Chọn Model", ["gemini-2.5-flash", "gemini-2.5-pro"])
    temp = st.slider("Độ sáng tạo (Temperature)", 0.0, 1.0, 0.7, 0.1)
    
    st.divider()
    st.info("Chế độ phân quyền: **Giáo viên Chủ nhiệm**")

# 3. Tiêu đề chính
st.markdown("<div class='main-header'>🎓 AI NHẬN XÉT HỌC SINH PRO 2026</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Hệ thống trợ lý AI toàn diện dành cho Giáo viên THCS - Chuẩn Thông tư 22/2021/TT-BGDĐT</div>", unsafe_allow_html=True)

# 4. Điều hướng Tab Chức năng
tab_import, tab_profile, tab_ai_gen, tab_dashboard, tab_chat = st.tabs([
    "📥 1. Import & Cảnh báo", 
    "👤 2. Hồ sơ Học sinh", 
    "📝 3. AI Sinh Nhận Xét", 
    "📊 4. Dashboard Báo Cáo", 
    "💬 5. AI Chat Assistant"
])

# ==========================================
# TAB 1: IMPORT & CẢNH BÁO BẤT THƯỜNG
# ==========================================
with tab_import:
    st.subheader("Module 1 & 10: Tải dữ liệu & AI Kiểm tra bất thường")
    uploaded_file = st.file_uploader("Kéo thả file Excel (VNEDU, SMAS hoặc tự do)", type=["xlsx", "xls"])
    
    if uploaded_file:
        df, mapping = AIImportWizard.auto_detect_and_parse(uploaded_file)
        st.session_state["current_df"] = df
        st.session_state["mapping"] = mapping
        
        st.success("Tự động nhận diện cấu trúc file thành công!")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("📋 **Xem trước dữ liệu gốc:**")
            st.dataframe(df.head(10), use_container_width=True)
        with col2:
            st.write("🗺️ **Cấu hình ánh xạ cột (AI Mapping):**")
            st.json(mapping)

        # Module 10: Phát hiện bất thường
        st.divider()
        st.subheader("🚨 AI Phát hiện bất thường điểm số")
        anomalies = AIAnomalyDetector.detect_anomalies(df, mapping)
        if anomalies:
            for item in anomalies:
                st.warning(f"⚠️ **{item['student']}**: {item['issue']} (Giá trị: {item['val']})")
        else:
            st.success("✅ Không phát hiện bất thường về định dạng hoặc điểm số!")

# ==========================================
# TAB 2: HỒ SƠ HỌC SINH
# ==========================================
with tab_profile:
    st.subheader("Module 2: Hồ sơ chi tiết Học sinh")
    if st.session_state["current_df"] is not None:
        df = st.session_state["current_df"]
        mapping = st.session_state["mapping"]
        name_col = mapping.get('name', df.columns[0])
        
        student_list = df[name_col].tolist()
        selected_student = st.selectbox("Chọn học sinh xem hồ sơ:", student_list)
        
        student_row = df[df[name_col] == selected_student].iloc[0]
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=120)
            st.markdown(f"### {selected_student}")
            st.write(f"Mã HS: **{student_row.get(mapping.get('code'), 'N/A')}**")
            st.write(f"Lớp: **{student_row.get(mapping.get('class'), '8A1')}**")
        with c2:
            st.write("📊 **Kết quả học tập:**")
            gk = student_row.get(mapping.get('gk'), 0)
            ck = student_row.get(mapping.get('ck'), 0)
            tb = student_row.get(mapping.get('tb'), 0)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Giữa kỳ", gk)
            m2.metric("Cuối kỳ", ck, delta=round(ck - gk, 2) if gk and ck else None)
            m3.metric("Điểm TB", tb)
    else:
        st.info("Vui lòng tải lên dữ liệu học sinh ở Tab 1.")

# ==========================================
# TAB 3: AI SINH NHẬN XÉT TỰ ĐỘNG
# ==========================================
with tab_ai_gen:
    st.subheader("Module 4, 5, 6, 7 & 8: AI Sinh nhận xét đa năng")
    if st.session_state["current_df"] is not None:
        df = st.session_state["current_df"]
        mapping = st.session_state["mapping"]
        name_col = mapping.get('name', df.columns[0])
        
        student_sel = st.selectbox("Chọn học sinh sinh nhận xét:", df[name_col].tolist(), key="gen_select")
        student_row = df[df[name_col] == student_sel].to_dict()
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            detail_level = st.select_slider("Độ chi tiết nhận xét:", options=["Ngắn", "Chuẩn", "Chi tiết", "Rất chi tiết"])
        with col_opt2:
            comment_style = st.selectbox("Phong cách nhận xét (Module 12):", ["Trang trọng", "Thân thiện", "Tích cực", "Ngắn gọn", "Khích lệ"])

        if st.button("🚀 AI Sinh 10 Nhận xét khác nhau (Không trùng lặp)"):
            gemini: GeminiService = st.session_state["gemini_service"]
            if not gemini.is_ready():
                st.error("Chưa cấu hình Gemini API Key!")
            else:
                with st.spinner("AI đang phân tích bảng điểm và tạo 10 nhận xét..."):
                    try:
                        comments = gemini.generate_10_unique_comments(
                            student_info={
                                "full_name": student_sel,
                                "score_tx": student_row.get(mapping.get('tx')),
                                "score_gk": student_row.get(mapping.get('gk')),
                                "score_ck": student_row.get(mapping.get('ck')),
                                "score_tb": student_row.get(mapping.get('tb'))
                            },
                            detail_level=detail_level
                        )
                        st.subheader("💡 10 Phương án Nhận xét Tự động:")
                        for idx, c in enumerate(comments, 1):
                            st.write(f"**{idx}.** {c}")
                    except Exception as e:
                        st.error(f"Lỗi: {str(e)}")
                        
        # Xuất dữ liệu (Module 15)
        st.divider()
        st.subheader("📤 Xuất báo cáo (Word / Excel)")
        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            mock_data = [{"name": student_sel, "class_name": "8A1", "academic_comment": "Học tốt môn Toán, cần chăm chỉ hơn.", "quality_comment": "Trung thực, chăm chỉ.", "capacity_comment": "Tự học tốt.", "advice": "Phát huy thế mạnh."}]
            word_file = ExportEngine.export_to_word(mock_data)
            st.download_button("📄 Tải Báo Cáo Word", data=word_file, file_name=f"NhanXet_{student_sel}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c_exp2:
            excel_file = ExportEngine.export_to_excel(df)
            st.download_button("📊 Tải Toàn Bộ Excel", data=excel_file, file_name="DanhSach_NhanXet_2026.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Vui lòng tải dữ liệu học sinh ở Tab 1.")

# ==========================================
# TAB 4: DASHBOARD BÁO CÁO PLOTLY
# ==========================================
with tab_dashboard:
    st.subheader("Module 14: Dashboard Biểu đồ Phân tích Lớp học")
    if st.session_state["current_df"] is not None:
        df = st.session_state["current_df"]
        mapping = st.session_state["mapping"]
        tb_col = mapping.get('tb')
        
        if tb_col and tb_col in df.columns:
            df[tb_col] = pd.to_numeric(df[tb_col], errors='coerce')
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                fig_hist = px.histogram(df, x=tb_col, nbins=10, title="Phổ điểm Trung bình của Lớp", color_discrete_sequence=['#1E88E5'])
                st.plotly_chart(fig_hist, use_container_width=True)
            with col_d2:
                # Phân loại học sinh
                df['Xếp loại'] = pd.cut(df[tb_col], bins=[0, 5, 6.5, 8, 10], labels=['Chưa đạt', "Đạt", "Khá", "Tốt"])
                fig_pie = px.pie(df, names='Xếp loại', title="Tỷ lệ Xếp loại Học sinh", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Không tìm thấy cột Điểm Trung Bình để vẽ biểu đồ.")
    else:
        st.info("Vui lòng nhập dữ liệu ở Tab 1.")

# ==========================================
# TAB 5: AI CHAT ASSISTANT
# ==========================================
with tab_chat:
    st.subheader("Module 16: Trợ lý AI Chat Hỏi-Đáp Trực tiếp")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Xin chào Thầy/Cô! Tôi là Trợ lý AI Giáo dục 2026. Tôi có thể giúp gì cho Thầy/Cô hôm nay?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if user_query := st.chat_input("Hỏi AI (Ví dụ: Học sinh nào cần hỗ trợ? So sánh HK1 và HK2...)"):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.write(user_query)

        gemini: GeminiService = st.session_state["gemini_service"]
        if gemini.is_ready():
            with st.chat_message("assistant"):
                context = ""
                if st.session_state["current_df"] is not None:
                    context = f"Dữ liệu lớp học hiện tại: {st.session_state['current_df'].to_dict(orient='records')[:5]}"
                
                prompt = f"Context: {context}\nUser Question: {user_query}"
                response = gemini.generate_text(prompt, system_instruction="Bạn là AI tư vấn giáo dục THCS thân thiện, thông minh.")
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.error("Chưa cấu hình API Key trong Sidebar.")
