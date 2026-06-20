import streamlit as st

def show_library_module():
    st.subheader("📚 Thư Viện Tra Cứu Đề Tài Mẫu Quy Chuẩn")
    
    search_query = st.text_input("Tìm kiếm tài liệu, sáng kiến (Ví dụ: Toán, Tin học, STEM...):")
    
    categories = {
        "Toán học": ["Biện pháp ứng dụng công nghệ số trong dạy học Hình học 8", "Phát triển tư duy phản biện qua giải toán có lời văn"],
        "Khoa học tự nhiên": ["Thiết kế chủ đề STEM nội dung dòng điện lớp 9", "Ứng dụng dạy học dự án trong chủ đề đa dạng sinh học"],
        "Tin học & Công nghệ": ["Xây dựng hệ thống học liệu số với Google Drive", "Tổ chức kiểm tra đánh giá trên nền tảng LMS"]
    }
    
    for cat, topics in categories.items():
        with st.expander(f"📁 Thư mục: SKKN môn {cat}"):
            for t in topics:
                st.write(f"🔹 {t}")
