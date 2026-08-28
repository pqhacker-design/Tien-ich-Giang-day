import io
from docx import Document
from docx.shared import RGBColor, Pt
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

class WordProcessor:
    @staticmethod
    def extract_text(file_bytes: bytes) -> str:
        doc = Document(io.BytesIO(file_bytes))
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = " ".join([p.text for p in cell.paragraphs if p.text.strip()])
                    if cell_text:
                        full_text.append(cell_text)
        return "\n".join(full_text)

    @staticmethod
    def insert_paragraph_after(paragraph, text, color_rgb, prefix=""):
        """Chèn đoạn văn mới sau paragraph với prefix và màu sắc."""
        new_p = OxmlElement('w:p')
        paragraph._p.addnext(new_p)
        new_para = Paragraph(new_p, paragraph._parent)
        new_para.paragraph_format.space_before = Pt(2)
        new_para.paragraph_format.space_after = Pt(4)
        new_para.paragraph_format.line_spacing = 1.15
        run = new_para.add_run(f"{prefix} {text}" if prefix else text)
        run.font.color.rgb = color_rgb
        run.italic = True
        run.font.size = Pt(11)
        return new_para

    @staticmethod
    def integrate_digital_capacity(file_bytes: bytes, ai_data: dict, integration_type: str) -> io.BytesIO:
        doc = Document(io.BytesIO(file_bytes))
        sua_doi_list = ai_data.get('sua_doi', [])
        
        # Màu sắc phân biệt
        color_digital = RGBColor(0, 102, 204)   # Xanh dương
        color_ai = RGBColor(214, 107, 0)        # Vàng cam
        
        for item in sua_doi_list:
            anchor = item.get('anchor_text', '').strip()
            content = item.get('insert_content', '').strip()
            loai = item.get('loai', 'Năng lực số')
            
            if not anchor or not content:
                continue
            
            # Xác định prefix và màu
            if loai == "Năng lực AI":
                prefix = "[Năng lực AI]:"
                color = color_ai
            else:
                prefix = "[Năng lực số]:"
                color = color_digital
            
            inserted = False
            
            # Tìm trong paragraph
            for para in doc.paragraphs:
                if anchor in para.text:
                    WordProcessor.insert_paragraph_after(para, content, color, prefix)
                    inserted = True
                    break
            
            # Tìm trong bảng
            if not inserted:
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for para in cell.paragraphs:
                                if anchor in para.text:
                                    WordProcessor.insert_paragraph_after(para, content, color, prefix)
                                    inserted = True
                                    break
                            if inserted:
                                break
                        if inserted:
                            break
                    if inserted:
                        break

        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)
        return output_stream
