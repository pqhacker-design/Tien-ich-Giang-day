import streamlit as st
import io
import re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Khối import linh hoạt để tránh lỗi đường dẫn hệ thống trên Streamlit Cloud
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

def export_refined_docx(topic, refined_text):
    """Đóng gói văn bản đã được AI hiệu đính sang file Word chuẩn Nghị định 30/2020/NĐ-CP"""
    doc = Document()
    
    # 1. Cấu hình lề trang chuẩn hành chính (Top 20mm, Bottom 20mm, Left 30mm, Right 15mm)
    for section in doc.sections:
        section.top_margin = Inches(20 / 25.4)
        section.bottom_margin = Inches(20 / 25.4)
        section.left_margin = Inches(30 / 25.4)
        section.right_margin = Inches(15 / 25.4)
        section.page_width = Inches(210 / 25.4)
        section.page_height = Inches(297 / 25.4)

    # Cấu hình Style mặc định (Times New Roman, 14pt)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    
    # 2. PHẦN TIÊU NGỮ & QUỐC HIỆU (Bảng ẩn 2 cột chuẩn văn thư)
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(4.2)
    
    # Cột 1: Đơn vị công tác
    cell_left = table.cell(0, 0)
    p_left = cell_left.paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_left.add_run("SỞ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG THCS ...").bold = True
    p_left.runs[0].font.size = Pt(12)
    
    # Cột 2: Quốc hiệu - Tiêu ngữ
    cell_right = table.cell(0, 1)
    p_right = cell_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_r1 = p_right.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    r_r1.bold = True
    r_r1.font.size = Pt(12)
    r_r2 = p_right.add_run("Độc lập - Tự do - Hạnh phúc\n_______________")
    r_r2.bold = True
    r_r2.font.size = Pt(13)

    # Khoảng trống xuống tên đề tài
    doc.add_paragraph().paragraph_format.space_before = Pt(24)

    # 3. TÊN ĐỀ TÀI SÁNG KIẾN KINH NGHIỆM
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_t1 = p_title.add_run("BÁO CÁO SÁNG KIẾN KINH NGHIỆM (BẢN ĐÃ HIỆU ĐÍNH)\n")
    r_t1.bold = True
    r_t1.font.size = Pt(14)
    
    clean_topic = topic.replace('"', '').replace('“', '').replace('”', '').replace('*', '').strip()
    r_t2 = p_title.add_run(f"“{clean_topic.upper()}”")
    r_t2.bold = True
    r_t2.font.size = Pt(15)

    # 4. QUÉT BIÊN DỊCH NỘI DUNG NÂNG CAO (Lọc sạch các ký tự Markdown rác)
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
        p.paragraph_format.line_spacing = 1.3  # Giãn dòng 1.3 lines chuẩn
        p.paragraph_format.space_after = Pt(6)   # Cách đoạn dưới 6pt
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY # Căn đều hai bên
        
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

        # Xử lý bóc tách in đậm cục bộ (Inline bold **) do AI trả ra
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
    st.subheader("📂 Trợ Lý AI Phân Tích & Thẩm Định Bản Nháp Word")
    st.info("Hỗ trợ đọc file .docx, tự động phát hiện lỗi chính tả, câu từ sư phạm và đánh giá cấu trúc theo quy chuẩn.")
    
    # Tải file Word lên hệ thống
    uploaded_file = st.file_uploader("Tải lên bản nháp Sáng kiến kinh nghiệm của thầy (.docx)", type=["docx"])
    
    if uploaded_file is not None:
        st.success("✅ Đã tải tệp lên thành công!")
        
        # Nhập tên đề tài để định hình tiêu đề chính xác khi kết xuất tệp Word
        doc_title = st.text_input("Xác nhận hoặc nhập Tên Đề Tài để xuất file (.docx):", value="Ứng dụng công nghệ đổi mới phương pháp dạy học")
        
        # Nút bấm kích hoạt AI quét văn bản
        if st.button("🧠 Kích hoạt AI quét và kiểm tra toàn diện"):
            with st.spinner("AI đang đọc dữ liệu văn bản và tiến hành thẩm định..."):
                try:
                    # 1. Tiến hành đọc toàn bộ nội dung từ file Word
                    doc = Document(uploaded_file)
                    full_text = []
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            full_text.append(paragraph.text)
                    
                    text_content = "\n".join(full_text)
                    preview_text = text_content[:8000]
                    
                    if len(text_content) == 0:
                        st.error("❌ File Word của thầy không có nội dung chữ hoặc nội dung nằm hoàn toàn trong bảng biểu/hình ảnh.")
                        return

                    st.info(f"📋 Hệ thống đã ghi nhận đoạn văn bản dài {len(text_content)} ký tự.")
                    
                    # --- LUỒNG 1: PHÂN TÍCH & THẨM ĐỊNH (Giữ nguyên cấu trúc gốc của thầy) ---
                    analysis_prompt = f"""
                    Bạn là Thư ký Hội đồng Khoa học Giáo dục kiêm chuyên gia hiệu đính văn bản học thuật.
                    Hãy phân tích và kiểm tra đoạn văn bản trích từ bản nháp Sáng kiến kinh nghiệm dưới đây:
                    
                    --- NỘI DUNG VĂN BẢN ---
                    {preview_text}
                    ------------------------
                    
                    Let's provide the critique.
                    Hãy đưa ra báo cáo thẩm định chi tiết theo các mục sau (sử dụng định dạng Markdown):
                    1. 📝 ĐÁNH GIÁ VĂN PHONG SƯ PHẠM: (Kiểm tra xem câu từ đã chuẩn hành chính chưa, có bị sáo rỗng hoặc dùng ngôn ngữ nói không? Chỉ ra từ ngữ cần sửa nếu có).
                    2. 📐 ĐÁNH GIÁ CẤU TRÚC KHOA HỌC: (Các phần Đặt vấn đề, Biện pháp đã logic chưa? Các biện pháp có tính mới, tính đột phá và ứng dụng công nghệ/AI/chuyển đổi số không?).
                    3. 📈 ĐÁNH GIÁ TÍNH MINH CHỨNG: (Số liệu thực nghiệm, kết quả giả định hoặc các biểu mẫu đi kèm đã đủ thuyết phục hội đồng chấm chưa?).
                    4. 🛠️ ĐỀ XUẤT HƯỚNG SỬA ĐỔI: (Đưa ra ít nhất 3 gợi ý cụ thể để thầy cô bổ sung, chỉnh sửa nhằm nâng cao tỷ lệ đạt giải cao).
                    """
                    
                    st.markdown("### 📊 1. Kết quả Thẩm định từ Trợ lý AI:")
                    ai_analysis = call_ai_stream(
                        prompt=analysis_prompt,
                        system_instruction="Bạn là Giáo sư, Viện trưởng Viện Khoa học Giáo dục Việt Nam.",
                        api_key=api_key
                    )
                    
                    # --- LUỒNG 2: TỰ ĐỘNG BIÊN TẬP VÀ XUẤT FILE WORD CHỈNH SỬA ---
                    st.markdown("---")
                    st.markdown("### 📝 2. Bản thảo Sáng kiến sau khi AI tự động sửa đổi trực tiếp:")
                    
                    refine_prompt = f"""
                    Bạn là Chuyên gia biên tập cấp cao của Bộ Giáo dục và Đào tạo. 
                    Dựa vào đoạn bản nháp dưới đây, hãy tiến hành sửa toàn bộ lỗi chính tả, chuyển đổi các câu văn nói thành câu văn hành chính sư phạm mượt mà, chuyên nghiệp và tăng tính khoa học.
                    
                    --- NỘI DUNG BẢN NHÁP GỐC ---
                    {preview_text}
                    ----------------------------
                    
                    YÊU CẦU: Chỉ viết lại nội dung bài viết hoàn chỉnh sau khi chỉnh sửa dưới dạng Markdown sạch. Không thêm lời chào, không viết nhận xét dài dòng như "Tôi đã sửa...".
                    """
                    
                    ai_refined_text = call_ai_stream(
                        prompt=refine_prompt,
                        system_instruction="Nhiệm vụ của bạn là hiệu đính, viết lại văn bản sư phạm một cách mượt mà và trực tiếp.",
                        api_key=api_key
                    )
                    
                    # Tạo file Word nhị phân từ bản đã hiệu đính
                    docx_bytes = export_refined_docx(doc_title, ai_refined_text)
                    
                    # Hiển thị nút tải file Word chuẩn Nghị định 30
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.download_button(
                        label="📥 Tải Bản Sáng Kiến Đã Chỉnh Sửa Hoàn Thiện (.docx)",
                        data=docx_bytes,
                        file_name=f"SKKN_Da_Chinh_Sua_{doc_title.replace(' ', '_')[:25]}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                    st.success("✨ Đã đóng gói thành công file Word! Bấm nút phía trên để tải về bản chỉnh sửa hoàn thiện lề lối hành chính.")
                    
                except Exception as e:
                    st.error(f"❌ Có lỗi xảy ra khi xử lý cấu trúc file Word: {str(e)}")
