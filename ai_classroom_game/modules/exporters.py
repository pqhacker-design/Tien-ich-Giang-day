import io
from docx import Document
from pptx import Presentation

class DocumentExporter:
    @staticmethod
    def export_to_docx(topic, quiz_data):
        doc = Document()
        doc.add_heading(f"KỊCH BẢN HOẠT ĐỘNG: {topic.upper()}", level=1)
        
        doc.add_heading("1. Phần Câu Hỏi Trắc Nghiệm", level=2)
        for idx, q in enumerate(quiz_data.get("trac_nghiem", []), 1):
            doc.add_paragraph(f"Câu {idx}: {q['cau_hoi']}")
            for opt in q['options']:
                doc.add_paragraph(f"  [ ] {opt}")
            doc.add_paragraph(f"👉 Đáp án đúng: {q['dap_an']} - Giải thích: {q['giai_thich']}")
            
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def export_to_pptx(topic, quiz_data):
        prs = Presentation()
        # Slide tiêu đề chính
        slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = f"Trò Chơi Học Tập\nChủ đề: {topic}"
        
        # Tạo slide câu hỏi tự động
        for q in quiz_data.get("trac_nghiem", []):
            blank_layout = prs.slide_layouts[1]
            s = prs.slides.add_slide(blank_layout)
            s.shapes.title.text = q['cau_hoi']
            body = s.placeholders[1]
            body.text = "\n".join(q['options'])
            
        buffer = io.BytesIO()
        prs.save(buffer)
        buffer.seek(0)
        return buffer
