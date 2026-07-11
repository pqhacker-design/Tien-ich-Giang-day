import streamlit as st
import plotly.express as px
import pandas as pd

def render_dashboard(db_conn, level):
    st.markdown("## 📊 Dashboard Phân Tích Lớp Học")
    
    df = pd.read_sql_query("SELECT * FROM students", db_conn)
    if df.empty:
        st.info("👋 Chưa có dữ liệu học sinh. Vui lòng chuyển sang tab 'Quản lý học sinh'.")
        return

    # Tính toán điểm trung bình thực tế từ chuỗi điểm thường xuyên
    df['tx_list'] = df['tx_scores'].apply(lambda x: [float(i) for i in str(x).split(',') if i.strip() != ''])
    
    # Render các chỉ số KPI nhanh
    col1, col2, col3 = st.columns(3)
    col1.metric("Sĩ số lớp", len(df))
    col2.metric("Điểm Cuối Kỳ TB", round(df['ck_score'].mean(), 2))
    col3.metric("Số HS cần hỗ trợ (Dưới Đạt)", len(df[df['ck_score'] < 5]))

    # Biểu đồ phân bổ phổ điểm Cuối Kỳ bằng Plotly
    st.markdown("### 📈 Phổ điểm cuối kỳ")
    fig = px.histogram(df, x="ck_score", nbins=10, labels={'ck_score': 'Điểm cuối kỳ'},
                       title="Phân phối điểm số cuối kỳ của lớp", color_discrete_sequence=['#4F46E5'])
    st.plotly_chart(fig, use_container_width=True)

    # Hệ thống Cảnh báo sớm (Module 9)
    st.markdown("### ⚠️ Cảnh báo sư phạm sớm")
    for idx, row in df.iterrows():
        if row['ck_score'] < 5.0:
            st.error(f"🔴 Học sinh **{row['name']}** ({row['id']}) có nguy cơ chưa hoàn thành môn học. Điểm CK: {row['ck_score']}")
        if row['gk_score'] is not None and row['ck_score'] is not None:
            if row['gk_score'] - row['ck_score'] >= 2.5:
                st.warning(f"🟡 Học sinh **{row['name']}** có dấu hiệu sa sút nghiêm trọng (Điểm GK: {row['gk_score']} -> CK: {row['ck_score']})")
