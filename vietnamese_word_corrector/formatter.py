import docx
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import re

def normalize_to_nd30(input_docx_path, output_docx_path):
    """
    Tự động chuẩn hóa lề lối, font chữ, thụt lề, giãn dòng và tô đậm đề mục 
    theo quy định Nghị định 30/2020/NĐ-CP đối với văn bản hành chính Việt Nam.
    """
    doc = docx.Document(input_docx_path)

    # 1. Cấu hình Lề trang giấy (Page Margins) theo NĐ 30/2020/NĐ-CP
    # Trên: 20-25mm (2.0 cm), Dưới: 20-25mm (2.0 cm), Trái: 30mm (3.0 cm), Phải: 15-20mm (1.5 cm)
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.5)

    # 2. Quy tắc Regex nhận diện các loại Đề mục để tự động IN ĐẬM và Định dạng
    pattern_roman_heading = re.compile(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X)[\.\s\:]') # I., II., III.
    pattern_arabic_heading = re.compile(r'^\d+[\.\s\)]')                            # 1., 2., 1)
    pattern_sub_heading = re.compile(r'^[a-z]\)')                                  # a), b), c)
    pattern_quoc_hieu = re.compile(r'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM', re.IGNORECASE)
    pattern_doc_type = re.compile(r'^(KẾ HOẠCH|QUYẾT ĐỊNH|THÔNG BÁO|BÁO CÁO|TỜ TRÌNH|CÔNG VĂN)', re.IGNORECASE)

    # 3. Duyệt từng đoạn văn (Paragraph) để định dạng chi tiết
    for p in doc.paragraphs:
        text_strip = p.text.strip()
        if not text_strip:
            continue

        # --- TỔNG QUAN GIÃN DÒNG & GIÃN ĐOẠN ---
        p.paragraph_format.line_spacing = 1.15         # Giãn dòng 1.15 (Quy định 1.0 - 1.5)
        p.paragraph_format.space_before = Pt(3)         # Giãn đoạn trước 3pt
        p.paragraph_format.space_after = Pt(3)          # Giãn đoạn sau 3pt

        # --- A. XỬ LÝ QUỐC HIỆU / TIÊU ĐỀ CHÍNH ---
        if pattern_quoc_hieu.search(text_strip):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(13)
                run.bold = True
            continue

        if pattern_doc_type.match(text_strip):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(14)
                run.bold = True
            continue

        # --- B. XỬ LÝ CÁC ĐỀ MỤC LỚN (I., II., III...) ---
        if pattern_roman_heading.match(text_strip):
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.first_line_indent = Cm(0) # Không thụt lề đề mục lớn
            p.paragraph_format.space_before = Pt(6)      # Tăng giãn đoạn cho đề mục
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(13)
                run.bold = True
            continue

        # --- C. XỬ LÝ CÁC MỤC CON (1., 2., a), b)...) ---
        if pattern_arabic_heading.match(text_strip) or pattern_sub_heading.match(text_strip):
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.first_line_indent = Cm(1.0) # Thụt lề đầu dòng 1cm
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(13)
                run.bold = True
            continue

        # --- D. XỬ LÝ NỘI DUNG VĂN BẢN THƯỜNG (BODY TEXT) ---
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY          # Căn đều 2 bên (Justify)
        p.paragraph_format.first_line_indent = Cm(1.27)     # Thụt lề đầu dòng chuẩn 1.27 cm (0.5 inch)
        
        for run in p.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(13)                          # Cỡ chữ chuẩn 13pt - 14pt
            run.font.color.rgb = RGBColor(0, 0, 0)          # Chữ màu đen chuẩn

    # 4. Định dạng lại nội dung bên trong các Bảng (Tables) nếu văn bản có bảng
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    for run in p.runs:
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(12) # Chữ trong bảng cỡ 12pt

    doc.save(output_docx_path)
    return output_docx_path
