import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def normalize_to_nd30(file_path, output_path):
    doc = docx.Document(file_path)
    
    # Thiết lập lề A4 chuẩn Nghị định 30 (Lề trên-dưới: 20-25mm, Trái: 30-35mm, Phải: 15-20mm)
    for section in doc.sections:
        section.top_margin = Inches(0.79)     # ~20mm
        section.bottom_margin = Inches(0.79)  # ~20mm
        section.left_margin = Inches(1.18)    # ~30mm
        section.right_margin = Inches(0.59)   # ~15mm
        section.page_width = Inches(8.27)     # A4
        section.page_height = Inches(11.69)

    for p in doc.paragraphs:
        # Chuẩn hóa Font & Cỡ chữ & Giãn dòng 1.15
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        
        for run in p.runs:
            run.font.name = 'Times New Roman'
            if not run.font.size:
                run.font.size = Pt(13)
                
        # Sửa thô các chuỗi Quốc hiệu lỗi phổ biến nếu có
        t = p.text.strip().upper()
        if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in t:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs: run.bold = True
            
    doc.save(output_path)
    return True