import io
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

class WordExportEngine:
    @staticmethod
    def create_docx(text_content: str) -> io.BytesIO:
        doc = docx.Document()
        
        # Thiết lập lề chuẩn Nghị định 30 (Lề trên 2cm, dưới 2cm, trái 3cm, phải 2cm)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.79)
            section.bottom_margin = Inches(0.79)
            section.left_margin = Inches(1.18)
            section.right_margin = Inches(0.79)

        # Style mặc định: Times New Roman, 13pt
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(13)
        font.color.rgb = RGBColor(0, 0, 0)

        # Ghi nội dung vào File Word
        lines = text_content.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(4)

            # Format một số dòng tiêu đề đơn giản
            if line_str.isupper() and len(line_str) < 100:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(line_str)
                run.bold = True
            elif line_str.startswith("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM") or line_str.startswith("Độc lập - Tự do"):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(line_str)
                run.bold = True
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.add_run(line_str)

        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        return file_stream
