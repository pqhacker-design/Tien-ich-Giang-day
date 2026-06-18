import streamlit as st

# 1. Cấu hình trang
import streamlit as st

# Cấu hình trang chủ
st.set_page_config(
    page_title="🏠 Trang chủ",  # <-- Streamlit sẽ dùng chuỗi này thay thế chữ "app" trên menu
    page_icon="🎓",
    layout="wide"
)

# 2. Tiêu đề chính của hệ thống
st.title("🎓 Hệ sinh thái Trợ lý Giáo dục AI")
st.write("Chào mừng thầy/cô đến với nền tảng công cụ công nghệ thông tin và AI hỗ trợ giảng dạy bám sát Chương trình GDPT 2018.")

st.markdown("---")

# 3. QUẢN LÝ API KEY TẬP TRUNG
st.subheader("🔑 Cấu hình kết nối AI")
gemini_api_key = st.text_input(
    "Nhập Google Gemini API Key của bạn tại đây:",
    type="password",
    help="Nhập một lần tại đây, tất cả các ứng dụng thành phần sẽ tự động sử dụng chung."
)

if gemini_api_key:
    st.session_state["gemini_api_key"] = gemini_api_key
    st.success("✔️ Đã đồng bộ API Key cho toàn bộ hệ thống!")
else:
    if "gemini_api_key" in st.session_state:
        st.info("ℹ️ Hệ thống đang sử dụng API Key đã lưu từ trước.")
    else:
        st.warning("⚠️ Vui lòng nhập Gemini API Key để kích hoạt các tính năng AI trong các ứng dụng con.")

st.markdown("---")

# 4. DANH SÁCH ỨNG DỤNG THÀNH PHẦN (Kết hợp nút bấm chuyển trang tự động)
st.subheader("🛠️ Danh sách các công cụ tiện ích")

# Hàng 1: Gồm 2 cột cho App 1 và App 2
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📝 1. Tích hợp Năng lực số")
        st.write("Tự động phân tích giáo án Word (.docx) và chèn nội dung phát triển năng lực số theo đúng các vị trí hoạt động dạy học thực tế.")
        # Sử dụng st.button để tạo hành động chuyển trang
        if st.button("🚀 Mở ứng dụng Tích hợp KNS", key="btn_tich_hop", use_container_width=True):
            # Đường dẫn tính từ thư mục pages/
            st.switch_page("pages/1_📝_Tích_Hợp_KNS.py")

with col2:
    with st.container(border=True):
        st.markdown("### 📚 2. Trợ lý AI - Soạn KHBD")
        st.write("Trợ lý ảo thông minh giúp giáo viên soạn kế hoạch bài dạy tất cả các môn học.")
        if st.button("🚀 Mở ứng dụng Soạn KHBD", key="btn_soan_khbd", use_container_width=True):
            st.switch_page("pages/2_📚_Trợ_lý_Soạn_KHBD.py")

st.write("") # Tạo khoảng cách dòng giữa 2 hàng

# Hàng 2: Gồm 2 cột cho App 3 và App 4
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        st.markdown("### 🎯 3. Gọi học sinh ngẫu nhiên")
        st.write("Công cụ tạo trò chơi vòng quay may mắn, lưới ảnh học sinh để tương tác, gọi tên ngẫu nhiên trong các hoạt động trên lớp học.")
        # Bạn nhớ đổi lại chính xác tên file của app 3 trong thư mục pages của bạn tại đây nhé
        if st.button("🚀 Mở ứng dụng Gọi học sinh", key="btn_goi_ten", use_container_width=True):
            st.switch_page("pages/3_🎯_Gọi_HS_ngẫu_nhiên.py")

with col4:
    with st.container(border=True):
        st.markdown("### 📈 4. Máy tính Lãi suất kép")
        st.write("Ứng dụng tính toán tài chính tích hợp trực quan sinh động, bám sát nội dung thực hành toán học Lớp 8 Bộ sách Kết nối tri thức.")
        if st.button("🚀 Mở ứng dụng Máy tính Lãi suất", key="btn_lai_suat", use_container_width=True):
            st.switch_page("pages/4_📈_Lai_Suat.py")

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
