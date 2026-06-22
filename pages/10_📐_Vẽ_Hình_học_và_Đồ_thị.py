import streamlit as st
import matplotlib.pyplot as plt
from ai_engine import AIEngine
from geometry_engine import GeometryEngine
from docx_exporter import DocxExporter

# Khởi tạo cấu hình trang
st.set_page_config(
    page_title="AI Vẽ Hình Học và Đồ Thị Toán Học",
    page_icon="📐",
    layout="wide"
)

# Khởi tạo các class engine vào session state
if 'ai_engine' not in st.session_state:
    st.session_state.ai_engine = AIEngine()
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'generated_fig' not in st.session_state:
    st.session_state.generated_fig = None

# --- SIDEBAR: Cấu hình và Tùy chỉnh ---
with st.sidebar:
    st.header("⚙️ CẤU HÌNH HỆ THỐNG")
    
    # Nhập API Key bảo mật
    api_key_input = st.text_input("Gemini API Key:", type="password", help="Nhập Gemini API Key của bạn để kích hoạt AI.")
    if api_key_input:
        import os
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.session_state.ai_engine = AIEngine()

    st.divider()
    st.header("🎨 TÙY CHỈNH NÉT VẼ")
    line_color = st.color_picker("Màu nét vẽ chính:", "#1f77b4")
    line_width = st.slider("Độ dày nét vẽ:", 1.0, 5.0, 2.0, 0.5)
    font_size = st.slider("Kích thước chữ chú thích:", 8, 20, 12, 1)
    
    st.divider()
    st.header("💾 CẤU HÌNH XUẤT BẢN")
    img_format = st.selectbox("Định dạng ảnh:", ["png", "jpg", "svg", "pdf"])
    dpi_resolution = st.selectbox("Độ phân giải (DPI):", [150, 300, 600], index=1)

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
with tabs[0]:
    col_input, col_render = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("📝 Nhập Đề Bài")
        mode = st.radio("Loại toán bài toán:", ["Hình học (THCS/THPT/Tọa độ)", "Đồ thị hàm số"], horizontal=True)
        mode_key = 'geometry' if "Hình học" in mode else 'function'
        
        prompt = st.text_area(
            "Nhập đề bài bằng tiếng Việt tự nhiên:",
            placeholder="Ví dụ: Vẽ tam giác ABC vuông tại A, AB = 4 cm, AC = 3 cm.\nHoặc: Vẽ đồ thị hàm số y = x^2 - 4x + 3",
            height=120
        )
        
        btn_generate = st.button("🚀 Phân Tích Đề & Vẽ Hình", type="primary", use_container_width=True)
        
        if btn_generate:
            if not prompt.strip():
                st.error("Vui lòng nhập đề bài trước khi vẽ!")
            else:
                with st.spinner("AI đang phân tích hình học và lập trình tọa độ..."):
                    result = st.session_state.ai_engine.analyze_and_generate_code(prompt, mode_key)
                    
                    if result["error"]:
                        st.error(result["error"])
                    else:
                        st.session_state.current_code = result["code"]
                        try:
                            fig = GeometryEngine.execute_drawing_code(result["code"], config_dict)
                            st.session_state.generated_fig = fig
                            
                            # Lưu vào lịch sử vẽ
                            st.session_state.history.append({
                                "prompt": prompt,
                                "code": result["code"],
                                "fig": fig
                            })
                            st.success("Phân tích đề bài thành công!")
                        except Exception as exec_err:
                            st.error(f"Lỗi khi thực thi mã vẽ hình: {str(exec_err)}")
    
    with col_render:
        st.subheader("🖼️ Kết Quả Trực Quan")
        if st.session_state.generated_fig:
            # Hiển thị đồ thị Matplotlib lên giao diện Streamlit
            st.pyplot(st.session_state.generated_fig)
            
            # Xuất ảnh ra bộ nhớ để download
            img_buf = GeometryEngine.convert_fig_to_image(
                st.session_state.generated_fig, 
                dpi=dpi_resolution, 
                format=img_format
            )
            
            # Nút bấm download ảnh trực tiếp
            st.download_button(
                label=f"📥 Tải xuống ảnh (. {img_format.upper()} - {dpi_resolution} DPI)",
                data=img_buf,
                file_name=f"math_drawing.{img_format}",
                mime=f"image/{img_format}",
                use_container_width=True
            )
        else:
            st.info("Hình vẽ minh họa sẽ hiển thị ở đây sau khi bạn nhấn nút 'Phân Tích Đề & Vẽ Hình'.")

    # Hiển thị Code Editor tự động bên dưới cho phép chỉnh sửa
    st.divider()
    st.subheader("💻 Mã Python Tạo Hình (AI sinh tự động)")
    if st.session_state.current_code:
        edited_code = st.text_area("Bạn có thể tùy chỉnh hoặc sao chép đoạn mã này để chạy độc lập:", 
                                   value=st.session_state.current_code, height=250)
        
        if st.button("🔄 Cập nhật hình vẽ bằng mã đã sửa"):
            try:
                fig = GeometryEngine.execute_drawing_code(edited_code, config_dict)
                st.session_state.generated_fig = fig
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi thực thi mã chỉnh sửa: {str(e)}")
    else:
        st.code("# Chưa có mã nào được sinh ra", language="python")

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
