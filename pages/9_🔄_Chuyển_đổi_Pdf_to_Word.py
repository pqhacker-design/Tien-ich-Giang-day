import streamlit as st
import io
import re
from google import genai
from google.genai import types
import pdfplumber
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Chuyển đổi Tài liệu sang Word", page_icon="🔄", layout="centered")

st.title("🔄 Chuyển đổi Tài liệu sang Word Pro (Math Equation)")
st.caption("Hệ thống chuyển đổi nâng cao: Tự động dựng công thức Toán chuẩn Microsoft Equation, giữ bảng và căn cột trắc nghiệm.")

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

# ================= HỆ THỐNG BIẾN ĐỔI LATEX SANG MS WORD EQUATION (OMML) =================
def create_element(name):
    return OxmlElement(name)

def create_attribute(element, name, value):
    element.set(qn(name), value)

def convert_latex_to_omml_run(paragraph, text):
    """
    Hàm phân tích chuỗi văn bản xen kẽ công thức toán dạng $...$ 
    và dựng hộp công thức Equation trực tiếp vào đoạn văn Word.
    """
    # Khai báo namespace toán học chuẩn Office
    m_ns = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
    
    # Tách chuỗi theo dấu $ câu công thức
    parts = re.split(r'(\$.*?\$)', text)
    
    for part in parts:
        if part.startswith('$') and part.endswith('$'):
            latex_formula = part[1:-1].strip()
            
            # --- TỐI ƯU CƠ BẢN CÁC KÝ HIỆU TOÁN THƯỜNG GẶP SANG OMML ---
            # Tạo thẻ vùng chứa công thức toán (m:oMath)
            oMath = OxmlElement('m:oMath')
            
            # Xử lý phân số dạng \frac{tử}{mẫu}
            frac_match = re.search(r'\\frac{(.*?)}{(.*?)}', latex_formula)
            if frac_match:
                num, den = frac_match.groups()
                f_elem = OxmlElement('m:f')
                num_elem = OxmlElement('m:num')
                den_elem = OxmlElement('m:den')
                
                # Tạo text cho tử số
                r1 = OxmlElement('m:r')
                t1 = OxmlElement('m:t')
                t1.text = num
                r1.append(t1)
                num_elem.append(r1)
                
                # Tạo text cho mẫu số
                r2 = OxmlElement('m:r')
                t2 = OxmlElement('m:t')
                t2.text = den
                r2.append(t2)
                den_elem.append(r2)
                
                f_elem.append(num_elem)
                f_elem.append(den_elem)
                oMath.append(f_elem)
            else:
                # Dọn rác các ký tự gạch chéo LaTeX phổ biến để hiển thị đẹp trong Word
                display_text = latex_formula
                display_text = display_text.replace(r'\vec', 'Vectơ ')
                display_text = display_text.replace(r'\int', '∫')
                display_text = display_text.replace(r'\sin', 'sin')
                display_text = display_text.replace(r'\cos', 'cos')
                display_text = display_text.replace(r'\log', 'log')
                display_text = display_text.replace(r'\mathbb{R}', 'ℝ')
                display_text = display_text.replace(r'\neq', '≠')
                display_text = display_text.replace(r'\cdot', '·')
                display_text = display_text.replace(r'\prime', "'")
                
                mr = OxmlElement('m:r')
                mt = OxmlElement('m:t')
                mt.text = display_text
                mr.append(mt)
                oMath.append(mr)
                
            paragraph._p.append(oMath)
        else:
            if part:
                # Nếu là văn bản thông thường, chèn dạng văn bản thường
                paragraph.add_run(part)

# ==================== HÀM TẠO FILE WORD CHUẨN CẤU TRÚC ĐỀ THI ====================
def create_word_document(text_content):
    doc = Document()
    
    # Định dạng căn lề trang đề thi chuẩn (Top/Bottom/Left/Right = 2cm)
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)

    # Cấu hình font chữ hệ thống
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

        # 1. NHẬN DIỆN VÀ DỰNG BẢNG BIỂU CỦA ĐỀ THI
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
                            # Áp dụng công thức toán học vào từng ô của bảng nếu có
                            p_cell = word_table.rows[r_idx].cells[c_idx].paragraphs[0]
                            convert_latex_to_omml_run(p_cell, val)
                
                doc.add_paragraph()
                in_table = False
                table_data = []

        # 2. XỬ LÝ CĂN NGANG ĐÁP ÁN TRẮC NGHIỆM TỰ ĐỘNG
        if re.search(r'A\..*B\..*C\..*D\.', clean_line) or re.search(r'A\s*[\.\)].*B\s*[\.\)].*C\s*[\.\)].*D\s*[\.\)]', clean_line):
            p = doc.add_paragraph()
            parts = re.split(r'(A\.|B\.|C\.|D\.)', clean_line)
            for part in parts:
                if part in ['A.', 'B.', 'C.', 'D.']:
                    run = p.add_run("    " + part + " ")
                    run.bold = True
                else:
                    convert_latex_to_omml_run(p, part)
            continue

        # 3. XỬ LÝ TIÊU ĐỀ HOẶC CÁC DÒNG CHỮ ĐẶC BIỆT CHÍNH THỨC
        if clean_line.startswith('# '):
            h = doc.add_heading('', level=1)
            h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            convert_latex_to_omml_run(h, clean_line.replace('# ', ''))
        elif clean_line.startswith('## '):
            h = doc.add_heading('', level=2)
            convert_latex_to_omml_run(h, clean_line.replace('## ', ''))
        elif any(keyword in clean_line.upper() for keyword in ["BỘ GIÁO DỤC", "ĐỀ THI CHÍNH THỨC", "KỲ THI TỐT NGHIỆP"]):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            convert_latex_to_omml_run(p, clean_line)
            for r in p.runs:
                r.bold = True
        else:
            # DÒNG CÂU HỎI VÀ NỘI DUNG VĂN BẢN THƯỜNG
            p = doc.add_paragraph()
            if clean_line.startswith("Câu "):
                match = re.match(r'(Câu \d+\.)(.*)', clean_line)
                if match:
                    bold_part, regular_part = match.groups()
                    p.add_run(bold_part).bold = True
                    convert_latex_to_omml_run(p, regular_part)
                else:
                    convert_latex_to_omml_run(p, clean_line)
            else:
                convert_latex_to_omml_run(p, clean_line)

    # Đề phòng bảng biểu nằm ở dòng cuối cùng của văn bản
    if in_table and table_data:
        word_table = doc.add_table(rows=len(table_data), cols=max(len(row) for row in table_data))
        word_table.style = 'Table Grid'
        for r_idx, row in enumerate(table_data):
            for c_idx, val in enumerate(row):
                if c_idx < len(word_table.rows[r_idx].cells):
                    p_cell = word_table.rows[r_idx].cells[c_idx].paragraphs[0]
                    convert_latex_to_omml_run(p_cell, val)

    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- GIAO DIỆN STREAMLIT UPLOAD VÀ XỬ LÝ ---
uploaded_file = st.file_uploader(
    "Tải lên Đề thi dạng Ảnh (PNG, JPG) hoặc File PDF toán học cần số hóa:",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    file_type = uploaded_file.type
    extracted_text = ""
    
    st.info(f"📁 Đã tải lên file thành công: **{uploaded_file.name}**")
    
    if st.button("🚀 Thực hiện trích xuất và dựng Equation"):
        with st.spinner("Hệ thống toán học AI đang bóc tách cấu trúc và mã hóa hộp công thức MS Word..."):
            
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
                
                # Ép AI bắt buộc phải bao bọc toàn bộ ký hiệu, biểu thức toán học vào cặp dấu đô la $...$
                prompt = (
                    "Bạn là chuyên gia chuyển đổi đề thi toán học sang LaTeX chất lượng cao.\n"
                    "YÊN CẦU QUY TẮC BẮT BUỘC:\n"
                    "1. BẮT BUỘC bao bọc TẤT CẢ các công thức toán, biểu thức số, vectơ, dấu tích phân, biến số (x, y, u_n, d, q...) "
                    "bên trong cặp dấu đô la một lớp. Ví dụ: $A B C D \\cdot A^{\\prime} B^{\\prime} C^{\\prime} D^{\\prime}$, $\\overrightarrow{A D}$, $y=f(x)$, $\\int f(x)dx$, $\\frac{8}{3}$. Không được để công thức toán ở dạng text trần.\n"
                    "2. Các câu hỏi trắc nghiệm có đáp án A, B, C, D nằm ngang thì PHẢI giữ nguyên trên cùng một dòng văn bản.\n"
                    "3. Dựng bảng biểu số liệu (nếu có) chính xác bằng cấu trúc bảng Markdown.\n"
                    "4. Chỉ trả về đề thi, tuyệt đối không viết thêm lời bình luận giải thích."
                )
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[file_part, prompt]
                    )
                    extracted_text = response.text
                except Exception as e:
                    st.error(f"Lỗi khi kết nối API: {e}")

        if extracted_text.strip():
            st.success("✅ Đã xử lý bóc tách toán học thành công!")
            
            with st.expander("👀 Xem trước văn bản trích xuất (Đã gán tag mã hóa toán học)"):
                st.text_area("Mã nguồn văn bản:", extracted_text, height=300)
            
            word_file = create_word_document(extracted_text)
            
            st.download_button(
                label="📥 Tải file WORD (.docx) chứa Equation chuẩn về máy",
                data=word_file,
                file_name=uploaded_file.name.rsplit('.', 1)[0] + "_math_equation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("Không tìm thấy nội dung ký tự từ file. Bạn vui lòng chụp ảnh rõ nét hơn nhé.")

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
