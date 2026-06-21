import streamlit as st
import io
import re
from google import genai
from google.genai import types
import pdfplumber
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Chuyển đổi Tài liệu sang Word", page_icon="🔄", layout="centered")

st.title("🔄 Chuyển đổi Ảnh/PDF sang Word Pro")
st.caption("Phiên bản cao cấp: Tự động dựng bảng, căn ngang đáp án trắc nghiệm và tối ưu công thức.")

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

# --- HÀM TẠO FILE WORD THÔNG MINH (GIỮ ĐỊNH DẠNG HÌNH HỌC & BẢNG) ---
def create_word_document(text_content):
    doc = Document()
    
    # Thiết lập căn lề trang chuẩn văn bản hành chính (Lề 2cm mỗi bên)
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)

    # Đặt font chữ mặc định cho toàn văn bản là Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    lines = text_content.split('\n')
    
    in_table = False
    table_data = []

    for line in lines:
        clean_line = line.strip()
        
        # Loại bỏ ký tự bao công thức toán học $ để hiển thị sạch đẹp
        clean_line = clean_line.replace('$', '')

        # 1. Xử lý Bảng biểu (Nhận diện định dạng bảng Markdown của AI)
        if clean_line.startswith('|'):
            if '---|' in clean_line or '===' in clean_line:
                continue # Bỏ qua dòng kẻ phân cách bảng của markdown
            
            in_table = True
            # Tách các cột dựa trên ký tự |
            columns = [col.strip() for col in clean_line.split('|')[1:-1]]
            if columns:
                table_data.append(columns)
            continue
        else:
            # Nếu vừa kết thúc một bảng, tiến hành dựng bảng vào Word
            if in_table and table_data:
                num_rows = len(table_data)
                num_cols = max(len(row) for row in table_data)
                
                word_table = doc.add_table(rows=num_rows, cols=num_cols)
                word_table.style = 'Table Grid' # Thêm đường viền ô lưới cho bảng
                
                for r_idx, row in enumerate(table_data):
                    for c_idx, val in enumerate(row):
                        if c_idx < len(word_table.rows[r_idx].cells):
                            word_table.rows[r_idx].cells[c_idx].text = val
                
                doc.add_paragraph() # Dòng trống sau bảng
                in_table = False
                table_data = []

        # 2. Xử lý cấu trúc Đáp án Trắc nghiệm (Căn ngang hàng nếu chứa A. B. C. D.)
        if re.search(r'A\..*B\..*C\..*D\.', clean_line) or re.search(r'A\s*[\.\)].*B\s*[\.\)].*C\s*[\.\)].*D\s*[\.\)]', clean_line):
            p = doc.add_paragraph()
            # Tìm kiếm các mốc đáp án để tab khoảng cách đều nhau trên Word
            parts = re.split(r'(A\.|B\.|C\.|D\.)', clean_line)
            current_run = None
            for part in parts:
                if part in ['A.', 'B.', 'C.', 'D.']:
                    current_run = p.add_run("   " + part + " ")
                    current_run.bold = True
                else:
                    p.add_run(part)
            continue

        # 3. Xử lý Tiêu đề lớn (Ví dụ: BỘ GIÁO DỤC VÀ ĐÀO TẠO, ĐỀ THI...)
        if clean_line.startswith('# '):
            h = doc.add_heading(clean_line.replace('# ', ''), level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif clean_line.startswith('## '):
            doc.add_heading(clean_line.replace('## ', ''), level=2)
        elif any(keyword in clean_line.upper() for keyword in ["BỘ GIÁO DỤC", "ĐỀ THI CHÍNH THỨC", "KỲ THI TỐT NGHIỆP"]):
            p = doc.add_paragraph()
            run = p.add_run(clean_line)
            run.bold = True
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            # Các dòng văn bản hoặc câu hỏi thông thường
            if clean_line:
                p = doc.add_paragraph()
                if clean_line.startswith("Câu "):
                    # Bôi đậm chữ "Câu X." cho đúng chuẩn đề thi
                    match = re.match(r'(Câu \d+\.)(.*)', clean_line)
                    if match:
                        bold_part, regular_part = match.groups()
                        p.add_run(bold_part).bold = True
                        p.add_run(regular_part)
                    else:
                        p.add_run(clean_line)
                else:
                    p.add_run(clean_line)

    # Xử lý trường hợp bảng nằm ở cuối cùng của văn bản
    if in_table and table_data:
        word_table = doc.add_table(rows=len(table_data), cols=max(len(row) for row in table_data))
        word_table.style = 'Table Grid'
        for r_idx, row in enumerate(table_data):
            for c_idx, val in enumerate(row):
                if c_idx < len(word_table.rows[r_idx].cells):
                    word_table.rows[r_idx].cells[c_idx].text = val

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- GIAO DIỆN TẢI FILE ---
uploaded_file = st.file_uploader(
    "Tải lên File ảnh đề thi hoặc File PDF cần chuyển đổi cấu trúc:",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    file_type = uploaded_file.type
    extracted_text = ""
    
    st.info(f"📁 Đã nhận dữ liệu: **{uploaded_file.name}**")
    
    if st.button("🚀 Bắt đầu trích xuất & Dựng bố cục Word"):
        with st.spinner("Hệ thống AI đang phân tích dạng cột, tái lập bảng biểu và xóa rác định dạng..."):
            
            if file_type == "application/pdf":
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        text_pages = []
                        for page in pdf.pages:
                            page_text = page.extract_text(layout=True)
                            if page_text:
                                text_pages.append(page_text)
                        extracted_text = "\n".join(text_pages)
                except Exception:
                    pass
            
            # Nếu trích xuất text thô từ PDF trống (PDF dạng scanned), hoặc file tải lên là file Ảnh
            if not extracted_text.strip():
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
                file_part = types.Part.from_bytes(data=file_bytes, mime_type=file_type)
                
                # Prompt ép cấu trúc văn bản đầu ra cho AI
                prompt = (
                    "Bạn là một chuyên gia số hóa đề thi. Hãy trích xuất toàn bộ chữ trong ảnh này.\n"
                    "QUY TẮC ĐỊNH DẠNG BẮT BUỘC:\n"
                    "1. Các câu hỏi trắc nghiệm có đáp án A, B, C, D nằm ngang thì PHẢI giữ nguyên trên cùng một dòng văn bản. Không được tự ý xuống dòng các lựa chọn A, B, C, D.\n"
                    "2. Nếu có bảng biểu (ví dụ: bảng tần số, bảng số liệu học trực tuyến), hãy xuất ra dưới dạng bảng cấu trúc Markdown hoàn chỉnh sử dụng các ký tự |. Ví dụ:\n"
                    "| Cột 1 | Cột 2 |\n"
                    "|---|---|\n"
                    "| Dữ liệu | Dữ liệu |\n"
                    "3. Không thêm các lời giải thích, lời thoại của AI. Chỉ trả về nội dung đề thi."
                )
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[file_part, prompt]
                    )
                    extracted_text = response.text
                except Exception as e:
                    st.error(f"Lỗi khi kết nối với máy chủ AI OCR: {e}")

        # --- HIỂN THỊ KẾT QUẢ VÀ NÚT TẢI FILE ---
        if extracted_text.strip():
            st.success("✅ Đã xử lý bố cục cấu trúc thành công!")
            
            with st.expander("👀 Xem trước cấu trúc văn bản trích xuất"):
                st.text_area("Bản xem trước:", extracted_text, height=300)
            
            word_file = create_word_document(extracted_text)
            
            st.download_button(
                label="📥 Tải file WORD (.docx) chuẩn cấu trúc về máy",
                data=word_file,
                file_name=uploaded_file.name.rsplit('.', 1)[0] + "_chuan_dinh_dang.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("Không thể đọc được cấu trúc từ file này. Anh vui lòng tải lại file rõ nét hơn nhé.")

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
