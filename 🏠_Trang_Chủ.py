import streamlit as st
from google import genai  # Thư viện google-genai mới
from google.genai.errors import APIError

# 1. Cấu hình trang chủ
st.set_page_config(
    page_title="Thầy Ngô Hùng - 0913117321",
    page_icon="🎓",
    layout="wide"
)

# 2. Tiêu đề chính
st.markdown("## 🎓 Hệ sinh thái Trợ lý Giáo dục AI  ([Get API key](https://aistudio.google.com/api-keys))")
st.caption("Nền tảng CNTT và AI hỗ trợ giảng dạy và học tập bám sát Chương trình GDPT 2018. (LƯU Ý: AI không làm giúp bạn, AI chỉ hỗ trợ cho bạn.)")

# --- 3. QUẢN LÝ & KIỂM TRA API KEY TẬP TRUNG (Dùng google-genai) ---
if "saved_api_key" not in st.session_state:
    st.session_state["saved_api_key"] = ""
if "api_key_valid" not in st.session_state:
    st.session_state["api_key_valid"] = False

def check_gemini_api_key(api_key: str) -> tuple[bool, str]:
    """Kiểm tra tính hợp lệ của API Key bằng Client của thư viện google-genai."""
    clean_key = api_key.strip()
    if not clean_key:
        return False, "Vui lòng không để trống API Key."
    
    try:
        # Khởi tạo Client từ google.genai
        client = genai.Client(api_key=clean_key)
        
        # Gửi request nhẹ để kiểm tra kết nối (sử dụng gemini-2.5-flash)
        client.models.generate_content(
            model="gemini-2.5-flash",
            contents="ping"
        )
        return True, "API Key hợp lệ và sẵn sàng sử dụng!"
        
    except APIError as e:
        error_str = str(e)
        if "API_KEY_INVALID" in error_str or "400" in error_str:
            return False, "API Key không chính xác. Vui lòng kiểm tra lại!"
        elif "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
            return False, "API Key đã vượt quá giới hạn (Quota Exceeded)."
        return False, f"Lỗi Google AI API: {e.message}"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"

with st.expander("**🔑 Cấu hình kết nối AI (Nhập API key của bạn để sử dụng các tiện ích)**", expanded=not st.session_state["api_key_valid"]):
    input_key = st.text_input(
        "**Nhập Google Gemini API Key của bạn tại đây:**",
        value=st.session_state["saved_api_key"],
        type="password",
        help="Lấy API Key miễn phí từ Google AI Studio để kích hoạt hệ thống."
    )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        verify_clicked = st.button("🔍 Kiểm tra & Lưu Key", type="primary", use_container_width=True)

    # Thực hiện kiểm tra khi bấm nút hoặc khi giá trị input thay đổi
    if verify_clicked or (input_key and input_key != st.session_state["saved_api_key"]):
        with st.spinner("Đang kết nối tới Google AI Studio..."):
            is_valid, message = check_gemini_api_key(input_key)
            
            if is_valid:
                st.session_state["saved_api_key"] = input_key
                st.session_state["gemini_api_key"] = input_key
                st.session_state["api_key_valid"] = True
                st.success(f"✔️ {message}")
            else:
                st.session_state["api_key_valid"] = False
                st.session_state.pop("gemini_api_key", None)
                st.error(f"❌ {message}")
    elif st.session_state.get("api_key_valid"):
        st.info("ℹ️ Hệ thống đang sử dụng API Key đã xác thực thành công.")
    else:
        st.warning("⚠️ Vui lòng nhập API Key để bắt đầu sử dụng.")
        
# 4. DANH SÁCH ỨNG DỤNG THÀNH PHẦN (Được đẩy lên sát bên trên)
st.markdown(
    """
    <div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;">
        <h4 style="margin: 0; color: #0369A1;">🛠️ DANH SÁCH CÁC CÔNG CỤ TIỆN ÍCH</h4>
    </div>
    """, 
    unsafe_allow_html=True
)
# Hàng 1: Gồm 3 cột cho App 1, App 2, App 3
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("#### 📝 1. Tích hợp Năng lực số")
        st.write("Tự động phân tích giáo án Word (.docx) và chèn nội dung phát triển năng lực số theo đúng các vị trí hoạt động dạy học thực tế.")
        if st.button("🚀 Mở ứng dụng Tích hợp KNS", key="btn_tich_hop", use_container_width=True):
            st.switch_page("pages/1_📝_Tích_Hợp_Kỹ_Năng_Số.py")

with col2:
    with st.container(border=True):
        st.markdown("### 📚 2. Trợ lý Soạn KHBD")
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
        st.write("Ứng dụng Kiểm tra và Sửa lỗi Chính tả và xuất ra định dạng chuẩn văn bản hành chính")
        if st.button("🚀 Mở ứng dụng Sửa lỗi chính tả", key="btn_sua_loi_chinh_ta", use_container_width=True):
            st.switch_page("pages/4_📝_Sửa_lỗi_chính_tả.py")

with col5:
    with st.container(border=True):
        st.markdown("### 📊 5. Ra đề kiểm tra")
        st.write("Ứng dụng hỗ trợ tạo ma trận, đặc tả và sinh đề kiểm tra định kỳ nhanh chóng, bám sát thông tư hướng dẫn mới.")
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
        st.markdown("### ✍️ 7. Trợ lý viết SKKN")
        st.write("Hệ thống Trợ lý AI Hỗ trợ viết Sáng kiến kinh nghiệm và Nghiên cứu Khoa học Sư phạm Toàn diện")
        if st.button("🚀 Mở ứng dụng Viết SKKN", key="btn_sang_kien_kinh_nghiem", use_container_width=True):
            st.switch_page("pages/7_✍️_Viết_Sáng_kiến_kinh_nghiệm.py")
with col8:
    with st.container(border=True):
        st.markdown("### 🎓 8. Gia sư AI - Hỗ trợ HS học tập")
        st.write("Hỗ trợ HS và hướng dẫn các em làm bài tập Tất cả các môn học từ TH đến THPT.")
        if st.button("🚀 Mở ứng dụng Gia sư", key="btn_gia_su_ai", use_container_width=True):
            st.switch_page("pages/8_🎓_Gia_Sư_AI.py")
with col9:
    with st.container(border=True):
        st.markdown("### 9_🔄_Chuyển đổi file .Pdf thành Word (.docx)")
        st.write("Ứng dụng trích xuất văn bản từ file .pdf, .png, .jpg và xuất bản thành file Word.")
        if st.button("🚀 Mở ứng dụng Pdf to Word", key="btn_pdf_to_word", use_container_width=True):
            st.switch_page("pages/9_🔄_Chuyển_đổi_Pdf_to_Word.py")

# Hàng 4: Gồm 3 cột cho App 10, App 11, App 12
col10, col11, col12 = st.columns(3)

with col10:
    with st.container(border=True):
        st.markdown("### 📐 10. Trợ lý giúp vẽ hình Hình học")
        st.write("Trợ lý AI giúp GV vẽ hình hình học theo đề bài ra để chèn vào KHBD hoặc lời giải trong đề bài.")
        if st.button("🚀 Mở ứng dụng Vẽ hình HH", key="btn_ve_hinh_hoc", use_container_width=True):
            st.switch_page("pages/10_📐_Vẽ_Hình_học_và_Đồ_thị.py")
with col11:
    with st.container(border=True):
        st.markdown("### 🛡️ 11. So sánh văn bản")
        st.write("Giúp người dùng so sánh, đối chiếu, đánh giá chất lượng văn bản so với mẫu và áp dụng chỉnh sửa.")
        if st.button("🚀 Mở ứng dụng So sánh VB", key="btn_so_sanh_van_ban", use_container_width=True):
            st.switch_page("pages/11_🛡️_So_sánh_văn_bản.py")
with col12:
    with st.container(border=True):
        st.markdown("### ✍️ 12. Trợ lý soạn thảo văn bản")
        st.write("Giúp GV soạn thảo và chỉnh sửa văn bản theo yêu cầu")
        if st.button("🚀 Mở Trợ lý soạn thảo VB", key="btn_tro_ly_vb", use_container_width=True):
            st.switch_page("pages/12_✍️_Trợ_lý_soạn_ thảo_văn_bản.py")            
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
