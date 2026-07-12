import streamlit as st
from gemini_service import GeminiService
from word_processor import WordProcessor

# Cấu hình trang ứng dụng
st.set_page_config(
    page_title="Tích hợp Năng lực số vào KHBD",
    page_icon="📝",
    layout="wide"
)

st.markdown("## 🤖 Tích hợp Năng lực số tự động vào KHBD")
st.info("Giúp GV tích hợp Năng lực số theo Chương trình GDPT 2018 nhanh chóng và chuẩn xác.")

# --- KHU VỰC CẤU HÌNH HỆ THỐNG (ĐÃ CHUYỂN TỪ SIDEBAR VÀO ĐẦU TRANG CHÍNH) ---
with st.expander("⚙️ **CẤU HÌNH HỆ THỐNG:**", expanded=False):

    col_cfg1, col_cfg2 = st.columns([2, 1])
    
    with col_cfg1:
        # Kiểm tra API Key tập trung từ session state
        if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
            api_key = st.session_state["gemini_api_key"]
            st.success("🔑 **Trạng thái API Key:** Đã nhận diện thành công từ Trang chủ.")
        else:
            st.warning("⚠️ **Chưa tìm thấy API Key:** Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key.")
            st.page_link("🏠_Trang_Chủ.py", label="**Nhấn vào đây để Quay lại Trang chủ**", icon="🔄")
            st.stop() # Dừng chạy các dòng code phía dưới nếu chưa có key

    with col_cfg2:
        # Lựa chọn cấp học môn học
        cap_hoc = st.selectbox(
            "**Chọn cấp học mục tiêu:**",
            ["Tự động nhận diện", "Tiểu học", "THCS", "THPT"]
        )

# --- MÀN HÌNH CHÍNH (XỬ LÝ FILE & KẾT QUẢ) ---
col1, col2 = st.columns([1, 1])
with col1:
    with st.container(border=True):
        st.markdown(
            """
            <div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #0369A1;">📂 1. Tải lên KHBD gốc</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        uploaded_file = st.file_uploader(
            "**Chọn file KHBD Word (.docx):**", 
            type=["docx"],
            help="Hệ thống chỉ hỗ trợ định dạng .docx tiêu chuẩn."
        )

        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            st.success(f"✔️ Đã tải lên file thành công: **{uploaded_file.name}**")
            
            # Nút kích hoạt xử lý tích hợp
            if st.button("🚀 Bắt đầu tích hợp năng lực số", type="primary", use_container_width=True):
                with st.spinner("🔄 Đang đọc dữ liệu và gửi phân tích tới Gemini AI..."):
                    try:
                        # Bước 1: Trích xuất nội dung văn bản giáo án
                        progress_bar = st.progress(10, text="Đang đọc nội dung file Word...")
                        doc_text = WordProcessor.extract_text(file_bytes)
                        
                        if not doc_text.strip():
                            st.error("❌ File Word trống hoặc không tìm thấy nội dung văn bản hợp lệ.")
                            st.stop()
                            
                        # Bước 2: Gọi AI xử lý nội dung bằng biến api_key dùng chung
                        progress_bar.progress(40, text="AI đang phân tích và thiết kế năng lực số...")
                        ai_handler = GeminiService(api_key=api_key)
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
    with st.container(border=True):
        st.markdown(
            """
            <div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #0369A1;">🖥️ 2. Kết quả & Tải về</h4>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
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
                label="💾 TẢI XUỐNG KHBD TÍCH HỢP (.DOCX)",
                data=st.session_state['processed_file'],
                file_name="KHBD_TichHopNangLucSo.docx",
                type="primary",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        else:
            st.info("Chưa có dữ liệu xử lý. Vui lòng hoàn thành các bước ở cột bên trái.")

# --- FOOTER CỐ ĐỊNH ---
st.divider()

# Chân trang (Footer)
col_left, col_right = st.columns(2)
with col_left:
    st.caption("Phát triển bởi Ngo Thanh Hung © 2026")
with col_right:
    st.markdown(
        "<div style='text-align: right; color: gray; font-size: 0.85em;'>"
        "AI có thể mắc lỗi. Cần kiểm tra kỹ các thông tin quan trọng."
        "</div>", 
        unsafe_allow_html=True
    )
