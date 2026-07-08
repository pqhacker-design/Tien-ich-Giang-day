import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re

def set_paragraph_text_and_style(p, text, font_size=13, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, uppercase=False):
    """Hàm xóa sạch style cũ bị xé lẻ và ghi đè style chuẩn Times New Roman"""
    if uppercase:
        text = text.upper()
        
    p.text = "" # Xóa văn bản cũ cùng với format lỗi gốc
    p.alignment = align
    
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0) # Ép màu đen chuẩn

def normalize_to_nd30(input_docx_path, output_docx_path):
    """
    Chuẩn hóa thể thức NĐ 30/2020/NĐ-CP:
    - Căn lề giấy chuẩn (Trái 3cm, Phải 1.5cm, Trên 2cm, Dưới 2cm)
    - In hoa + In đậm các đề mục lớn
    - Căn giữa Tiêu đề / Quốc hiệu
    - Thụt đầu dòng 1.27cm cho văn bản thường
    """
    if not input_docx_path or not docx:
        return output_docx_path

    doc = docx.Document(input_docx_path)

    # 1. Cấu hình lề trang giấy theo Nghị định 30
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.5)

    # 2. Quy tắc Regex phát hiện đề mục
    pattern_quoc_hieu = re.compile(r'^(CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM|ĐỘC LẬP - TỰ DO - HẠNH PHÚC)', re.IGNORECASE)
    pattern_main_title = re.compile(r'^(BẢNG THUYẾT MINH|KẾT LUẬN|TỔNG QUAN|QUYẾT ĐỊNH|THÔNG BÁO|BÁO CÁO|TỜ TRÌNH|KẾ HOẠCH)', re.IGNORECASE)
    pattern_numbered_heading = re.compile(r'^\d+[\.\s\)]|^[I|V|X]+[\.\s\:]') # Match: 1., 2., I., II.
    pattern_sub_heading = re.compile(r'^(SỰ KIỆN|Ý NGHĨA|PHÂN TÍCH|KẾT LUẬN|TÔNG MÀU|PHÔNG CHỮ|SỰ KẾT HỢP)[\:\s]', re.IGNORECASE)

    for i, p in enumerate(doc.paragraphs):
        text_raw = p.text.strip()
        if not text_raw:
            continue

        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)

        # A. Quốc hiệu & Tiêu đề chính -> CĂN GIỮA, IN HOA, IN ĐẬM
        if pattern_quoc_hieu.search(text_raw) or pattern_main_title.match(text_raw) or (i == 0 and len(text_raw) < 100):
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            set_paragraph_text_and_style(p, text_raw, font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, uppercase=True)
            continue

        # B. Đề mục đánh số (1. TỔNG QUAN..., II. PHÂN TÍCH...) -> IN HOA, IN ĐẬM, CĂN TRÁI
        if pattern_numbered_heading.match(text_raw):
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, uppercase=True)
            continue

        # C. Đề mục con (Ý nghĩa:, Tông màu...) -> IN ĐẬM, KHÔNG VIẾT HOA HẾT
        if pattern_sub_heading.match(text_raw):
            p.paragraph_format.first_line_indent = Cm(0.5)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, uppercase=False)
            continue

        # D. Văn bản thường (Body text) -> CĂN ĐỀU 2 BÊN, THỤT LỀ ĐẦU DÒNG 1.27 CM
        p.paragraph_format.first_line_indent = Cm(1.27)
        set_paragraph_text_and_style(p, text_raw, font_size=13, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, uppercase=False)

    doc.save(output_docx_path)
    return output_docx_path
