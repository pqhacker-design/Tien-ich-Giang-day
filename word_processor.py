import io
import os
from docx import Document
from docx.shared import RGBColor, Pt
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

class WordProcessor:
    @staticmethod
    def extract_text(file_bytes: bytes) -> str:
        """Đọc toàn bộ text từ file Word để gửi cho AI phân tích."""
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
    def insert_paragraph_after(paragraph, text, color_rgb):
        """Hàm bổ trợ: Chèn đoạn văn mới ngay sau đoạn văn chỉ định và tối ưu khoảng cách."""
        new_p = OxmlElement('w:p')
        paragraph._p.addnext(new_p)
        new_para = Paragraph(new_p, paragraph._parent)
        
        # --- ĐIỀU CHỈNH KHOẢNG CÁCH (LÀM GỌN) ---
        # Thiết lập khoảng cách trước/sau đoạn văn bằng 0 để không bị đẩy dòng xa
        new_para.paragraph_format.space_before = Pt(2)
        new_para.paragraph_format.space_after = Pt(4)
        new_para.paragraph_format.line_spacing = 1.15 # Giãn dòng tiêu chuẩn
        
        # Thêm nội dung và định dạng chữ
        run = new_para.add_run(text)
        run.font.color.rgb = color_rgb
        run.italic = True 
        run.font.size = Pt(11) # Đảm bảo kích thước chữ vừa vặn, gọn gàng
        return new_para

    @staticmethod
    def integrate_digital_capacity(file_bytes: bytes, ai_data: dict) -> io.BytesIO:
        """Tìm các điểm neo (anchor_text) và chèn nội dung số trực tiếp gọn gàng vào sau vị trí đó."""
        doc = Document(io.BytesIO(file_bytes))
        sua_doi_list = ai_data.get('sua_doi', [])
        color_blue = RGBColor(0, 102, 204) # Màu xanh dương sáng rõ ràng
        
        for item in sua_doi_list:
            anchor = item.get('anchor_text', '').strip()
            content = item.get('insert_content', '').strip()
            
            if not anchor or not content:
                continue
                
            inserted = False
            
            # 1. Tìm kiếm trong các Paragraph thông thường ngoài bảng
            for para in doc.paragraphs:
                if anchor in para.text:
                    # ĐÃ ĐỔI: Loại bỏ hoàn toàn các ký tự xuống dòng \n thừa ở đầu và cuối text
                    clean_text = f"[Tích hợp Năng lực số]: {content}"
                    WordProcessor.insert_paragraph_after(para, clean_text, color_blue)
                    inserted = True
                    break 
            
            # 2. Tìm kiếm sâu bên trong các bảng (Tables)
            if not inserted:
                for table in doc.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for para in cell.paragraphs:
                                if anchor in para.text:
                                    clean_text = f"[Tích hợp Năng lực số]: {content}"
                                    WordProcessor.insert_paragraph_after(para, clean_text, color_blue)
                                    inserted = True
                                    break
                            if inserted: break
                        if inserted: break
                    if inserted: break

        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)
        return output_stream