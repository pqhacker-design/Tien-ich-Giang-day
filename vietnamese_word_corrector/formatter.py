import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import re
from vietnamese_word_corrector.ai_checker import classify_paragraphs_with_ai

def set_paragraph_text_and_style(p, text, font_size=13, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, uppercase=False):
    """Xóa bỏ triệt để style cũ và áp dụng style chuẩn Times New Roman"""
    if uppercase:
        text = text.upper()
        
    p.text = "" 
    p.alignment = align
    
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)

def normalize_to_nd30(input_docx_path, output_docx_path):
    if not input_docx_path or not docx:
        return output_docx_path

    doc = docx.Document(input_docx_path)

    # 1. Định dạng Lề giấy NĐ 30/2020/NĐ-CP
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(1.5)

    # 2. Lấy danh sách văn bản và gọi AI phân loại
    raw_paragraphs = [p.text.strip() for p in doc.paragraphs]
    non_empty_indices = [i for i, text in enumerate(raw_paragraphs) if text]
    non_empty_texts = [raw_paragraphs[i] for i in non_empty_indices]

    ai_labels = classify_paragraphs_with_ai(non_empty_texts)
    
    label_map = {}
    for idx, orig_i in enumerate(non_empty_indices):
        label_map[orig_i] = ai_labels[idx] if idx < len(ai_labels) else "BODY_TEXT"

    # 3. Ép định dạng dựa trên nhãn AI
    for i, p in enumerate(doc.paragraphs):
        text_raw = p.text.strip()
        if not text_raw:
            continue

        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)

        label = label_map.get(i, "BODY_TEXT")

        if label in ["QUOC_HIEU", "MAIN_TITLE"]:
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            set_paragraph_text_and_style(p, text_raw, font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, uppercase=True)

        elif label == "HEADING_1":
            p.paragraph_format.first_line_indent = Cm(0)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(3)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, uppercase=True)

        elif label == "HEADING_2":
            p.paragraph_format.first_line_indent = Cm(0.5)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, uppercase=False)

        elif label == "SIGNATURE":
            p.paragraph_format.first_line_indent = Cm(0)
            set_paragraph_text_and_style(p, text_raw, font_size=12, bold=False, italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, uppercase=False)

        else:
            p.paragraph_format.first_line_indent = Cm(1.27)
            set_paragraph_text_and_style(p, text_raw, font_size=13, bold=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, uppercase=False)

    # 4. Định dạng Bảng biểu
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
