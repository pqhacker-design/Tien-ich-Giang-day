import streamlit as st

# 1. Cấu hình trang (Phải đặt ở dòng đầu tiên)
st.set_page_config(
    page_title="Hệ sinh thái Trợ lý Giáo dục AI",
    page_icon="🎓",
    layout="wide"
)

# 2. Tiêu đề chính của hệ thống
st.title("🎓 Hệ sinh thái Trợ lý Giáo dục AI")
st.write("Chào mừng thầy/cô đến với nền tảng công cụ công nghệ thông tin và AI hỗ trợ giảng dạy bám sát Chương trình GDPT 2018.")

st.markdown("---")

# 3. QUẢN LÝ API KEY TẬP TRUNG (Dùng chung cho tất cả các app con)
st.subheader("🔑 Cấu hình kết nối AI")
gemini_api_key = st.text_input(
    "Nhập Google Gemini API Key của bạn tại đây:",
    type="password",
    help="Nhập một lần tại đây, tất cả các ứng dụng thành phần (Gia sư, Tích hợp...) sẽ tự động sử dụng chung."
)

# Lưu API Key vào Session State để các file trong thư mục pages/ có thể gọi ra dùng trực tiếp
if gemini_api_key:
    st.session_state["gemini_api_key"] = gemini_api_key
    st.success("✔️ Đã đồng bộ API Key cho toàn bộ hệ thống!")
else:
    if "gemini_api_key" in st.session_state:
        st.info("ℹ️ Hệ thống đang sử dụng API Key đã lưu từ trước.")
    else:
        st.warning("⚠️ Vui lòng nhập Gemini API Key để kích hoạt các tính năng AI trong các ứng dụng con.")

st.markdown("---")

# 4. DANH SÁCH ỨNG DỤNG THÀNH PHẦN (Hiển thị dạng Lưới 2x2)
st.subheader("🛠️ Danh sách các công cụ tiện ích")

# Hàng 1: Gồm 2 cột cho App 1 và App 2
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True): # Tạo khung viền chuyên nghiệp
        st.markdown("### 📝 1. Tích hợp Năng lực số")
        st.write("Tự động phân tích giáo án Word (.docx) và chèn nội dung phát triển năng lực số theo đúng các vị trí hoạt động dạy học thực tế.")
        st.markdown("**👉 Chọn `1 📝 Tich Hop` ở menu bên trái để mở.**")

with col2:
    with st.container(border=True):
        st.markdown("### 🤖 2. Gia sư Trợ lý AI")
        st.write("Trợ lý ảo thông minh giải đáp kiến thức chuyên sâu, xây dựng phiếu bài tập và gợi ý phương pháp sư phạm cho giáo viên.")
        st.markdown("**👉 Chọn `2 🤖 Gia Su` ở menu bên trái để mở.**")

# Thêm một khoảng cách nhỏ giữa 2 hàng
st.write("")

# Hàng 2: Gồm 2 cột cho App 3 và App 4 (Các ứng dụng mở rộng sau này)
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.markdown("### 🎯 3. Gọi học sinh ngẫu nhiên")
        st.write("Công cụ tạo trò chơi vòng quay may mắn, lưới ảnh học sinh để tương tác, gọi tên ngẫu nhiên trong các hoạt động trên lớp học.")
        st.markdown("**👉 Chọn `3 🎯 Goi Ten` ở menu bên trái để mở.**")

with col4:
    with st.container(border=True):
        st.markdown("### 📈 4. Máy tính Lãi suất kép")
        st.write("Ứng dụng tính toán tài chính tích hợp trực quan sinh động, bám sát nội dung thực hành toán học Lớp 8 Bộ sách Kết nối tri thức.")
        st.markdown("**👉 Chọn `4 📈 Lai Suat` ở menu bên trái để mở.**")

st.markdown("---")

# 5. Chân trang (Footer)
col_left, col_right = st.columns(2)
with col_left:
    st.caption("Phát triển bởi Ngo Thanh Hung © 2026")
with col_right:
    st.markdown(
        "<div style='text-align: right; color: gray; font-size: 0.85em;'>"
        "Hệ thống tối ưu hiển thị tốt nhất trên máy tính và môi trường Windows 11."
        "</div>", 
        unsafe_allow_html=True
    )
