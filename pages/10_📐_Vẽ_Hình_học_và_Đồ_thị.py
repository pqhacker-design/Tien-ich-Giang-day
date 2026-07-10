import streamlit as st
import os
import matplotlib.pyplot as plt
from ai_math_drawer.ai_engine import AIEngine
from ai_math_drawer.geometry_engine import GeometryEngine
from ai_math_drawer.docx_exporter import DocxExporter

# 1. Cấu hình trang (Bắt buộc đặt ở đầu file)
st.set_page_config(
    page_title="AI Vẽ Hình Học và Đồ Thị Toán Học",
    page_icon="📐",
    layout="wide"
)

# ĐỊNH NGHĨA SẴN BIẾN ĐỂ TRIỆT TIÊU LỖI ATTRIBUTEERROR DÙ TRANG CÓ LỖI HAY CHƯA NHẬP KEY
ai_engine = None 

st.markdown("## 📐 AI Vẽ Hình Học và Đồ Thị Toán Học")
st.info("Trợ lý giúp vẽ hình hình học tự động và vẽ đồ thị từ đề bài (Hỗ trợ nhập chữ, tải Ảnh, PDF hoặc file Word)")

# --- 2. KIỂM TRA VÀ ĐỒNG BỘ API KEY TỪ BIẾN LƯU TRỮ TRANG CHỦ ---
# Kiểm tra cả 2 biến để đảm bảo an toàn tối đa
has_key = False
api_key_final = ""

if "saved_api_key" in st.session_state and st.session_state["saved_api_key"].strip() != "":
    api_key_final = st.session_state["saved_api_key"].strip()
    has_key = True
elif "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_final = st.session_state["gemini_api_key"].strip()
    has_key = True

if has_key:
    # Gán vào môi trường và khởi tạo Engine cục bộ an toàn cho luồng rerun
    os.environ["GEMINI_API_KEY"] = api_key_final
    ai_engine = AIEngine()
else:
    # Nếu thực sự chưa có key, hiển thị thông báo và chặn đứng giao diện phía dưới
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ ở thanh bên trái sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ nhập API Key", icon="🔄")
    st.stop() 

# Khởi tạo bộ nhớ dữ liệu hình vẽ
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'generated_fig' not in st.session_state:
    st.session_state.generated_fig = None

# --- 3. KHU VỰC CẤU HÌNH NÉT VẼ & XUẤT BẢN TRÊN TRANG CHÍNH ---
st.markdown('<div style="background-color: #F8FAFC; padding: 10px; border-left: 5px solid #64748B; border-radius: 4px; margin-bottom: 15px;"><h4 style="margin: 0; color: #475569;">⚙️ CẤU HÌNH ĐỒ HỌA & ĐẦU RA</h4></div>', unsafe_allow_html=True)

col_config_1, col_config_2 = st.columns(2)

with col_config_1:
    st.markdown("**🎨 TÙY CHỈNH NÉT VẼ**")
    cc1, cc2, cc3 = st.columns([1, 1.5, 1.5])
    with cc1:
        line_color = st.color_picker("Màu nét chính:", "#1f77b4")
    with cc2:
        line_width = st.slider("Độ dày nét vẽ:", 1.0, 5.0, 2.0, 0.5)
    with cc3:
        font_size = st.slider("Kích thước chữ chú thích:", 8, 20, 12, 1)

with col_config_2:
    st.markdown("**💾 CẤU HÌNH XUẤT BẢN**")
    cc4, cc5 = st.columns(2)
    with cc4:
        img_format = st.selectbox("Định dạng ảnh:", ["png", "jpg", "svg", "pdf"])
    with cc5:
        dpi_resolution = st.selectbox("Độ phân giải (DPI):", [150, 300, 600], index=1)

config_dict = {
    "line_color": line_color,
    "line_width": line_width,
    "font_size": font_size
}

st.divider()

# --- 4. GIAO DIỆN CHÍNH CỦA ỨNG DỤNG ---
tabs = st.tabs(["| 🔮 Vẽ Hình Tự Động", "| 📚 Lịch Sử & Xuất Word Hàng Loạt", "| 💡 Hướng Dẫn & Ví Dụ"])

# TAB 1: VẼ HÌNH TỰ ĐỘNG
with tabs[0]:
    col_input, col_render = st.columns([1, 1.2])
    
    with col_input:
        st.markdown('<div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;"><h4 style="margin: 0; color: #0369A1;">📤 Nhập Đề Bài/Upload File</h4></div>', unsafe_allow_html=True)
        mode = st.radio("Loại bài toán:", ["Hình học (THCS/THPT/Tọa độ)", "Đồ thị hàm số"], horizontal=True)
        mode_key = 'geometry' if "Hình học" in mode else 'function'
        
        uploaded_file = st.file_uploader("Tải lên Ảnh đề bài, file PDF hoặc file Word chứa đề toán:", type=["png", "jpg", "jpeg", "pdf", "docx"])
        prompt = st.text_area("Yêu cầu cụ thể hoặc đề bài dạng văn bản:", placeholder="Vẽ đồ thị hàm số y=2x^2", height=80)
        btn_generate = st.button("🚀 AI Phân Tích Đề & Vẽ Hình", type="primary", use_container_width=True)
        
        if btn_generate:
            # KIỂM TRA BỔ SUNG ĐỂ TRÁNH LỖI PHÁT SINH TỪ HÀNG ĐỢI SỰ KIỆN CỦA STREAMLIT
            if ai_engine is None:
                st.error("Hệ thống chưa sẵn sàng do thiếu API Key. Vui lòng làm mới lại trang hoặc nhập key tại Trang chủ.")
            elif uploaded_file is None and (not prompt.strip() or prompt == "Hãy phân tích đề bài và vẽ hình minh họa."):
                st.error("Vui lòng tải file đề bài lên hoặc nhập nội dung văn bản đề bài cụ thể!")
            else:
                with st.spinner("AI đang phân tích dữ kiện hình học và lập trình tọa độ..."):
                    result = ai_engine.analyze_and_generate_code(
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
        st.markdown('<div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;"><h4 style="margin: 0; color: #0369A1;">🖼️ Kết Quả Trực Quan</h4></div>', unsafe_allow_html=True)
        if st.session_state.generated_fig:
            st.pyplot(st.session_state.generated_fig)
            img_buf = GeometryEngine.convert_fig_to_image(st.session_state.generated_fig, dpi=dpi_resolution, format=img_format)
            st.download_button(
                label=f"📥 Tải xuống ảnh (. {img_format.upper()} - {dpi_resolution} DPI)",
                data=img_buf,
                file_name=f"math_drawing.{img_format}",
                mime=f"image/{img_format}",
                use_container_width=True, type="primary"
            )
        else:
            st.info("Hình vẽ minh họa sẽ hiển thị ở đây sau khi bạn nhấn nút 'AI Phân Tích Đề & Vẽ Hình'.")

    st.divider()
    st.subheader("💻 Mã Python Tạo Hình (AI sinh tự động)")
    if st.session_state.current_code:
        edited_code = st.text_area("Bạn có thể tùy chỉnh hoặc sao chép đoạn mã này để chạy độc lập:", value=st.session_state.current_code, height=250)
        if st.button("🔄 Cập nhật hình vẽ bằng mã đã sửa", type="primary"):
            try:
                fig = GeometryEngine.execute_drawing_code(edited_code, config_dict)
                st.session_state.generated_fig = fig
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi thực thi mã chỉnh sửa: {str(e)}")
    else:
        st.code("# Chưa có mã nào được sinh ra", language="python")

# TAB 2: XUẤT FILE WORD HÀNG LOẠT
with tabs[1]:
    st.markdown('<div style="background-color: #E0F2FE; padding: 4px; border-left: 5px solid #0284C7; border-radius: 4px; margin-bottom: 10px;"><h4 style="margin: 0; color: #0369A1;">📚 Quản lý thư viện hình đã vẽ & Xuất tài liệu Word</h4></div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.info("Chưa có bài toán nào trong lịch sử phiên làm việc này.")
    else:
        st.write(f"Hiện đang lưu trữ **{len(st.session_state.history)}** hình vẽ.")
        selected_indices = []
        for idx, item in enumerate(st.session_state.history):
            if st.checkbox(f"Bài toán {idx+1}: {item['prompt'][:80]}...", value=True, key=f"hist_{idx}"):
                selected_indices.append(idx)
        
        if st.button("📝 Xuất hình Các Bài Đã Chọn Sang Microsoft Word (.docx)", type="primary"):
            if not selected_indices:
                st.warning("Vui lòng chọn ít nhất một hình vẽ!")
            else:
                with st.spinner("Đang đóng gói file Word..."):
                    exporter = DocxExporter()
                    for order, idx in enumerate(selected_indices, 1):
                        item = st.session_state.history[idx]
                        img_stream = GeometryEngine.convert_fig_to_image(item['fig'], dpi=300, format='png')
                        exporter.add_math_problem(order, item['prompt'], img_stream)
                    
                    st.download_button(
                        label="📥 Click để Tải File Word (.docx) Về Máy",
                        data=exporter.save(),
                        file_name="Giao_An_Hinh_Hoc_AI.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True, type="primary"
                    )

# TAB 3: HƯỚNG DẪN
with tabs[2]:
    st.markdown("""
    ### 📖 Hướng dẫn sử dụng nhanh:
    1. **Đồng bộ khóa**: Hãy chắc chắn bạn đã nhập Gemini API Key tại Trang Chủ.
    2. **Đưa tài liệu lên**: Nhập chữ hoặc tải file Ảnh, PDF, Word chứa đề bài.
    3. **Chỉ thị cho AI**: Gõ yêu cầu cụ thể và nhấn nút vẽ hình.
    4. **Tải về**: Tùy chỉnh màu sắc nét vẽ ở khu vực cấu hình phía trên và tải ảnh hoặc file Word về máy.
    """)

# --- 5. FOOTER CỐ ĐỊNH ---
st.divider()
col_left, col_right = st.columns(2)
with col_left:
    st.caption("Phát triển bởi Ngo Thanh Hung © 2026")
with col_right:
    st.markdown("<div style='text-align: right; color: gray; font-size: 0.85em;'>AI có thể mắc lỗi. Cần kiểm tra kỹ các thông tin quan trọng.</div>", unsafe_allow_html=True)
