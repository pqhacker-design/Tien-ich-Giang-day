from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import io

def create_powerpoint_file(slide_data_json, style_choice):
    """Xây dựng và định dạng file .pptx tự động từ dữ liệu JSON của AI"""
    prs = Presentation()
    
    # Định nghĩa cấu hình màu sắc theo cấp học lựa chọn
    if style_choice == "Tiểu học":
        bg_color = RGBColor(240, 249, 255) # Xanh nước biển nhạt sinh động
        title_color = RGBColor(2, 132, 199)
        text_color = RGBColor(30, 41, 59)
    elif style_choice == "THCS":
        bg_color = RGBColor(248, 250, 252) # Hiện đại trực quan
        title_color = RGBColor(30, 58, 138)
        text_color = RGBColor(15, 23, 42)
    else: # THPT - Tối giản, chuyên nghiệp
        bg_color = RGBColor(255, 255, 255)
        title_color = RGBColor(17, 24, 39)
        text_color = RGBColor(55, 65, 81)

    slides_list = slide_data_json.get("slides", [])
    
    for s_idx, s_data in enumerate(slides_list):
        s_type = s_data.get("type", "content")
        
        # Chọn Layout thích hợp: 0 là Slide Title, 1 là Slide Title & Content, 6 là Blank
        if s_type == "title":
            slide_layout = prs.slide_layouts[0]
            slide = prs.slides.add_slide(slide_layout)
            
            title = slide.shapes.title
            title.text = s_data.get("title", "BÀI GIẢNG ĐIỆN TỬ")
            title.text_frame.paragraphs[0].font.color.rgb = title_color
            title.text_frame.paragraphs[0].font.name = "Arial"
            
            subtitle = slide.placeholders[1]
            sub_text = f"{s_data.get('subtitle', '')}\nGiáo viên: {s_data.get('teacher', 'Ngo Thanh Hung')}\nTrường học: {s_data.get('school', 'Trường THCS')}"
            subtitle.text = sub_text
            
        elif s_type == "quiz":
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)
            
            # Gán tiêu đề câu hỏi
            title_shape = slide.shapes.title
            title_shape.text = s_data.get("title", "Câu hỏi luyện tập")
            title_shape.text_frame.paragraphs[0].font.color.rgb = RGBColor(220, 38, 38) # Màu đỏ nổi bật cho câu hỏi
            
            # Khối nội dung trắc nghiệm
            body_shape = slide.placeholders[1]
            tf = body_shape.text_frame
            tf.text = s_data.get("question", "") + "\n"
            for opt in s_data.get("options", []):
                p = tf.add_paragraph()
                p.text = f"❑ {opt}"
                p.level = 1
                
        else: # Các slide nội dung thông thường, hoạt động, mục tiêu
            slide_layout = prs.slide_layouts[1]
            slide = prs.slides.add_slide(slide_layout)
            
            title_shape = slide.shapes.title
            title_shape.text = s_data.get("title", "Nội dung bài học")
            title_shape.text_frame.paragraphs[0].font.color.rgb = title_color
            
            body_shape = slide.placeholders[1]
            tf = body_shape.text_frame
            
            if "bullets" in s_data:
                tf.text = ""
                for idx, bullet in enumerate(s_data.get("bullets", [])):
                    p = tf.add_paragraph() if idx > 0 else tf.paragraphs[0]
                    p.text = f"• {bullet}"
                    p.font.size = Pt(18)
                    p.font.color.rgb = text_color
            else:
                tf.text = s_data.get("body", s_data.get("content", ""))
                tf.paragraphs[0].font.size = Pt(18)
                tf.paragraphs[0].font.color.rgb = text_color
                
        # --- TỰ ĐỘNG CHÈN GHI CHÚ CHO GIÁO VIÊN (TEACHER NOTES) ---
        notes_slide = slide.notes_slide
        text_frame = notes_slide.notes_text_frame
        text_frame.text = s_data.get("notes", "Giáo viên giảng dạy theo đúng nội dung tiến trình slide hiển thị.")

    # Đóng gói xuất luồng file nhị phân tải trực tiếp
    ppt_stream = io.BytesIO()
    prs.save(ppt_stream)
    ppt_stream.seek(0)
    return ppt_stream