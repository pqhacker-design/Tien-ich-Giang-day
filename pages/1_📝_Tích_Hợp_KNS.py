import streamlit as st
from gemini_service import GeminiService
from word_processor import WordProcessor

# Cấu hình trang ứng dụng
st.set_page_config(
    page_title="Tích hợp Năng lực số vào KHBD",
    page_icon="📝",
    layout="wide"
)

st.title("🤖 Ứng dụng tích hợp Năng lực số tự động vào Giáo án (KHBD)")
st.write("Giải pháp hỗ trợ giáo viên chuyển đổi số giáo án theo Chương trình GDPT 2018 nhanh chóng và chuẩn xác.")

# --- THANH BÊN (SIDEBAR) ---
st.sidebar.header("⚙️ CẤU HÌNH HỆ THỐNG")

# Nhập API Key bảo mật
gemini_api_key = st.sidebar.text_input(
    "Nhập Google Gemini API Key:",
    type="password",
    help="Bạn có thể lấy mã API key miễn phí tại Google AI Studio."
)

# Lựa chọn cấp học môn học
cap_hoc = st.sidebar.selectbox(
    "Chọn cấp học mục tiêu:",
    ["Tự động nhận diện", "Tiểu học", "THCS", "THPT"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Hướng dẫn:**\n"
    "1. Nhập API Key ở trên.\n"
    "2. Tải lên file giáo án `.docx` hiện có.\n"
    "3. Nhấn nút xử lý để AI tự động phân tích và chèn cấu trúc năng lực số thích hợp."
)

# --- MÀN HÌNH CHÍNH ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📂 1. Tải lên giáo án gốc")
    uploaded_file = st.file_uploader(
        "Chọn file giáo án Word (.docx)", 
        type=["docx"],
        help="Hệ thống chỉ hỗ trợ định dạng .docx tiêu chuẩn."
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        st.success(f"✔️ Đã tải lên file thành công: **{uploaded_file.name}**")
        
        # Nút kích hoạt xử lý tích hợp
        if st.button("🚀 Bắt đầu tích hợp năng lực số", type="primary"):
            if not gemini_api_key:
                st.error("❌ Vui lòng nhập Gemini API Key ở thanh bên trước khi thực hiện!")
            else:
                with st.spinner("🔄 Đang đọc dữ liệu và gửi phân tích tới Gemini AI..."):
                    try:
                        # Bước 1: Trích xuất nội dung văn bản giáo án
                        progress_bar = st.progress(10, text="Đang đọc nội dung file Word...")
                        doc_text = WordProcessor.extract_text(file_bytes)
                        
                        if not doc_text.strip():
                            st.error("❌ File Word trống hoặc không tìm thấy nội dung văn bản hợp lệ.")
                            st.stop()
                            
                        # Bước 2: Gọi AI xử lý nội dung
                        progress_bar.progress(40, text="AI đang phân tích và thiết kế năng lực số...")
                        ai_handler = GeminiService(api_key=gemini_api_key)
                        ai_result = ai_handler.analyze_and_integrate(doc_text, cap_hoc)
                        
                        # Lưu kết quả AI vào session state để hiển thị preview
                        st.session_state['ai_result'] = ai_result
                        
                        # Bước 3: Tạo và lưu file Word mới
                        progress_bar.progress(80, text="Đang chèn nội dung và tô màu định dạng Word...")
                        processed_file = WordProcessor.integrate_digital_capacity(file_bytes, ai_result)
                        st.session_state['processed_file'] = processed_file
                        
                        progress_bar.progress(100, text="Hoàn tất xử lý!")
                        st.success("🎉 Tích hợp năng lực số thành công!")
                        
                    except Exception as e:
                        st.error(f"❌ Đã xảy ra lỗi trong quá trình xử lý: {str(e)}")

with col2:
    st.subheader("🖥️ 2. Kết quả & Tải về")
    
    # Kiểm tra xem đã có kết quả xử lý trong phiên làm việc chưa
    if 'ai_result' in st.session_state and 'processed_file' in st.session_state:
        res = st.session_state['ai_result']
        sua_doi_list = res.get('sua_doi', [])
        
        st.markdown("### 📋 Các vị trí đã được tích hợp nội dung số:")
        
        if not sua_doi_list:
            st.warning("AI không tìm thấy hoặc không đề xuất vị trí tích hợp nào phù hợp với văn bản gốc.")
        else:
            # Duyệt qua danh sách chỉnh sửa để hiển thị trực quan lên giao diện xem trước
            for idx, item in enumerate(sua_doi_list):
                anchor = item.get('anchor_text', 'Không rõ vị trí')
                content = item.get('insert_content', 'Không có nội dung')
                
                with st.expander(f"📍 Vị trí {idx + 1}: Sau cụm từ \"{anchor}\"", expanded=True):
                    st.markdown(f"**Văn bản gốc tìm thấy:** `{anchor}`")
                    st.markdown(f"**Nội dung số được chèn vào:** <span style='color:#0066CC; font-weight:bold;'>{content}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Nút Download File Word đã hoàn thiện
        st.download_button(
            label="💾 TẢI XUỐNG GIÁO ÁN TÍCH HỢP (.DOCX)",
            data=st.session_state['processed_file'],
            file_name="KHBD_TichHopNangLucSo.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.info("Chưa có dữ liệu xử lý. Vui lòng hoàn thành các bước ở cột bên trái.")
