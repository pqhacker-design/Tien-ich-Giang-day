import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def show_data_analysis_module():
    st.subheader("📊 Xử Lý Dữ Liệu Thống Kê & Trực Quan Hóa")
    st.info("Nhập số liệu điểm số của học sinh lớp thực nghiệm trước và sau tác động.")
    
    c1, c2 = st.columns(2)
    with c1:
        pre_scores_str = st.text_area("Điểm TRƯỚC tác động (cách nhau bằng dấu phẩy):", value="5,6,5,7,4,8,6,5,7,6")
    with c2:
        post_scores_str = st.text_area("Điểm SAU tác động (cách nhau bằng dấu phẩy):", value="7,8,7,9,6,9,8,7,9,8")
        
    if st.button("📉 Phân tích thống kê & Vẽ biểu đồ"):
        try:
            pre_scores = [float(x.strip()) for x in pre_scores_str.split(",") if x.strip()]
            post_scores = [float(x.strip()) for x in post_scores_str.split(",") if x.strip()]
            
            if len(pre_scores) != len(post_scores):
                st.error("Số lượng học sinh trước và sau tác động phải bằng nhau!")
                return
                
            df = pd.DataFrame({"Trước tác động": pre_scores, "Sau tác động": post_scores})
            st.dataframe(df.T)
            
            # Tính toán chỉ số cơ bản
            mean_pre = np.mean(pre_scores)
            mean_post = np.mean(post_scores)
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("ĐTB Trước", f"{mean_pre:.2f}")
            col_m2.metric("ĐTB Sau", f"{mean_post:.2f}", delta=f"+{mean_post - mean_pre:.2f}")
            
            # Vẽ biểu đồ đường hướng phát triển
            fig, ax = plt.subplots()
            ax.plot(pre_scores, label="Trước tác động", marker='o', color='red', linestyle='--')
            ax.plot(post_scores, label="Sau tác động", marker='s', color='green')
            ax.set_title("Biểu đồ đường thể hiện sự tiến bộ của học sinh")
            ax.set_ylabel("Điểm số")
            ax.legend()
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"Lỗi định dạng dữ liệu: {e}. Vui lòng kiểm tra lại dấu phẩy.")
