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
st.caption("Trợ lý giúp vẽ hình hình học tự động và vẽ đồ thị từ đề bài (Hỗ trợ nhập chữ, tải Ảnh, PDF hoặc file Word)")

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ (ĐÃ SỬA LỖI CÚ PHÁP) ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"].strip()
    # Gán vào biến môi trường hệ thống để thư viện google-genai tự động nạp
    os.environ["GEMINI_API_KEY"] = api_key_input
    if 'ai_engine' not in st.session_state:
        st.session_state.ai_engine = AIEngine()
else:
    # Nếu chưa nhập key ở trang chủ, hiển thị thông báo nhắc nhở và dừng app con lại
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop() # Dừng không chạy các đoạn code phía dưới để tránh lỗi crash

# Khởi tạo các bộ nhớ trạng thái khác cho trang vẽ hình nếu chưa có
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'generated_fig' not in st.session_state:
    st.session_state.generated_fig = None

# --- SIDEBAR: CHỈ GIỮ LẠI TÙY CHỈNH ĐỒ HỌA ---
with st.sidebar:
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

# --- THIẾT KẾ GIAO DIỆN CHÍNH ---
tabs = st.tabs(["🔮 Vẽ Hình Tự Động", "📚 Lịch Sử & Xuất Word Hàng Loạt", "💡 Hướng Dẫn & Ví Dụ"])

# TAB 1: VẼ HÌNH TỰ ĐỘNG
with tabs[0]:
    col_input, col_render = st.columns([1, 1.2])
    
    with col_input:
        st.subheader("📤 Nhập Đề Bài & Tải File")
        mode = st.radio("Loại bài toán:", ["Hình học (THCS/THPT/Tọa độ)", "Đồ thị hàm số"], horizontal=True)
        mode_key = 'geometry' if "Hình học" in mode else 'function'
        
        # Cho phép tải file đề bài
        uploaded_file = st.file_uploader(
            "Tải lên Ảnh đề bài, file PDF hoặc file Word chứa đề toán:", 
            type=["png", "jpg", "jpeg", "pdf", "docx"],
            help="Bạn có thể chụp màn hình câu hỏi toán rồi tải lên đây mà không cần gõ lại ký hiệu phức tạp."
        )
        
        # Nhập yêu cầu cụ thể
        prompt = st.text_area(
            "Yêu cầu cụ thể hoặc đề bài dạng văn bản:",
            value="Hãy phân tích đề bài và vẽ hình minh họa.",
            placeholder="Ví dụ: Vẽ hình câu 3b / Vẽ đồ thị hàm số ở câu hỏi tự luận cuối cùng...",
            height=80
        )
        
        btn_generate = st.button("🚀 AI Phân Tích Đề & Vẽ Hình", type="primary", use_container_width=True)
        
        if btn_generate:
            if uploaded_file is None and (not prompt.strip() or prompt == "Hãy phân tích đề bài và vẽ hình minh họa."):
                st.error("Vui lòng tải file đề bài lên hoặc nhập nội dung văn bản đề bài cụ thể!")
            else:
                with st.spinner("AI đang phân tích dữ kiện hình học và lập trình tọa độ..."):
                    result = st.session_state.ai_engine.analyze_and_generate_code(
                        mode=mode_key, 
                        user_request=prompt, 
                        uploaded_file=uploaded_file
                    )
                    
                    if result["error"]:
                        st.error(result["error"])
                    else:
                        st.session_state.current_code = result["code"]
                        try:
                            fig = GeometryEngine.execute_drawing_code(result["code"], config_dict)
                            st.session_state.generated_fig = fig
                            
                            # Lưu vào lịch sử vẽ
                            display_prompt = prompt if uploaded_file is None else f"[{uploaded_file.name}] {prompt}"
                            st.session_state.history.append({
                                "prompt": display_prompt,
                                "code": result["code"],
                                "fig": fig
                            })
                            st.success("Phân tích đề bài và dựng hình thành công!")
                        except Exception as exec_err:
                            st.error(f"Lỗi khi thực thi mã vẽ hình: {str(exec_err)}")
    
    with col_render:
        st.subheader("🖼️ Kết Quả Trực Quan")
        if st.session_state.generated_fig:
            # Hiển thị đồ thị lên giao diện
            st.pyplot(st.session_state.generated_fig)
            
            # Xuất ảnh ra bộ nhớ để download
            img_buf = GeometryEngine.convert_fig_to_image(
                st.session_state.generated_fig, 
                dpi=dpi_resolution, 
                format=img_format
            )
            
            # Nút download ảnh
            st.download_button(
                label=f"📥 Tải xuống ảnh (. {img_format.upper()} - {dpi_resolution} DPI)",
                data=img_buf,
                file_name=f"math_drawing.{img_format}",
                mime=f"image/{img_format}",
                use_container_width=True
            )
        else:
            st.info("Hình vẽ minh họa sẽ hiển thị ở đây sau khi bạn nhấn nút 'AI Phân Tích Đề & Vẽ Hình'.")

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
        
        selected_indices = []
        for idx, item in enumerate(st.session_state.history):
            checked = st.checkbox(f"Bài toán {idx+1}: {item['prompt'][:80]}...", value=True, key=f"hist_{idx}")
            if checked:
                selected_indices.append(idx)
        
        if st.button("📝 Xuất hình Các Bài Đã Chọn Sang Microsoft Word (.docx)", type="secondary"):
            if not selected_indices:
                st.warning("Vui lòng chọn ít nhất một hình vẽ để tạo tài liệu!")
            else:
                with st.spinner("Đang đóng gói file Word..."):
                    exporter = DocxExporter()
                    for order, idx in enumerate(selected_indices, 1):
                        item = st.session_state.history[idx]
                        img_stream = GeometryEngine.convert_fig_to_image(item['fig'], dpi=300, format='png')
                        exporter.add_math_problem(order, item['prompt'], img_stream)
                    
                    docx_data = exporter.save()
                    st.download_button(
                        label="📥 Click để Tải File Word (.docx) Về Máy",
                        data=docx_data,
                        file_name="Ve_Hinh_Hoc_AI.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

# TAB 3: HƯỚNG DẪN & VÍ DỤ MẪU
with tabs[2]:
    st.markdown("""
    ### 📖 Hướng dẫn sử dụng nhanh:
    1. **Đồng bộ khóa**: Hãy chắc chắn bạn đã nhập Gemini API Key tại Trang Chủ của hệ thống tiện ích.
    2. **Đưa tài liệu lên**: Bạn có thể gõ trực tiếp đề bài hoặc tiện lợi nhất là đăng tải file Ảnh (chụp màn hình), file tài liệu PDF, file Word chứa câu hỏi.
    3. **Chỉ thị cho AI**: Ra lệnh cụ thể như: *'Hãy vẽ đồ thị câu 4'* hoặc *'Vẽ hình bài hình học cuối file'*.
    4. **Tải về**: Tự do tùy chỉnh nét vẽ, đổi kích thước chữ nhãn điểm và xuất file ảnh chất lượng cao hoặc xuất danh sách bài tập sang Word.
    
    ### 🌟 Các mẫu câu lệnh đề xuất chạy cực tốt với Gemini:
    * *Hình học THCS:* `"Vẽ tam giác ABC có AB=5, AC=7, góc A bằng 60 độ. Vẽ đường cao AH và trung điểm M của BC."`
    * *Đồ thị hàm số THPT:* `"Vẽ đồ thị hàm số y = (2*x + 1) / (x - 1). Hiển thị các tiệm cận đứng và tiệm cận ngang bằng nét đứt."`
    * *Hình học tọa độ:* `"Trong mặt phẳng Oxy, vẽ đường tròn (C) tâm I(2, -3) bán kính R=4 và đường thẳng d: 3x - 4y + 5 = 0."`
    """)
