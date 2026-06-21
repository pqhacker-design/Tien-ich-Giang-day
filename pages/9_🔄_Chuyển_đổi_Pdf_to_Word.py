import streamlit as st
import io
import re
from google import genai
from google.genai import types
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Chuyển đổi Tài liệu sang Word", page_icon="🔄", layout="centered")

st.title("🔄 Chuyển đổi Tài liệu sang Word (Chống Rác Watermark/Mộc Đỏ)")
st.caption("Phiên bản nâng cấp: Sử dụng mắt thần AI OCR để tự động loại bỏ chữ chìm, mộc đỏ rác và giữ nguyên định dạng.")

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.stop() 

if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = genai.Client(api_key=api_key_input)
    except Exception as e:
        st.error(f"Khởi tạo Gemini Client thất bại: {e}")
        st.stop()

client = st.session_state.gemini_client

# ==================== BỘ PHÂN TÍCH CHỮ IN ĐẬM / IN NGHIÊNG TỪ AI ====================
def add_formatted_text(paragraph, text):
    """
    Hàm tự động quét qua chuỗi văn bản chứa ký tự markdown (* hoặc **)
    để phân tách, áp dụng thuộc tính Bold, Italic và dọn sạch dấu vết rác.
    """
    tokens = re.split(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)', text)
    
    for token in tokens:
        if token.startswith('***') and token.endswith('***'):
            clean_token = token[3:-3].replace('$', '')
            run = paragraph.add_run(clean_token)
            run.bold = True
            run.italic = True
        elif token.startswith('**') and token.endswith('**'):
            clean_token = token[2:-2].replace('$', '')
            run = paragraph.add_run(clean_token)
            run.bold = True
        elif token.startswith('*') and token.endswith('*'):
            clean_token = token[1:-1].replace('$', '')
            run = paragraph.add_run(clean_token)
            run.italic = True
        else:
            clean_token = token.replace('$', '')
            paragraph.add_run(clean_token)

# ==================== HÀM TẠO FILE WORD GIỮ ĐỊNH DẠNG TỐI ĐA ====================
def create_word_document(text_content):
    doc = Document()
    
    # Định dạng căn lề trang chuẩn văn bản hành chính Việt Nam (Lề 2cm mỗi bên)
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)

    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    lines = text_content.split('\n')
    in_table = False
    table_data = []

    for line in lines:
        raw_line = line
        clean_line = line.strip()
        if not clean_line:
            continue

        # 1. DỰNG LẠI BẢNG BIỂU CHUẨN Ô LƯỚI
        if clean_line.startswith('|'):
            if '---|' in clean_line or '===' in clean_line:
                continue
            in_table = True
            columns = [col.strip() for col in clean_line.split('|')[1:-1]]
            if columns:
                table_data.append(columns)
            continue
        else:
            if in_table and table_data:
                num_rows = len(table_data)
                num_cols = max(len(row) for row in table_data)
                word_table = doc.add_table(rows=num_rows, cols=num_cols)
                word_table.style = 'Table Grid'
                
                for r_idx, row in enumerate(table_data):
                    for c_idx, val in enumerate(row):
                        if c_idx < len(word_table.rows[r_idx].cells):
                            p_cell = word_table.rows[r_idx].cells[c_idx].paragraphs[0]
                            add_formatted_text(p_cell, val)
                
                doc.add_paragraph()
                in_table = False
                table_data = []

        # 2. XỬ LÝ ĐÁP ÁN TRẮC NGHIỆM CĂN NGANG HÀNG (Dành cho đề thi)
        if re.search(r'A\..*B\..*C\..*D\.', clean_line) or re.search(r'A\s*[\.\)].*B\s*[\.\)].*C\s*[\.\)].*D\s*[\.\)]', clean_line):
            p = doc.add_paragraph()
            if raw_line.startswith('    ') or raw_line.startswith('\t'):
                p.paragraph_format.left_indent = Inches(0.4)
                
            parts = re.split(r'(A\.|B\.|C\.|D\.)', clean_line)
            for part in parts:
                if part in ['A.', 'B.', 'C.', 'D.']:
                    run = p.add_run("    " + part + " ")
                    run.bold = True
                else:
                    add_formatted_text(p, part)
            continue

        # 3. XỬ LÝ TIÊU ĐỀ HOẶC ĐOẠN VĂN THƯỜNG
        if clean_line.startswith('# '):
            h = doc.add_heading('', level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_formatted_text(h, clean_line.replace('# ', ''))
        elif clean_line.startswith('## '):
            h = doc.add_heading('', level=2)
            add_formatted_text(h, clean_line.replace('## ', ''))
        else:
            p = doc.add_paragraph()
            
            # Xử lý thụt lề đầu dòng
            if raw_line.startswith('    ') or raw_line.startswith('\t'):
                p.paragraph_format.left_indent = Inches(0.4)

            if clean_line.startswith("Câu "):
                match = re.match(r'(Câu \d+\.)(.*)', clean_line)
                if match:
                    bold_part, regular_part = match.groups()
                    p.add_run(bold_part).bold = True
                    add_formatted_text(p, regular_part)
                else:
                    add_formatted_text(p, clean_line)
            else:
                add_formatted_text(p, clean_line)

    if in_table and table_data:
        word_table = doc.add_table(rows=len(table_data), cols=max(len(row) for row in table_data))
        word_table.style = 'Table Grid'
        for r_idx, row in enumerate(table_data):
            for c_idx, val in enumerate(row):
                if c_idx < len(word_table.rows[r_idx].cells):
                    p_cell = word_table.rows[r_idx].cells[c_idx].paragraphs[0]
                    add_formatted_text(p_cell, val)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- GIAO DIỆN STREAMLIT UPLOAD VÀ XỬ LÝ ---
uploaded_file = st.file_uploader(
    "Tải lên Tài liệu dạng Ảnh hoặc PDF cần xử lý chống rác:",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    file_type = uploaded_file.type
    extracted_text = ""
    
    st.info(f"📁 Đã nhận file: **{uploaded_file.name}**")
    
    if st.button("🚀 Bắt đầu trích xuất sạch (Bỏ Watermark)"):
        with st.spinner("Hệ thống AI thông minh đang bóc tách văn bản gốc và lọc bỏ chữ chìm..."):
            
            # KHÔNG DÙNG THƯ VIỆN ĐỌC TEXT LAYER ĐỂ TRÁNH DÍNH WATERMARK RÁC
            # Chuyển trực tiếp file byte sang cho Gemini phân tích hình ảnh trực quan (OCR bằng mắt AI)
            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()
            file_part = types.Part.from_bytes(data=file_bytes, mime_type=file_type)
            
            # Bộ Prompt chỉ thị khắt khe ép AI lọc bỏ hoàn toàn các loại dấu chìm rác
            prompt = (
                "Bạn là chuyên gia số hóa tài liệu hành chính và văn bản pháp luật.\n"
                "Nhiệm vụ của bạn là trích xuất chính xác 100% nội dung văn bản chữ từ tài liệu này.\n\n"
                
                "⚠️ LƯU Ý QUAN TRỌNG ĐỂ LỌC RÁC WATERMARK:\n"
                "Trong tài liệu có thể xuất hiện các dòng chữ mờ đóng dấu chìm (ví dụ: tên người, phòng ban, ngày giờ chạy dọc trang) hoặc mộc đỏ đè lên chữ. "
                "Hãy BỎ QUA HOÀN TOÀN toàn bộ các nội dung dấu chìm này, không trích xuất chúng, không chèn các ký tự rác vụn vặt đó vào văn bản trả về.\n\n"
                
                "🔴 QUY TẮC ĐỊNH DẠNG VĂN BẢN HÀNH CHÍNH:\n"
                "1. BẢO TOÀN CHỮ IN ĐẬM/IN NGHIÊNG: Đoạn văn nào in đậm bắt buộc bọc trong `**` (Ví dụ: **CHÍNH PHỦ**), đoạn nào in nghiêng bọc trong `*`.\n"
                "2. THỤT LỀ ĐẦU DÒNG: Nếu đoạn văn hoặc điều khoản có thụt lề đầu dòng, hãy thêm đúng 4 dấu cách '    ' vào đầu dòng.\n"
                "3. TOÁN HỌC / SỐ LIỆU: Chuyển toàn bộ công thức toán hoặc số mũ về Unicode thuần đẹp mắt (Ví dụ: x², u_n, phân số dùng dấu / rõ ràng).\n"
                "4. Dựng bảng biểu số liệu chính xác bằng cấu trúc bảng Markdown sử dụng ký tự '|'.\n"
                "5. Chỉ trả về nội dung tài liệu sạch, không thêm bất kỳ lời bình luận hay giải thích nào của AI."
            )
            
            try:
                # Sử dụng gemini-2.5-flash hoặc gemini-2.5-pro để có năng lực xử lý hình ảnh OCR tốt nhất
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[file_part, prompt]
                )
                extracted_text = response.text
            except Exception as e:
                st.error(f"Lỗi khi kết nối hệ thống AI OCR: {e}")

        if extracted_text.strip():
            st.success("✅ Đã xử lý lọc rác và bảo toàn cấu trúc thành công!")
            
            with st.expander("👀 Xem trước văn bản sạch (Đã lọc bỏ dấu chìm)"):
                st.text_area("Văn bản trích xuất:", extracted_text, height=300)
            
            word_file = create_word_document(extracted_text)
            
            st.download_button(
                label="📥 Tải file WORD (.docx) Văn Bản Sạch về máy",
                data=word_file,
                file_name=uploaded_file.name.rsplit('.', 1)[0] + "_van_ban_sach.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("Không thể xử lý dữ liệu từ file này.")

# --- FOOTER CỐ ĐỊNH ---
st.divider()
st.markdown(
    """
    <div style="text-align: center; font-size: 0.8em; color: grey;">
        Ứng dụng được phát triển bởi Ngô Thanh Hùng
    </div>
    """,
    unsafe_allow_html=True
)
