import streamlit as st
import io
import re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Khối import linh hoạt tránh lỗi đường dẫn hệ thống
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

def export_refined_docx(topic, refined_text):
    """Đóng gói văn bản đã được AI tối ưu hóa sang file Word chuẩn Nghị định 30/2020/NĐ-CP"""
    doc = Document()
    
    # 1. Định dạng lề chuẩn Hành chính (Top 20mm, Bottom 20mm, Left 30mm, Right 15mm)
    for section in doc.sections:
        section.top_margin = Inches(20 / 25.4)
        section.bottom_margin = Inches(20 / 25.4)
        section.left_margin = Inches(30 / 25.4)
        section.right_margin = Inches(15 / 25.4)
        section.page_width = Inches(210 / 25.4)
        section.page_height = Inches(297 / 25.4)

    # Cấu hình phông chữ mặc định toàn văn bản
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    
    # 2. Tiêu ngữ Quốc hiệu song song dạng bảng ẩn
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(4.2)
    
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_left.add_run("SỞ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG THCS ...").bold = True
    p_left.runs[0].font.size = Pt(12)
    
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_r1 = p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    r_r1.bold = True
    r_r1.font.size = Pt(12)
    r_r2 = p_right.add_run("Độc lập - Tự do - Hạnh phúc\n_______________")
    r_r2.bold = True
    r_r2.font.size = Pt(13)

    # Khoảng trống xuống đề tài
    doc.add_paragraph().paragraph_format.space_before = Pt(24)

    # 3. Tiêu đề đề tài sáng kiến
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_t1 = p_title.add_run("BÁO CÁO SÁNG KIẾN KINH NGHIỆM (BẢN ĐÃ TỐI ƯU HÓA)\n")
    r_t1.bold = True
    r_t1.font.size = Pt(14)
    
    clean_topic = topic.replace('"', '').replace('“', '').replace('”', '').replace('*', '').strip()
    r_t2 = p_title.add_run(f"“{clean_topic.upper()}”")
    r_t2.bold = True
    r_t2.font.size = Pt(15)

    # 4. Quét biên dịch nội dung từ AI (Khử sạch Markdown rác)
    lines = refined_text.split('\n')
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line == "---":
            continue
            
        if cleaned_line.startswith('#'):
            cleaned_line = re.sub(r'^#+\s*', '', cleaned_line)
            is_heading = True
        else:
            is_heading = False
            
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        is_bullet = False
        if cleaned_line.startswith(('* ', '- ', '• ')):
            cleaned_line = re.sub(r'^[\*\-\•]\s*', '', cleaned_line)
            is_bullet = True
            p.paragraph_format.left_indent = Inches(0.4)
        
        is_admin_heading = cleaned_line.upper().startswith(("ĐẶT VẤN ĐỀ", "GIẢI PHÁP", "NỘI DUNG", "KẾT LUẬN", "KẾT QUẢ")) or re.match(r'^(\d+|\d+\.\d+|[I|V|X]+)\.\s*', cleaned_line)
        
        if is_heading or is_admin_heading:
            p.paragraph_format.space_before = Pt(12)
            if re.match(r'^\d+\.\d+', cleaned_line):
                p.paragraph_format.first_line_indent = Inches(0.5)
        elif not is_bullet:
            p.paragraph_format.first_line_indent = Inches(0.5)

        # Xử lý in đậm nội hàm (Inline bold **)
        parts = re.split(r'(\*\*.*?\*\*)', cleaned_line)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                text_run = part.replace('**', '')
                run = p.add_run(text_run)
                run.bold = True
            else:
                if part:
                    run = p.add_run(part)
                    if is_heading or is_admin_heading:
                        run.bold = True
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def show_docx_processor_module(api_key=None):
    st.subheader("📂 Trợ Lý AI Hiệu Đính & Tự Động Biên Tập File Word")
    st.info("Hệ thống sẽ đọc file bản nháp, tự động phát hiện câu từ lỗi, chỉnh sửa chuẩn hóa văn phong sư phạm và xuất bản file Word mới.")
    
    uploaded_file = st.file_uploader("Tải lên bản nháp Sáng kiến kinh nghiệm của thầy (.docx)", type=["docx"])
    
    if uploaded_file is not None:
        st.success("✅ Đã tải tệp lên thành công!")
        
        # Nhập tên đề tài trực tiếp để AI làm căn cứ định vị tiêu đề Word
        doc_title = st.text_input("Xác nhận hoặc nhập lại Tên Đề Tài để xuất file:", value="Ứng dụng công nghệ AI nâng cao hiệu quả dạy học")
        
        if st.button("🧠 Kích hoạt AI tự động sửa đổi & Xuất bản Word mới"):
            with st.spinner("AI đang quét sâu văn bản, hiệu đính lỗi và tối ưu hóa cấu trúc nội dung..."):
                try:
                    # Đọc nội dung file Word tải lên
                    doc = Document(uploaded_file)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            full_text.append(paragraph.text)
                    
                    text_content = "\n".join(full_text)
                    preview_text = text_content[:8000] # Lấy vùng nội dung cốt lõi
                    
                    if len(text_content) == 0:
                        st.error("❌ File Word không chứa dữ liệu chữ.")
                        return
                    
                    # Câu lệnh ép AI chỉnh sửa trực tiếp vào nội dung text thay vì nhận xét suông
                    prompt = f"""
                    Bạn là Chuyên gia Hiệu đính và Biên tập viên cao cấp của Tạp chí Khoa học Giáo dục Việt Nam.
                    Hãy đọc kỹ đoạn văn bản trích từ bản nháp Sáng kiến kinh nghiệm sau đây, thực hiện sửa lỗi chính tả, viết lại các câu văn phong nói thành văn phong hành chính sư phạm trang trọng, bổ sung liên kết logic giữa các luận điểm để văn bản đạt chất lượng tốt nhất.
                    
                    --- NỘI DUNG BẢN NHÁP GỐC ---
                    {preview_text}
                    ----------------------------
                    
                    YÊU CẦU ĐẦU RA:
                    - Viết lại toàn bộ văn bản hoàn chỉnh đã được sửa đổi và tối ưu. Không đưa ra lời nhận xét giải thích dài dòng như "Tôi đã sửa...", chỉ trả về nội dung bài viết sau khi sửa.
                    - Giữ nguyên cấu trúc các mục chính (Đặt vấn đề, Biện pháp, Kết quả...).
                    - Định dạng đầu ra bằng Markdown sạch gọn để hệ thống đồng bộ hóa.
                    """
                    
                    # Gọi AI xử lý dữ liệu dòng chảy (Stream)
                    refined_response = call_ai_stream(
                        prompt=prompt,
                        system_instruction="Bạn là Giáo sư, Viện trưởng Viện Khoa học Giáo dục Việt Nam. Nhiệm vụ của bạn là hiệu đính trực tiếp văn bản.",
                        api_key=api_key
                    )
                    
                    st.markdown("### 📝 Nội dung đã được Trợ lý AI tinh chỉnh và làm sạch:")
                    st.markdown(refined_response)
                    st.markdown("---")
                    
                    # Tiến hành đóng gói dữ liệu đã chỉnh sửa thành file Word chuẩn hành chính
                    docx_bytes = export_refined_docx(doc_title, refined_response)
                    
                    # Hiển thị nút tải file Word chuẩn Nghị định 30 ngay lập tức
                    st.download_button(
                        label="📥 Tải Bản Sáng Kiến Đã Tối Ưu Hóa (.docx) - Chuẩn Hành Chính",
                        data=docx_bytes,
                        file_name=f"SKKN_Da_Hieu_Dinh_{doc_title.replace(' ', '_')[:25]}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("✨ Đã tạo file Word thành công! File tải về đã tự động khóa phông Times New Roman cỡ 14, căn lề lọt lòng chuẩn hành chính.")
                    
                except Exception as e:
                    st.error(f"❌ Lỗi trong quá trình biên tập dữ liệu: {str(e)}")
