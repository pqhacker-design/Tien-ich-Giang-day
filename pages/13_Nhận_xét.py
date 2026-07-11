import streamlit as st
from services.gemini_service import GeminiService
from database.connection import init_db

# Cấu hình Trang Streamlit
st.set_page_config(
    page_title="AI Nhận Xét Học Sinh PRO 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Mode & Custom CSS
st.markdown("""
<style>
    .main-title {
        color: #1E88E5;
        font-family: 'Roboto', sans-serif;
        text-align: center;
        padding: 1rem;
    }
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Cơ sở dữ liệu
init_db()

# Sidebar - Cấu hình API Key & Hệ thống
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3429/3429402.png", width=80)
    st.title("PRO 2026 v2.5")
    
    api_key = st.text_input("🔑 Google Gemini API Key", type="password")
    if api_key:
        st.session_state["gemini_service"] = GeminiService(api_key)
        st.success("API Key đã kích hoạt!")
    else:
        st.warning("Vui lòng nhập API Key để dùng tính năng AI.")
        
    st.divider()
    st.subheader("⚙️ Tùy chọn AI")
    model_choice = st.selectbox("Chọn Model", ["gemini-2.5-flash", "gemini-2.5-pro"])
    temp = st.slider("Độ sáng tạo (Temperature)", 0.0, 1.0, 0.7, 0.1)

# Trang chủ Dashboard tổng quan
st.markdown("<h1 class='main-title'>🎓 AI NHẬN XÉT HỌC SINH PRO 2026</h1>", unsafe_allow_html=True)
st.info("Hệ thống trợ lý AI toàn diện dành riêng cho Giáo viên THCS - Chuẩn Thông tư 22/2021/TT-BGDĐT")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tổng số Học sinh", "120", "+5")
col2.metric("Đã nhận xét", "98/120", "81.6%")
col3.metric("Cảnh báo điểm", "3", "-2", delta_color="inverse")
col4.metric("Kho mẫu có sẵn", "5,240 mẫu")

st.divider()
st.subheader("🚀 Thao tác nhanh")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📥 Tải lên bảng điểm (VNEDU/SMAS)", use_container_width=True):
        st.switch_page("pages/1_📥_Nhập_Dữ_Liệu.py")
with c2:
    if st.button("📝 Sinh nhận xét tự động", use_container_width=True):
        st.switch_page("pages/4_📝_Nhận_Xét_Tự_Động.py")
with c3:
    if st.button("💬 Chat với Trợ lý AI", use_container_width=True):
        st.switch_page("pages/7_💬_AI_Trợ_Lý_Chat.py")
