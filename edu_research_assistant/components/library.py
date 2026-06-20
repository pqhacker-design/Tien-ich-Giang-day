import streamlit as st
import io
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Import hàm gọi AI từ lõi hệ thống
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

def export_to_docx_admin_format(topic, content_text):
    """
    Xuất nội dung văn bản sang file Word chuẩn định dạng hành chính Nghị định 30/2020/NĐ-CP
    Đã tích hợp bộ lọc bóc tách ký tự Markdown (** , ### , * ) tránh lỗi hiển thị chữ thô.
    """
    import re
    doc = Document()
    
    # 1. Cấu hình lề trang chuẩn (Top 20mm, Bottom 20mm, Left 30mm, Right 15mm)
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
    
    # --- PHẦN TIÊU NGỮ & QUỐC HIỆU (Bảng ẩn 2 cột) ---
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(4.2)
    
    # Cột 1: Đơn vị
    cell_left = table.cell(0, 0)
    p_left1 = cell_left.paragraphs[0]
    p_left1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_l1 = p_left1.add_run("SỞ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG THCS ...")
    run_l1.font.name = 'Times New Roman'
    run_l1.font.size = Pt(12)
    run_l1.bold = True
    
    p_left2 = cell_left.add_paragraph()
    p_left2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_left2.paragraph_format.space_before = Pt(4)
    p_left2.add_run("-------").font.size = Pt(12)
    
    # Cột 2: Quốc hiệu Tiêu ngữ
    cell_right = table.cell(0, 1)
    p_right1 = cell_right.paragraphs[0]
    p_right1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_r1 = p_right1.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    run_r1.bold = True
    run_r1.font.size = Pt(12)
    
    run_r2 = p_right1.add_run("Độc lập - Tự do - Hạnh phúc")
    run_r2.bold = True
    run_r2.font.size = Pt(13)
    
    p_right2 = cell_right.add_paragraph()
    p_right2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_right2.paragraph_format.space_before = Pt(2)
    p_right2.add_run("_______________").bold = True

    # Khoảng cách xuống tên đề tài
    doc.add_paragraph().paragraph_format.space_before = Pt(24)

    # --- TÊN ĐỀ TÀI SÁNG KIẾN ---
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_title_lbl = p_title.add_run("BÁO CÁO SÁNG KIẾN KINH NGHIỆM\n")
    r_title_lbl.bold = True
    r_title_lbl.font.size = Pt(14)
    
    # Làm sạch tên đề tài nếu dính dấu ngoặc kép hoặc dấu sao của AI
    clean_topic = topic.replace('"', '').replace('“', '').replace('”', '').replace('*', '').strip()
    r_title_val = p_title.add_run(f"“{clean_topic.upper()}”")
    r_title_val.bold = True
    r_title_val.font.size = Pt(15)

    # --- BỘ LỌC VÀ BIÊN DỊCH VĂN BẢN CHUẨN ---
    lines = content_text.split('\n')
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line == "---":
            continue
            
        # 1. Khử toàn bộ các ký tự Tiêu đề Markdown (###, ##, #)
        if cleaned_line.startswith('#'):
            cleaned_line = re.sub(r'^#+\s*', '', cleaned_line)
            is_heading = True
        else:
            is_heading = False
            
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3  # Giãn dòng 1.3 lines chuẩn
        p.paragraph_format.space_after = Pt(6)   # Cách đoạn dưới 6pt
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY # Căn đều hai bên
        
        # 2. Xử lý định dạng mục Đầu dòng / Danh sách (Bullet points hoặc dấu *)
        is_bullet = False
        if cleaned_line.startswith(('* ', '- ', '• ')):
            cleaned_line = re.sub(r'^[\*\-\•]\s*', '', cleaned_line)
            is_bullet = True
            p.paragraph_format.left_indent = Inches(0.4) # Thụt lề đoạn danh sách
        
        # Định nghĩa quy tắc in đậm cho tiêu đề lớn chuẩn hành chính
        is_admin_heading = cleaned_line.upper().startswith(("ĐẶT VẤN ĐỀ", "GIẢI PHÁP", "NỘI DUNG", "KẾT LUẬN", "KẾT QUẢ")) or re.match(r'^(\d+|\d+\.\d+|[I|V|X]+)\.\s*', cleaned_line)
        
        if is_heading or is_admin_heading:
            p.paragraph_format.space_before = Pt(12)
            # Tự động thụt lề 1.25cm nếu là tiêu đề tiểu mục nhỏ (ví dụ: 2.1. Lý do chọn đề tài)
            if re.match(r'^\d+\.\d+', cleaned_line):
                p.paragraph_format.first_line_indent = Inches(0.5)
        elif not is_bullet:
            # Thụt lề dòng đầu tiên 1.25cm đối với đoạn văn thường
            p.paragraph_format.first_line_indent = Inches(0.5)

        # 3. Sử dụng Regex bóc tách chuỗi **in đậm** ở giữa câu do AI sinh ra
        # Tách chuỗi theo cặp dấu **
        parts = re.split(r'(\*\*.*?\*\*)', cleaned_line)
        
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # Phần chữ nằm trong cặp dấu ** -> Bỏ dấu sao và đặt thuộc tính in đậm
                text_run = part.replace('**', '')
                run = p.add_run(text_run)
                run.bold = True
            else:
                # Phần chữ thường
                if part:
                    run = p.add_run(part)
                    if is_heading or is_admin_heading:
                        run.bold = True
            
            run.font.name = 'Times New Roman'
            run.font.size = Pt(14)
            
    # Ghi dữ liệu ra bộ nhớ đệm bytes
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.getvalue()

def show_library_module(api_key=None):
    st.subheader("📚 Thư Viện Tra Cứu & Tự Động Sinh Sáng Kiến Mẫu")
    st.info("Thầy/Cô có thể tra cứu các mẫu có sẵn hoặc gõ một tên đề tài bất kỳ để AI tự động xây dựng một bản sáng kiến mẫu hoàn chỉnh.")

    # --- TÍNH NĂNG CAO CẤP: AI TỰ SINH SÁNG KIẾN MẪU THEO TÊN NGƯỜI DÙNG GÕ ---
    st.markdown("### 🤖 Tính năng: Tự động biên soạn Sáng kiến mẫu theo yêu cầu")
    
    user_topic = st.text_input(
        "✍️ Nhập tên Đề tài/Sáng kiến thầy cô muốn tạo mẫu:",
        placeholder="Ví dụ: Ứng dụng AI và chuyển đổi số nâng cao hiệu quả dạy học môn Toán lớp 8"
    )
    
    if st.button("🔥 Kích hoạt AI biên soạn Bản mẫu Sư phạm"):
        if not user_topic.strip():
            st.warning("⚠️ Vui lòng nhập tên đề tài trước khi bấm tạo mẫu.")
        else:
            with st.spinner("🧠 AI đang phân tích bối cảnh, tra cứu thuật ngữ và biên soạn bản mẫu..."):
                prompt = f"""
                Hãy đóng vai là Chuyên gia Khoa học Sư phạm cấp cao của Bộ Giáo dục và Đào tạo Việt Nam.
                Xây dựng một BẢN SÁNG KIẾN KINH NGHIỆM MẪU chi tiết cho đề tài: "{user_topic}".
                
                Yêu cầu cấu trúc nội dung sinh ra phải bao gồm đầy đủ các phần sau:
                1. TÊN ĐỀ TÀI (Chuẩn hóa lại nếu cần)
                2. ĐẶT VẤN ĐỀ
                   - Lý do chọn đề tài (Nêu bật tính cấp thiết và thực trạng khó khăn tại trường học).
                   - Mục đích nghiên cứu.
                3. GIẢI PHÁP THỰC HIỆN (Biên soạn chi tiết ít nhất 3 biện pháp cốt lõi, đột phá, có ứng dụng công nghệ hoặc đổi mới phương pháp).
                4. KẾT QUẢ ĐẠT ĐƯỢC (Đưa ra các số liệu định lượng, tỷ lệ % tăng trưởng giả định một cách khoa học).
                5. KẾT LUẬN & KIẾN NGHỊ (Bài học kinh nghiệm và đề xuất với nhà trường/Sở GD&ĐT).
                
                Văn phong yêu cầu: Nghiêm túc, mang tính học thuật ngành giáo dục Việt Nam, lập luận chặt chẽ, không sáo rỗng.
                """
                
                generated_sample = call_ai_stream(
                    prompt=prompt, 
                    system_instruction="Bạn là Giáo sư Viện Khoa học Giáo dục Việt Nam.", 
                    api_key=api_key
                )
                
                st.success("🎉 Đã biên soạn thành công bản mẫu sư phạm!")
                st.markdown("---")
                st.markdown(generated_sample)
                st.markdown("---")
                
                # --- TỰ ĐỘNG XỬ LÝ VÀ CHUYỂN ĐỔI SANG FILE WORD (.DOCX) CHUẨN ---
                try:
                    docx_bytes = export_to_docx_admin_format(user_topic, generated_sample)
                    
                    # Đổi nút bấm từ tải file .txt thành nút tải file .docx chuyên nghiệp
                    st.download_button(
                        label="📥 Tải Bản mẫu Word (.docx) Chuẩn Nghị Định 30",
                        data=docx_bytes,
                        file_name=f"Mau_SKKN_{user_topic.replace(' ', '_')[:30]}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error(f"Lỗi khi đóng gói cấu trúc file Word hành chính: {e}")
                    # Nút tải file dự phòng dạng .txt nếu máy chủ bị nghẽn thư viện biên dịch
                    st.download_button(
                        label="📥 Tải Bản mẫu dự phòng (.txt)",
                        data=generated_sample,
                        file_name=f"Mau_SKKN_{user_topic.replace(' ', '_')[:30]}.txt",
                        mime="text/plain"
                    )
                
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # --- THƯ VIỆN CÁC MẪU CỐ ĐỊNH CŨ ---
    st.markdown("### 📁 Danh mục các mẫu quy chuẩn có sẵn trong thư viện")
    search_query = st.text_input("🔍 Tìm kiếm nhanh trong kho mẫu sẵn có:", "")
    
    library_data = {
        "Toán học": [
            {
                "title": "Biện pháp ứng dụng công nghệ số trong dạy học Hình học lớp 8",
                "author": "Mẫu chuẩn Bộ GD&ĐT",
                "summary": "Giải pháp tập trung vào việc sử dụng các phần mềm hình học động (Geogebra) kết hợp mô hình lớp học đảo ngược...",
                "content": "ĐẶT VẤN ĐỀ\n1. Lý do chọn đề tài...\n\nNỘI DUNG CỐT LÕI..."
            }
        ]
    }
    
    for cat, topics in library_data.items():
        filtered_topics = [t for t in topics if search_query.lower() in t["title"].lower() or search_query.lower() in cat.lower()]
        if filtered_topics:
            with st.expander(f"📁 Danh mục: Môn {cat} ({len(filtered_topics)} tài liệu)"):
                for t in filtered_topics:
                    st.markdown(f"### 📄 {t['title']}")
                    st.write(f"ℹ️ **Tóm tắt:** {t['summary']}")
                    if st.checkbox(f"👁️ Xem nội dung mẫu", key=t['title']):
                        st.text_area("Nội dung:", value=t['content'], height=150)
