import streamlit as st
import json
from modules.doc_reader import read_docx, read_pdf
from modules.ppt_ai import generate_powerpoint_data_ai
from modules.ppt_export import create_powerpoint_file

st.set_page_config(page_title="Trợ lý Tạo PowerPoint Bài Giảng 4.0", page_icon="📊", layout="wide")

st.markdown("## 📊 Trợ lý Tự động Tạo PowerPoint Bài Giảng 4.0")
st.caption("Sinh bài giảng điện tử (.pptx) cấu trúc chuẩn sư phạm, kèm ghi chú Notes giảng dạy đầy đủ chỉ với một nút bấm.")
st.markdown("---")

# Kiểm tra API Key từ session_state trang chủ
api_key = st.session_state.get("gemini_api_key", "")
if not api_key:
    st.warning("⚠️ Chưa phát hiện Gemini API Key từ trang chủ. Vui lòng nhập khóa API tại thanh cấu hình trang chủ hoặc nhập bổ sung dưới đây:")
    api_key = st.text_input("Nhập bổ sung Gemini API Key:", type="password")

# Cấu hình tham số thông tin cho Slide
col_meta1, col_meta2, col_meta3 = st.columns(3)
with col_meta1:
    subject_input = st.text_input("Môn học bài giảng:", "Toán học")
    teacher_name = st.text_input("Tên giáo viên lên lớp:", "Thầy Ngô Hùng")
with col_meta2:
    grade_input = st.text_input("Khối lớp bài giảng:", "Lớp 8")
    school_name = st.text_input("Tên trường học:", "Trường THCS")
with col_meta3:
    style_select = st.selectbox("Phong cách & Lứa tuổi học sinh:", ["Tiểu học", "THCS", "THPT"], index=1)
    duration_input = st.text_input("Thời lượng tiết dạy PowerPoint:", "2 Tiết")

st.markdown("---")
st.subheader("1. Nguồn dữ liệu cung cấp cho AI phân tích")
source_option = st.radio("Chọn nguồn dữ liệu đầu vào:", 
                         ["📂 Tải file Giáo án cũ (.docx, .pdf)", "📝 Nhập nội dung chủ đề/văn bản trực tiếp"], 
                         horizontal=True)

raw_source_text = ""

if "📂" in source_option:
    uploaded_file = st.file_uploader("Tải file Giáo án gốc của thầy vào đây:", type=["docx", "pdf"])
    if uploaded_file:
        file_bytes = uploaded_file.read()
        if uploaded_file.name.endswith(".docx"):
            raw_source_text = read_docx(file_bytes)
        elif uploaded_file.name.endswith(".pdf"):
            raw_source_text = read_pdf(file_bytes)
        st.success(f"Đã nạp thành công dữ liệu file: {uploaded_file.name}")
else:
    raw_source_text = st.text_area("Nhập tên bài học, phân phối chương trình hoặc tóm tắt kiến thức SGK tại đây:", 
                                   height=200, placeholder="Ví dụ: Bài Định lí Pythagore - Toán 8 Kết nối tri thức...")

# Nút lệnh kích hoạt quy trình 1 nút bấm đặc biệt
st.markdown("---")
if st.button("🎯 KÍCH HOẠT QUY TRÌNH 1 NÚT BẤM - SINH SLIDE BÀI GIẢNG", type="primary", use_container_width=True):
    if not api_key:
        st.error("Lỗi: Hệ thống yêu cầu phải có Gemini API Key để xử lý thiết kế nội dung.")
    elif not raw_source_text.strip():
        st.warning("Vui lòng tải file hoặc điền thông tin nội dung cốt lõi để AI phân tích cấu trúc bài giảng.")
    else:
        with st.spinner("🚀 Trợ lý AI đang bóc tách chuỗi sư phạm, tinh gọn nội dung, sinh câu hỏi tương tác và thiết lập Notes giảng dạy..."):
            
            meta_payload = {
                "subject": subject_input,
                "grade": grade_input,
                "duration": duration_input,
                "teacher": teacher_name,
                "school": school_name
            }
            
            # Bước 1 & 2: Gọi AI phân tích và trả về cấu trúc Slide JSON
            ppt_json = generate_powerpoint_data_ai(api_key, raw_source_text, meta_payload, style_select)
            
            if "error" in ppt_json:
                st.error(ppt_json["error"])
            else:
                st.session_state["generated_ppt_json"] = ppt_json
                st.success("🎉 AI đã biên soạn cấu trúc slide thành công! Xem trước phân phối chi tiết bên dưới.")

# Hiển thị kết quả preview trực quan và nút Download file thành phẩm hành chính
if "generated_ppt_json" in st.session_state:
    slide_data = st.session_state["generated_ppt_json"]
    
    st.markdown("### 👁️ Bản xem trước cấu trúc bài giảng & Ghi chú giảng dạy (Teacher Notes)")
    
    for idx, s in enumerate(slide_data.get("slides", [])):
        with st.container(border=True):
            st.markdown(f"#### 🖥️ Slide {idx + 1}: {s.get('title', 'Nội dung')} (Loại: *{s.get('type','content')}*)")
            
            if s.get("type") == "quiz":
                st.write(f"**Câu hỏi:** {s.get('question')}")
                for opt in s.get("options", []):
                    st.write(f" ❑ {opt}")
            elif "bullets" in s:
                for b in s.get("bullets", []):
                    st.write(f"• {b}")
            else:
                st.write(s.get("body", s.get("content", "")))
                
            if s.get("prompt_image"):
                st.caption(f"🎨 **Ý tưởng hình ảnh minh họa AI đề xuất:** *{s.get('prompt_image')}*")
                
            st.markdown(f"<div style='background-color:#F0FDF4; padding:8px; border-radius:4px; font-size:0.9em; color:#166534;'><b>💡 Lời thoại/Ghi chú của Thầy khi chiếu slide này (Notes):</b><br/>{s.get('notes')}</div>", unsafe_allow_html=True)
            
    # Tiến hành xuất bản file vật lý thông qua python-pptx
    ppt_file_stream = create_powerpoint_file(slide_data, style_select)
    
    # Định dạng tên file chuẩn hành chính không dấu: MonHoc_Lop_BaiHoc.pptx
    clean_subject = "".join(c for c in subject_input if c.isalnum())
    clean_grade = "".join(c for c in grade_input if c.isalnum())
    
    st.markdown("---")
    st.download_button(
        label="📥 TẢI XUỐNG BÀI GIẢNG POWERPOINT (.PPTX) HOÀN CHỈNH",
        data=ppt_file_stream,
        file_name=f"{clean_subject}_{clean_grade}_BaiGiangDienTu.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True
    )