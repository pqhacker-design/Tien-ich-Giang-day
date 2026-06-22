import streamlit as st
import os
import matplotlib.pyplot as plt
from ai_math_drawer.ai_engine import AIEngine
from ai_math_drawer.geometry_engine import GeometryEngine
from ai_math_drawer.docx_exporter import DocxExporter

# Khởi tạo cấu hình trang
st.set_page_config(
    page_title="AI Vẽ Hình Học và Đồ Thị Toán Học",
    page_icon="📐",
    layout="wide"
)
st.title("📐 AI Vẽ Hình Học và Đồ Thị Toán Học")
st.caption("Trợ lý giúp vẽ hình hình học tự động và vẽ đồ thị từ đề bài")
# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
    # Gán vào biến môi trường hệ thống để thư viện google-genai tự động nạp
os.environ["GEMINI_API_KEY"] = st.session_state["gemini_api_key"].strip()
st.session_state.ai_engine = AIEngine()
else:
    # Nếu chưa nhập key ở trang chủ, hiển thị thông báo nhắc nhở và dừng app con lại
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop() # Dừng không chạy các đoạn code phía dưới để tránh lỗi crash
    
# Khởi tạo các class engine vào session state
if 'ai_engine' not in st.session_state:
    st.session_state.ai_engine = AIEngine()
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'generated_fig' not in st.session_state:
    st.session_state.generated_fig = None

# --- SIDEBAR: CHỈ GIỮ LẠI TÙY CHỈNH ĐỒ HỌA (ĐÃ BỎ PHẦN CAU HINH API) ---
with st.sidebar:
    st.header("🎨 TÙY CHỈNH NÉT VẼ")
    line_color = st.color_picker("Màu nét vẽ chính:", "#1f77b4")
    line_width = st.slider("Độ dày nét vẽ:", 1.0, 5.0, 2.0, 0.5)
    font_size = st.slider("Kích thước chữ chú thích:", 8, 20, 12, 1)
    
    st.divider()
    st.header("💾 CẤU HÌNH XUẤT BẢN")
    img_format = st.selectbox("Định dạng ảnh:", ["png", "jpg", "svg", "pdf"])
    dpi_resolution = st.selectbox("Độ phân giải (DPI):", [150, 300, 600], index=1)

# Đóng gói cấu hình để truyền vào GeometryEngine
config_dict = {
    "line_color": line_color,
    "line_width": line_width,
    "font_size": font_size
}

# --- GIAO DIỆN CHÍNH ---
st.title("📐 AI Vẽ Hình Học & Đồ Thị Toán Học")
st.caption("Ứng dụng thông minh hỗ trợ Giáo viên & Học sinh tự động hóa hình vẽ toán học bằng Trí tuệ nhân tạo.")

tabs = st.tabs(["🔮 Vẽ Hình Tự Động", "📚 Lịch Sử & Xuất Word Hàng Loạt", "💡 Hướng Dẫn & Ví Dụ"])

# TAB 1: VẼ HÌNH TỰ ĐỘNG
# ... (Giữ nguyên các đoạn code khởi tạo và sidebar cũ của bạn) ...

# TAB 1: VẼ HÌNH TỰ ĐỘNG
with tabs[0]:
    col_input, col_render = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("📝 Nhập Đề Bài & Tải File")
        mode = st.radio("Loại toán bài toán:", ["Hình học (THCS/THPT/Tọa độ)", "Đồ thị hàm số"], horizontal=True)
        mode_key = 'geometry' if "Hình học" in mode else 'function'
        
        # TÍNH NĂNG MỚI: Cho phép tải file đề bài
        uploaded_file = st.file_uploader(
            "Tải lên Ảnh đề bài, file PDF hoặc file Word chứa đề toán:", 
            type=["png", "jpg", "jpeg", "pdf", "docx"],
            help="Bạn có thể chụp màn hình câu hỏi toán rồi tải lên đây mà không cần gõ lại ký hiệu phức tạp."
        )
        
        # Nhập chỉ dẫn câu cần vẽ
        prompt = st.text_area(
            "Yêu cầu cụ thể dành cho AI:",
            value="Hãy tìm và vẽ hình minh họa cho Câu 5 trong đề bài trên.",
            placeholder="Ví dụ: Vẽ hình câu 3b / Vẽ đồ thị hàm số ở câu hỏi tự luận cuối cùng...",
            height=80
        )
        
        btn_generate = st.button("🚀 AI Phân Tích Đề & Vẽ Hình", type="primary", use_container_width=True)
        
        if btn_generate:
            if uploaded_file is None and not prompt.strip():
                st.error("Vui lòng tải file đề bài lên hoặc nhập nội dung văn bản đề bài!")
            else:
                with st.spinner("AI đang 'đọc' tài liệu và lập trình tính toán tọa độ..."):
                    # Gọi hàm xử lý nâng cấp từ AI Engine
                    result = st.session_state.ai_engine.analyze_and_generate_code(
                        mode=mode_key, 
                        user_request=prompt, 
                        uploaded_file=uploaded_file
                    )
                    
                    if result["error"]:
                        st.error(result["error"])
                        if result["code"]:
                            st.info(f"Phản hồi từ AI:\n{result['code']}")
                    else:
                        st.session_state.current_code = result["code"]
                        try:
                            # Thực thi mã vẽ thông qua GeometryEngine
                            fig = GeometryEngine.execute_drawing_code(result["code"], config_dict)
                            st.session_state.generated_fig = fig
                            
                            st.session_state.history.append({
                                "prompt": prompt if uploaded_file is None else f"[{uploaded_file.name}] {prompt}",
                                "code": result["code"],
                                "fig": fig
                            })
                            st.success("AI đã phân tích đề toán và dựng hình thành công!")
                        except Exception as exec_err:
                            st.error(f"Lỗi khi chạy mã vẽ hình do AI sinh ra: {str(exec_err)}")
                            st.info("Bạn có thể chỉnh sửa lại đoạn mã bên dưới để sửa lỗi.")
                            
    with col_render:
        st.subheader("🖼️ Kết Quả Trực Quan")
        # ... (Giữ nguyên đoạn hiển thị ảnh và nút bấm download ảnh cũ của bạn) ...
# TAB 2: LỊCH SỬ VÀ XUẤT FILE WORD HÀNG LOẠT
with tabs[1]:
    st.subheader("📚 Quản lý thư viện hình đã vẽ & Xuất tài liệu Word")
    if not st.session_state.history:
        st.info("Chưa có bài toán nào trong lịch sử phiên làm việc này.")
    else:
        st.write(f"Hiện đang lưu trữ **{len(st.session_state.history)}** hình vẽ.")
        
        # Checkbox chọn các hình muốn xuất file Word
        selected_indices = []
        for idx, item in enumerate(st.session_state.history):
            checked = st.checkbox(f"Bài toán {idx+1}: {item['prompt'][:60]}...", value=True, key=f"hist_{idx}")
            if checked:
                selected_indices.append(idx)
        
        if st.button("📝 Xuất Các Bài Đã Chọn Sang Microsoft Word (.docx)", type="secondary"):
            if not selected_indices:
                st.warning("Vui lòng chọn ít nhất một hình vẽ để tạo tài liệu!")
            else:
                with st.spinner("Đang đóng gói file Word..."):
                    exporter = DocxExporter()
                    for order, idx in enumerate(selected_indices, 1):
                        item = st.session_state.history[idx]
                        # Chuyển đổi fig thành luồng dữ liệu PNG ổn định để chèn vào Word
                        img_stream = GeometryEngine.convert_fig_to_image(item['fig'], dpi=300, format='png')
                        exporter.add_math_problem(order, item['prompt'], img_stream)
                    
                    docx_data = exporter.save()
                    st.download_button(
                        label="📥 Click để Tải File Word (.docx) Về Máy",
                        data=docx_data,
                        file_name="Giao_An_Hinh_Hoc_AI.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

# TAB 3: HƯỚNG DẪN & VÍ DỤ MẪU
with tabs[2]:
    st.markdown("""
    ### 📖 Hướng dẫn sử dụng nhanh:
    1. **Nhập API Key**: Lấy từ Google AI Studio dán vào phần cài đặt ở thanh menu bên trái.
    2. **Nhập ngôn ngữ tự nhiên**: Gõ trực tiếp đề toán như trong sách giáo khoa.
    3. **Tùy chỉnh**: Thay đổi màu sắc, kích thước chữ theo ý muốn ở thanh bên trước hoặc sau khi vẽ.
    4. **Xuất bản**: Tải ảnh đơn lẻ dạng vector (SVG/PDF) hoặc ảnh siêu nét (600 DPI) để in ấn; Hoặc tạo file Word hàng loạt làm đề thi, giáo án.
    
    ### 🌟 Các mẫu câu lệnh đề xuất chạy cực tốt với Gemini:
    * *Hình học THCS:* `"Vẽ tam giác ABC có AB=5, AC=7, góc A bằng 60 độ. Vẽ đường cao AH và trung điểm M của BC."`
    * *Đồ thị hàm số THPT:* `"Vẽ đồ thị hàm số y = (2*x + 1) / (x - 1). Hiển thị các tiệm cận đứng và tiệm cận ngang bằng nét đứt."`
    * *Hình học tọa độ:* `"Trong mặt phẳng Oxy, vẽ đường tròn (C) tâm I(2, -3) bán kính R=4 và đường thẳng d: 3x - 4y + 5 = 0."`
    """)
