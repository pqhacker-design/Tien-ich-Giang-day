import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
from vietnamese_word_corrector.ai_checker import classify_paragraphs_with_ai

def set_paragraph_text_and_style(p, text, font_size=13, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, uppercase=False):
    """Xóa bỏ triệt để style cũ/xé lẻ và ép style mới chuẩn 100% Times New Roman"""
    if uppercase:
        text = text.upper()
        
    p.text = "" # Xóa văn bản cũ cùng với format lỗi
    p.alignment = align
    
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0) # Ép màu đen chuẩn

def normalize_to_nd30(input_docx_path, output_docx_path):
    """
    Sử dụng AI kết hợp Quy chuẩn NĐ 30/2020/NĐ-CP để tự động chuẩn hóa bất kỳ văn bản thô nào:
    - Định dạng Lề giấy chuẩn (Trái 3cm, Phải 1.5cm, Trên 2cm, Dưới 2cm)
    - Nhận diện & Viết IN HOA + IN ĐẬM các đề mục (Kể cả văn bản thô không đánh số)
    - Căn giữa Tiêu đề / Quốc hiệu
    - Căn đều 2 bên + Thụt đầu dòng 1.27 cm cho văn bản thường
    """
    if not input_docx_path or not docx:
        return output_docx_path

    doc = docx.Document(input_docx_path)

    # 1. Căn chỉnh lề trang giấy theo NĐ30
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.5)

    # 2. Trích xuất toàn bộ danh sách văn bản để AI phân loại
    raw_paragraphs = [p.text.strip() for p in doc.paragraphs]
    non_empty_indices = [i for i, text in enumerate(raw_paragraphs) if text]
    non_empty_texts = [raw_paragraphs[i] for i in non_empty_indices]

    # Gọi AI nhận dạng thông minh cấu trúc
    ai_labels = classify_paragraphs_with_ai(non_empty_texts)
    
    label_map = {}
    for idx, orig_i in enumerate(non_empty_indices):
        label_map[orig_i] = ai_labels[idx] if idx < len(ai_labels) else "BODY_TEXT"

    # 3. Tiến hành ép Định dạng (Formatting) dựa trên kết quả nhận diện của AI
    for i, p in enumerate(doc.paragraphs):
        text_raw = p.text.strip()
        if not text_raw:
            continue

        # Cấu hình giãn dòng chuẩn
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)

        label = label_map.get(i, "BODY_TEXT")

        # A. QUỐC HIỆU / TIÊU ĐỀ CHÍNH -> CĂN GIỮA, IN HOA, IN ĐẬM
        if label in ["QUOC_HIEU", "MAIN_TITLE"]:
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            set_paragraph_text_and_style(p, text_raw, font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, uppercase=True)

        # B. ĐỀ MỤC CẤP 1 (I, II, 1, 2, TỔNG QUAN, PHÂN TÍCH...) -> IN HOA, IN ĐẬM, CĂN TRÁI
        elif label == "HEADING_1":
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(3)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, uppercase=True)

        # C. ĐỀ MỤC CẤP 2 (Ý nghĩa:, Tông màu:, a), b)...) -> IN ĐẬM, CĂN TRÁI/THỤT NHẸ 0.5CM
        elif label == "HEADING_2":
            p.paragraph_format.first_line_indent = Cm(0.5)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, uppercase=False)

        # D. NƠI NHẬN / CHỮ KÝ -> CĂN PHẢI / TRÁI ĐẶC THÙ
        elif label == "SIGNATURE":
            p.paragraph_format.first_line_indent = Cm(0)
            set_paragraph_text_and_style(p, text_raw, font_size=12, bold=False, italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, uppercase=False)

        # E. VĂN BẢN THƯỜNG (BODY TEXT) -> CĂN ĐỀU 2 BÊN, THỤT ĐẦU DÒNG 1.27 CM
        else:
            p.paragraph_format.first_line_indent = Cm(1.27)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, uppercase=False)

    # 4. Định dạng Bảng biểu (nếu có)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    if p.text.strip():
                        set_paragraph_text_and_style(p, p.text.strip(), font_size=12, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT)

    doc.save(output_docx_path)
    return output_docx_path
