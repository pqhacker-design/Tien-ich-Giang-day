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
    """Xuất nội dung văn bản sang file Word chuẩn định dạng hành chính Nghị định 30/2020/NĐ-CP"""
    doc = Document()
    
    # 1. Cấu hình khổ giấy A4 & Căn lề trang chuẩn (Top 20mm, Bottom 20mm, Left 30mm, Right 15mm)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(20 / 25.4)
        section.bottom_margin = Inches(20 / 25.4)
        section.left_margin = Inches(30 / 25.4)
        section.right_margin = Inches(15 / 25.4)
        section.page_width = Inches(210 / 25.4)
        section.page_height = Inches(297 / 25.4)

    # 2. Cấu hình Style chữ mặc định toàn văn bản (Times New Roman, Cỡ 14)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(14)
    
    # 3. CHÈN QUỐC HIỆU - TIÊU NGỮ (Dùng bảng ẩn 2 cột song song chuẩn 100% văn bản gốc)
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    table.autofit = False
    table.columns[0].width = Inches(2.8)
    table.columns[1].width = Inches(4.2)
    
    # Cột bên trái: Cơ quan chủ quản / Đơn vị công tác
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
    run_l2 = p_left2.add_run("-------")
    run_l2.font.name = 'Times New Roman'
    run_l2.font.size = Pt(12)
    
    # Cột bên phải: Quốc hiệu & Tiêu ngữ
    cell_right = table.cell(0, 1)
    p_right1 = cell_right.paragraphs[0]
    p_right1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_r1 = p_right1.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
    run_r1.font.name = 'Times New Roman'
    run_r1.font.size = Pt(12)
    run_r1.bold = True
    
    run_r2 = p_right1.add_run("Độc lập - Tự do - Hạnh phúc")
    run_r2.font.name = 'Times New Roman'
    run_r2.font.size = Pt(13)
    run_r2.bold = True
    
    p_right2 = cell_right.add_paragraph()
    p_right2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_right2.paragraph_format.space_before = Pt(2)
    run_r3 = p_right2.add_run("_______________")
    run_r3.font.name = 'Times New Roman'
    run_r3.font.size = Pt(13)
    run_r3.bold = True

    # Tạo khoảng trống giữa Tiêu ngữ và Tên sáng kiến
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(24)

    # 4. CHÈN TÊN VĂN BẢN ĐỀ TÀI SÁNG KIẾN KINH NGHIỆM
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    run_title_lbl = p_title.add_run("BÁO CÁO SÁNG KIẾN KINH NGHIỆM\n")
    run_title_lbl.font.name = 'Times New Roman'
    run_title_lbl.font.size = Pt(14)
    run_title_lbl.bold = True
    
    run_title_val = p_title.add_run(f"“{topic.upper()}”")
    run_title_val.font.name = 'Times New Roman'
    run_title_val.font.size = Pt(15)
    run_title_val.bold = True

    # 5. XỬ LÝ ĐOẠN VĂN BẢN (Quét định dạng các đề mục in đậm và nội dung)
    lines = content_text.split('\n')
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3  # Giãn dòng (Line spacing) chuẩn 1.3 lines
        p.paragraph_format.space_after = Pt(6)  # Giãn dòng đoạn dưới (Space after) 6pt
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY # Căn đều 2 bên (Justify)
        
        # Nhận diện các tiêu đề lớn, mục lục để in đậm tự động
        if cleaned_line.startswith(("ĐẶT VẤN ĐỀ", "GIẢI PHÁP", "NỘI DUNG", "KẾT LUẬN", "1.", "2.", "3.", "4.", "I.", "II.", "III.")):
            run = p.add_run(cleaned_line)
            run.bold = True
            p.paragraph_format.space_before = Pt(12) # Tự động giãn dòng cách đoạn trên khi gặp tiêu đề lớn
        else:
            # Đối với đoạn văn thường: Tự động thụt lề dòng đầu tiên (First line indent) từ 1cm đến 1.25cm
            p.paragraph_format.first_line_indent = Inches(0.5) 
            run = p.add_run(cleaned_line)
            
        run.font.name = 'Times New Roman'
        run.font.size = Pt(14)
        
    # Biên dịch tài liệu thành dữ liệu nhị phân (Bytes) để chuyển tiếp lên Streamlit Cloud
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
