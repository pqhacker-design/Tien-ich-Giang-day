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

st.title("🔄 Chuyển đổi Tài liệu sang Word (Unicode Thuần Bền Vững)")
st.caption("Phiên bản chuẩn hóa Unicode: Không dùng mã Equation phức tạp, cam kết hiển thị mượt mà 100% trên mọi thiết bị.")

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

# ==================== HÀM TẠO FILE WORD UNICODE THUẦN ====================
def create_word_document(text_content):
    doc = Document()
    
    # Định dạng căn lề trang đề thi tiêu chuẩn (Top/Bottom/Left/Right = 2cm)
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)

    # Cấu hình font chữ hệ thống mặc định sang Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    lines = text_content.split('\n')
    in_table = False
    table_data = []

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        # 1. NHẬN DIỆN VÀ DỰNG BẢNG BIỂU
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
                            word_table.rows[r_idx].cells[c_idx].text = val
                
                doc.add_paragraph()
                in_table = False
                table_data = []

        # 2. XỬ LÝ CĂN NGANG ĐÁP ÁN TRẮC NGHIỆM (A, B, C, D)
        if re.search(r'A\..*B\..*C\..*D\.', clean_line) or re.search(r'A\s*[\.\)].*B\s*[\.\)].*C\s*[\.\)].*D\s*[\.\)]', clean_line):
            p = doc.add_paragraph()
            parts = re.split(r'(A\.|B\.|C\.|D\.)', clean_line)
            for part in parts:
                if part in ['A.', 'B.', 'C.', 'D.']:
                    run = p.add_run("    " + part + " ")
                    run.bold = True
                else:
                    p.add_run(part)
            continue

        # 3. XỬ LÝ TIÊU ĐỀ HOẶC CÁC DÒNG CHỮ ĐẶC BIỆT CHÍNH THỨC
        if clean_line.startswith('# '):
            h = doc.add_heading(clean_line.replace('# ', ''), level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif clean_line.startswith('## '):
            doc.add_heading(clean_line.replace('## ', ''), level=2)
        elif any(keyword in clean_line.upper() for keyword in ["BỘ GIÁO DỤC", "ĐỀ THI CHÍNH THỨC", "KỲ THI TỐT NGHIỆP", "MÔN THI"]):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(clean_line)
            run.bold = True
        else:
            # DÒNG CÂU HỎI VÀ NỘI DUNG VĂN BẢN THƯỜNG
            p = doc.add_paragraph()
            if clean_line.startswith("Câu "):
                match = re.match(r'(Câu \d+\.)(.*)', clean_line)
                if match:
                    bold_part, regular_part = match.groups()
                    p.add_run(bold_part).bold = True
                    p.add_run(regular_part)
                else:
                    p.add_run(clean_line)
            else:
                p.add_run(clean_line)

    # Đề phòng bảng biểu nằm ở dòng cuối cùng của văn bản
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

# --- GIAO DIỆN STREAMLIT UPLOAD VÀ XỬ LÝ ---
uploaded_file = st.file_uploader(
    "Tải lên File đề thi (Ảnh hoặc PDF) để số hóa sang Unicode:",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    file_type = uploaded_file.type
    extracted_text = ""
    
    st.info(f"📁 Đã tải lên file thành công: **{uploaded_file.name}**")
    
    if st.button("🚀 Thực hiện trích xuất sang văn bản thuần"):
        with st.spinner("Hệ thống AI đang chuyển đổi toàn bộ công thức toán thành ký tự Unicode thuần..."):
            
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
            
            if not extracted_text.strip():
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
                file_part = types.Part.from_bytes(data=file_bytes, mime_type=file_type)
                
                # Prompt ÉP BUỘC AI chuyển đổi công thức sang chữ và ký tự Unicode phổ thông
                prompt = (
                    "Bạn là một chuyên gia số hóa tài liệu. Hãy trích xuất chính xác văn bản từ hình ảnh này.\n"
                    "QUY TẮC CHUYỂN ĐỔI TOÁN HỌC SANG UNICODE THUẦN (CẤM DÙNG LATEX/EQUATION):\n"
                    "1. Không dùng các ký tự như $, \\frac, \\vec, \\int, \\log. Hãy chuyển tất cả thành ký tự văn bản thuần có thể đọc được.\n"
                    "2. Biến đổi cụ thể:\n"
                    "   - Phân số: Dùng dấu gạch chéo (Ví dụ: 8/3, 2/3).\n"
                    "   - Vectơ: Thêm chữ vectơ hoặc dùng mũi tên Unicode phía trước (Ví dụ: vectơ AD hoặc →AD).\n"
                    "   - Số mũ và chỉ số dưới: Dùng ký tự Unicode nhỏ (Ví dụ: x², u₁, u₃, log₃(3x)).\n"
                    "   - Tập hợp: Dùng ký tự chuẩn như ℝ, ≠, ∈, d, q.\n"
                    "   - Đạo hàm: Dùng dấu phẩy đơn (Ví dụ: f'(x) = 2x).\n"
                    "3. Giữ nguyên định dạng các đáp án trắc nghiệm A, B, C, D nằm ngang trên cùng một dòng văn bản.\n"
                    "4. Chỉ trả về nội dung đề thi được làm sạch, không thêm lời thoại của AI."
                )
                
                try:
                    response = client.models.generate_content(
                        model="gemini-3.5-flash",  # Sử dụng bản 3.5 để hiểu văn cảnh chuyển đổi Unicode tốt nhất
                        contents=[file_part, prompt]
                    )
                    extracted_text = response.text
                except Exception as e:
                    st.error(f"Lỗi khi kết nối API: {e}")

        if extracted_text.strip():
            st.success("✅ Đã chuẩn hóa văn bản thành công!")
            
            with st.expander("👀 Xem trước văn bản trích xuất (Unicode thuần)"):
                st.text_area("Văn bản trích xuất:", extracted_text, height=300)
            
            word_file = create_word_document(extracted_text)
            
            st.download_button(
                label="📥 Tải file WORD (.docx) Unicode siêu bền vững",
                data=word_file,
                file_name=uploaded_file.name.rsplit('.', 1)[0] + "_unicode.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("Không tìm thấy nội dung ký tự từ file.")

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
