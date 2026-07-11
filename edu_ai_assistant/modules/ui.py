import streamlit as st
import pandas as pd
import plotly.express as px

class UIManager:
    @staticmethod
    def setup_theme():
        st.set_page_config(
            page_title="AI Trợ lý Văn bản Giáo dục",
            page_icon="🎓",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # CSS tùy biến Material UI & Clean Dashboard
        st.markdown("""
        <style>
            .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
            .stMetric { background-color: #f8f9fa; border-radius: 10px; padding: 15px; border: 1px solid #e9ecef; }
            .css-card { background-color: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 15px; }
            footer {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)

    @staticmethod
    def render_header():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown("##🎓 AI Trợ lý Xử lý Văn bản Giáo dục")
            st.info("Thế hệ Multi-Agent AI | Chuẩn Nghị định 30 & Bộ Giáo dục và Đào tạo")
        with col2:
            st.write("")
            st.success("🟢 System Online")

    @staticmethod
    def render_dashboard():
        st.subheader("📊 Tổng quan Hệ thống")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Tổng văn bản xử lý", "1,248", "+12% tháng này")
        col2.metric("Đã xử lý hôm nay", "24 văn bản", "+5 hôm nay")
        col3.metric("Tỷ lệ chuẩn Thể thức", "98.5%", "+1.2%")
        col4.metric("Dung lượng RAG Database", "45 Tài liệu", "Cập nhật hôm nay")
        st.divider()
