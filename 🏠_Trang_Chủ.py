import streamlit as st

# 1. Cấu hình trang chủ
st.set_page_config(
    page_title="Thầy Ngô Hùng - 0913117321",
    page_icon="🎓",
    layout="wide"
)

# 2. Tiêu đề chính tối ưu siêu gọn (Kết hợp H2 và Caption để tiết kiệm dòng)
st.markdown("## 🎓 Hệ sinh thái Trợ lý Giáo dục AI")
st.caption("Nền tảng CNTT và AI hỗ trợ giảng dạy và học tập bám sát Chương trình GDPT 2018. (LƯU Ý: AI không làm giúp bạn, AI chỉ hỗ trợ cho bạn.)")

# 3. QUẢN LÝ API KEY TẬP TRUNG (Thu gọn vào Expander - Mặc định ĐÓNG để đỡ chiếm chỗ)
with st.expander("🔑 Cấu hình kết nối AI (Nhập API key của bạn để sử dụng các tiện ích)", expanded=False):
    gemini_api_key = st.text_input(
        "Nhập Google Gemini API Key của bạn tại đây ([Bấm vào đây để lấy API key](https://aistudio.google.com/api-keys)):",
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

# 4. DANH SÁCH ỨNG DỤNG THÀNH PHẦN (Được đẩy lên sát bên trên)
st.markdown("### 🛠️ Danh sách các công cụ tiện ích")

# Hàng 1: Gồm 3 cột cho App 1, App 2, App 3
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### 📝 1. Tích hợp Năng lực số")
        st.write("Tự động phân tích giáo án Word (.docx) và chèn nội dung phát triển năng lực số theo đúng các vị trí hoạt động dạy học thực tế.")
        if st.button("🚀 Mở ứng dụng Tích hợp KNS", key="btn_tich_hop", use_container_width=True):
            st.switch_page("pages/1_📝_Tích_Hợp_Kỹ_Năng_Số.py")

with col2:
    with st.container(border=True):
        st.markdown("### 📚 2. Trợ lý AI - Soạn KHBD")
        st.write("Trợ lý AI thông minh giúp giáo viên Tạo mới hoặc Chỉnh sửa Kế hoạch bài dạy theo CV 5512, tích hợp KNS và xuất ra Word.")
        if st.button("🚀 Mở ứng dụng Soạn KHBD", key="btn_soan_khbd", use_container_width=True):
            st.switch_page("pages/2_📚_Trợ_lý_Soạn_KHBD.py")

with col3:
    with st.container(border=True):
        st.markdown("### 🎯 3. Gọi học sinh ngẫu nhiên")
        st.write("Công cụ tạo trò chơi vòng quay may mắn, lưới ảnh học sinh để tương tác, gọi tên ngẫu nhiên trong các hoạt động trên lớp học.")
        if st.button("🚀 Mở ứng dụng Gọi học sinh", key="btn_goi_ten", use_container_width=True):
            st.switch_page("pages/3_🎯_Gọi_HS_ngẫu_nhiên.py")
            
# Hàng 2: Gồm 3 cột cho App 4, App 5, App 6
col4, col5, col6 = st.columns(3)

with col4:
    with st.container(border=True):
        st.markdown("### 📝 4. Sửa lỗi chính tả văn bản")
        st.write("Ứng dụng Kiểm tra và Sửa lỗi Chính tả/Ngữ pháp Tiếng Việt chuyên sâu dành cho file Word (.docx)")
        if st.button("🚀 Mở ứng dụng Sửa lỗi chính tả", key="btn_sua_loi_chinh_ta", use_container_width=True):
            st.switch_page("pages/4_📝_Sửa_lỗi_chính_tả.py")

with col5:
    with st.container(border=True):
        st.markdown("### 📝 5. Ra đề kiểm tra")
        st.write("Ứng dụng hỗ trợ ma trận, đặc tả và sinh đề kiểm tra định kỳ nhanh chóng, bám sát thông tư hướng dẫn mới.")
        if st.button("🚀 Mở ứng dụng Ra đề kiểm tra", key="btn_ra_de_kt", use_container_width=True):
            st.switch_page("pages/5_📊_Ra_đề_kiểm_tra.py")

with col6:
    with st.container(border=True):
        st.markdown("### 🎮 6. Trò chơi học tập")
        st.write("Thiết kế nhanh các câu hỏi tương tác, kịch bản trò chơi khởi động và ôn tập bài học sinh động.")
        if st.button("🚀 Mở ứng dụng Thiết kế Game", key="btn_game_hoc_tap", use_container_width=True):
            st.switch_page("pages/6_🎮_Trò_chơi_học_tập.py")

# Hàng 3: Gồm 3 cột cho App 7, App 8, App 9
col7, col8, col9 = st.columns(3)

with col7:
    with st.container(border=True):
        st.markdown("### 🎓 7. Trợ lý viết Sáng kiến kinh nghiệm")
        st.write("Hệ thống Trợ lý AI Hỗ trợ viết Sáng kiến kinh nghiệm và Nghiên cứu Khoa học Sư phạm Toàn diện")
        if st.button("🚀 Mở ứng dụng Viết SKKN", key="btn_sang_kien_kinh_nghiem", use_container_width=True):
            st.switch_page("pages/7_🎓_Viết_Sáng_kiến_kinh_nghiệm.py")
with col8:
    with st.container(border=True):
        st.markdown("### 🎓 8. Gia sư AI - Hỗ trợ HS")
        st.write("Hỗ trợ HS và hướng dẫn các em làm bài tập Tất cả các môn học từ TH đến THPT.")
        if st.button("🚀 Mở ứng dụng Gia sư", key="btn_gia_su_ai", use_container_width=True):
            st.switch_page("pages/8_🎓_Gia_Sư_AI.py")
with col9:
    with st.container(border=True):
        st.markdown("### 9_🔄_Chuyển đổi file .Pdf thành Word (.docx)")
        st.write("Ứng dụng trích xuất văn bản từ tài liệu hoặc hình ảnh và xuất bản thành file Word.")
        if st.button("🚀 Mở ứng dụng Pdf to Word", key="btn_pdf_to_word", use_container_width=True):
            st.switch_page("pages/9_🔄_Chuyển_đổi_Pdf_to_Word.py")

# Hàng 4: Gồm 3 cột cho App 10, App 11, App 12
col10, col11, col12 = st.columns(3)

with col10:
    with st.container(border=True):
        st.markdown("### 🎓 10. Trợ lý giúp vẽ hình Hình học")
        st.write("Trợ lý AI giúp GV vẽ hình hình học theo đề bài ra để chèn vào KHBD hoặc lời giải trong đề bài.")
        if st.button("🚀 Mở ứng dụng Vẽ hình HH", key="btn_ve_hinh_hoc", use_container_width=True):
            st.switch_page("pages/10_📐_Vẽ_Hình_học_và_Đồ_thị.py")
with col11:
    with st.container(border=True):
        st.markdown("### 🎓 8. Gia sư AI - Hỗ trợ HS")
        st.write("Hỗ trợ HS và hướng dẫn các em làm bài tập Tất cả các môn học từ TH đến THPT.")
        if st.button("🚀 Mở ứng dụng Gia sư", key="btn_so_sanh_van_ban", use_container_width=True):
            st.switch_page("pages/8_🎓_Gia_Sư_AI.py")
with col12:
    with st.container(border=True):
        st.markdown("### 9_🔄_Chuyển đổi file .Pdf thành Word (.docx)")
        st.write("Ứng dụng trích xuất văn bản từ tài liệu hoặc hình ảnh và xuất bản thành file Word.")
        if st.button("🚀 Mở ứng dụng Pdf to Word", key="btn_khong_biet", use_container_width=True):
            st.switch_page("pages/9_🔄_Chuyển_đổi_Pdf_to_Word.py")            
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
