import streamlit as st
import json
import os
import re
from io import BytesIO
import pandas as pd

# Thư viện xử lý tài liệu
import docx
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

import PyPDF2
import google.generativeai as genai

# ==========================================
# CẤU HÌNH TRANG & GIAO DIỆN
# ==========================================
st.set_page_config(
    page_title="SmartTest 2018 - Hệ thống Tạo Đề Kiểm tra Tự động",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho giao diện hiện đại và chuyên nghiệp
st.markdown("""
<style>
    .main-title { font-size: 2.4rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 2rem; }
    .section-header { font-size: 1.4rem; font-weight: 600; color: #0F766E; margin-top: 1.5rem; margin-bottom: 1rem; border-left: 5px solid #0F766E; padding-left: 10px; }
    .stButton>button { width: 100%; background-color: #0F766E; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #0D9488; color: white; }
    .history-card { padding: 10px; border-radius: 5px; border: 1px solid #E5E7EB; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# KHỞI TẠO TRẠNG THÁI (SESSION STATE)
# ==========================================
if 'history' not in st.session_state:
    st.session_state.history = []
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = None
if 'matrix_df' not in st.session_state:
    st.session_state.matrix_df = None
if 'spec_df' not in st.session_state:
    st.session_state.spec_df = None

# ==========================================
# CÁC HÀM TIỆN ÍCH & XỬ LÝ TÀI LIỆU
# ==========================================
def extract_text_from_docx(file_bytes):
    try:
        doc = Document(BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs if p.text])
    except Exception as e:
        st.error(f"Lỗi đọc file DOCX: {e}")
        return ""

def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Lỗi đọc file PDF: {e}")
        return ""

# ==========================================
# KẾT NỐI VÀ XỬ LÝ GEMINI AI
# ==========================================
def init_gemini_client(api_key):
    try:
        genai.configure(api_key=api_key)
        # Sử dụng mô hình gemini-2.5-pro để xử lý tư duy ma trận chính xác nhất
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Lỗi cấu hình Gemini Client: {e}")
        return None
        
def analyze_topics_with_ai(model, text_content):
    """Phân tích văn bản tài liệu và trích xuất danh sách chủ đề"""
    prompt = f"""
    Bạn là chuyên gia thẩm định chương trình GDPT 2018. Hãy đọc văn bản nội dung kiến thức sau và trích xuất ra các Chủ đề/Chương cốt lõi.
    Chỉ trả về danh sách tên các chủ đề, cách nhau bằng dấu gạch đầu dòng (-), không kèm theo lời giải thích nào khác.
    
    Nội dung tài liệu:
    {text_content[:8000]}
    """
    try:
        response = model.generate_content(prompt)
        topics = [line.strip("- ").strip() for line in response.text.split("\n") if line.strip()]
        return topics
    except Exception as e:
        st.error(f"Lỗi phân tích tài liệu bằng AI: {e}")
        return []

def generate_exam_data(model, config, topics, matrix_info):
    """Gọi Gemini API để sinh cấu trúc Đề, Đáp án, Ma trận và Đặc tả dạng JSON"""
    
    # Chuẩn bị Prompt chi tiết, ràng buộc cấu trúc đầu ra là JSON chuẩn
    prompt = f"""
    Bạn là chuyên gia xây dựng đề kiểm tra và đo lường giáo dục theo chuẩn Chương trình GDPT 2018 của Bộ Giáo dục và Đào tạo Việt Nam.
    Hãy tạo một bộ dữ liệu kiểm tra hoàn chỉnh bao gồm: Ma trận, Bảng đặc tả, Đề kiểm tra và Đáp án/Hướng dẫn chấm chi tiết dựa trên các thông tin sau:
    
    THÔNG TIN CHUNG:
    - Môn học: {config['subject']} | Lớp: {config['grade']}
    - Loại đề: {config['exam_type']} | Thời lượng: {config['duration']} phút
    - Học kỳ: {config['semester']} | Năm học: {config['school_year']}
    - Danh sách các chủ đề: {", ".join(topics)}
    
    CẤU TRÚC ĐỀ VÀ TỶ LỆ ĐIỂM:
    - Hình thức: Trắc nghiệm ({config['tn_ratio']}%) và Tự luận ({config['tl_ratio']}%)
    - Tỷ lệ nhận thức: Nhận biết ({config['nb_ratio']}%), Thông hiểu ({config['th_ratio']}%), Vận dụng ({config['vd_ratio']}%), Vận dụng cao ({config['vdc_ratio']}%)
    
    YÊU CẦU ĐỀ KIỂM TRA:
    1. Ngôn ngữ chính xác, khoa học, bám sát ma trận tư duy, phù hợp với tâm sinh lý lứa tuổi học sinh lớp {config['grade']}.
    2. Các câu trắc nghiệm khách quan (TN) phải có 4 lựa chọn (A, B, C, D), phương án nhiễu phải có độ nhiễu hợp lý, không trùng lặp, chỉ có DUY NHẤT 1 đáp án đúng.
    3. Các câu tự luận (TL) phải đi kèm hướng dẫn chấm và thang điểm chi tiết từng bước.
    4. Quy định tổng số câu hỏi ngắn gọn, logic phù hợp với thời gian {config['duration']} phút.
    5. Hãy thực hiện quy trình tự kiểm tra (Self-Correction): Rà soát trùng lặp, kiểm tra logic đáp án và độ khó trước khi xuất kết quả.

    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON NGUYÊN BẢN (KHÔNG CHỨA KHỐI CODE ```json VÀ ```), với cấu trúc chính xác như sau:
    {{
      "ma_tran": [
        {{"chu_de": "Tên chủ đề", "nb_tn": 0, "nb_tl": 0, "th_tn": 0, "th_tl": 0, "vd_tn": 0, "vd_tl": 0, "vdc_tn": 0, "vdc_tl": 0}}
      ],
      "bang_dac_ta": [
        {{"chu_de": "Tên chủ đề", "noi_dung": "Nội dung kiến thức", "muc_do": "Nhận biết/Thông hiểu/...", "yeu_cau_can_dat": "Mô tả yêu cầu đạt", "so_cau": "1 câu TN/TL", "diem": 0.25}}
      ],
      "de_kiem_tra": {{
        "trac_nghiem": [
          {{"id": "Câu 1", "muc_do": "Nhận biết", "chu_de": "...", "cau_hoi": "Nội dung câu hỏi?", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "dap_an": "A"}}
        ],
        "tu_luan": [
          {{"id": "Câu 1 (TL)", "muc_do": "Vận dụng", "chu_de": "...", "cau_hoi": "Nội dung câu hỏi tự luận?", "diem": 1.5}}
        ]]
      }},
      "dap_an_chi_tiet": {{
        "trac_nghiem": {{"Câu 1": "A"}},
        "tu_luan": [
          {{"id": "Câu 1 (TL)", "huong_dan": "Các bước chấm điểm...", "thang_diem": {{"Bước 1...": 0.5, "Bước 2...": 1.0}}}}
        ]
      }}
    }}
    """
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # Xử lý làm sạch chuỗi JSON nếu bị AI bọc trong markdown code block
    raw_text = re.sub(r'^```json\s*', '', raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r'```$', '', raw_text).strip()
    
    return json.loads(raw_text)

# ==========================================
# XUẤT FILE TÀI LIỆU WORD (.DOCX)
# ==========================================
def create_element(name):
    return OxmlElement(name)

def set_cell_border(cell, **kwargs):
    """Hàm tạo viền cho ô trong bảng Docx"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = create_element('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = 'w:{}'.format(edge)
            element = tcBorders.find(qn(tag))
            if element is None:
                element = create_element(tag)
                tcBorders.append(element)
            for key, val in edge_data.items():
                element.set(qn('w:{}'.format(key)), str(val))

def export_to_docx(config, data):
    doc = Document()
    
    # Cấu hình lề trang văn bản
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)
        
    # Kiểu chữ mặc định
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    
    # --- TRANG BÌA THÔNG TIN ---
    p_header = doc.add_paragraph()
    p_header.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_school = p_header.add_run("SỞ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG THCS & THPT THÔNG MINH\n")
    run_school.bold = True
    
    title_p = doc.add_paragraph()
    title_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(20)
    run_title = title_p.add_run(f"ĐỀ KIỂM TRA {config['exam_type'].upper()}\nMÔN: {config['subject'].upper()} - LỚP {config['grade']}\n")
    run_title.bold = True
    run_title.size = Pt(16)
    
    sub_title = doc.add_paragraph()
    sub_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_title.add_run(f"Học kỳ: {config['semester']} | Năm học: {config['school_year']}\nThời gian làm bài: {config['duration']} phút (Không kể thời gian giao đề)\n")
    
    doc.add_page_break()
    
    # --- PHẦN 1: MA TRẬN ĐỀ KIỂM TRA ---
    doc.add_heading("I. MA TRẬN ĐỀ KIỂM TRA", level=1)
    matrix_table = doc.add_table(rows=1, cols=10)
    matrix_table.style = 'Table Grid'
    hdr_cells = matrix_table.rows[0].cells
    headers = ['Chủ đề', 'NB TN', 'NB TL', 'TH TN', 'TH TL', 'VD TN', 'VD TL', 'VDC TN', 'VDC TL', 'Tổng']
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].font.bold = True
        
    for item in data.get('ma_tran', []):
        row_cells = matrix_table.add_row().cells
        row_cells[0].text = str(item.get('chu_de', ''))
        row_cells[1].text = str(item.get('nb_tn', 0))
        row_cells[2].text = str(item.get('nb_tl', 0))
        row_cells[3].text = str(item.get('th_tn', 0))
        row_cells[4].text = str(item.get('th_tl', 0))
        row_cells[5].text = str(item.get('vd_tn', 0))
        row_cells[6].text = str(item.get('vd_tl', 0))
        row_cells[7].text = str(item.get('vdc_tn', 0))
        row_cells[8].text = str(item.get('vdc_tl', 0))
        # Tính tổng câu thô sơ
        total_q = sum([int(item.get(k, 0)) for k in ['nb_tn', 'nb_tl', 'th_tn', 'th_tl', 'vd_tn', 'vd_tl', 'vdc_tn', 'vdc_tl']])
        row_cells[9].text = str(total_q)
        
    doc.add_page_break()
    
    # --- PHẦN 2: BẢNG ĐẶC TẢ ---
    doc.add_heading("II. BẢNG ĐẶC TẢ ĐỀ KIỂM TRA", level=1)
    spec_table = doc.add_table(rows=1, cols=6)
    spec_table.style = 'Table Grid'
    spec_hdrs = ['STT', 'Chủ đề / Kiến thức', 'Mức độ nhận thức', 'Yêu cầu cần đạt', 'Số câu hỏi', 'Điểm']
    for i, h in enumerate(spec_hdrs):
        spec_table.rows[0].cells[i].text = h
        spec_table.rows[0].cells[i].paragraphs[0].runs[0].font.bold = True
        
    for idx, item in enumerate(data.get('bang_dac_ta', [])):
        row_cells = spec_table.add_row().cells
        row_cells[0].text = str(idx + 1)
        row_cells[1].text = f"{item.get('chu_de','')}\n- {item.get('noi_dung','')}"
        row_cells[2].text = str(item.get('muc_do', ''))
        row_cells[3].text = str(item.get('yeu_cau_can_dat', ''))
        row_cells[4].text = str(item.get('so_cau', ''))
        row_cells[5].text = str(item.get('diem', ''))
        
    doc.add_page_break()
    
    # --- PHẦN 3: ĐỀ KIỂM TRA CHÍNH THỨC ---
    doc.add_heading("III. ĐỀ KIỂM TRA CHÍNH THỨC", level=1)
    de = data.get('de_kiem_tra', {})
    
    if de.get('trac_nghiem'):
        p_tn_head = doc.add_paragraph()
        r_tn_head = p_tn_head.add_run("PHẦN I. TRẮC NGHIỆM KHÁCH QUAN")
        r_tn_head.bold = True
        
        for q in de['trac_nghiem']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')}: ").bold = True
            p_q.add_run(q.get('cau_hoi'))
            
            # Ghi các phương án lựa chọn
            opts = q.get('options', {})
            p_opt = doc.add_paragraph()
            p_opt.paragraph_format.left_indent = Inches(0.25)
            p_opt.add_run(f"A. {opts.get('A','')}      B. {opts.get('B','')}      C. {opts.get('C','')}      D. {opts.get('D','')}")
            
    if de.get('tu_luan'):
        p_tl_head = doc.add_paragraph()
        p_tl_head.paragraph_format.space_before = Pt(15)
        r_tl_head = p_tl_head.add_run("PHẦN II. TỰ LUẬN")
        r_tl_head.bold = True
        
        for q in de['tu_luan']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')} ({q.get('diem')} điểm): ").bold = True
            p_q.add_run(q.get('cau_hoi'))
            
    doc.add_page_break()
    
    # --- PHẦN 4: ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM ---
    doc.add_heading("IV. ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM", level=1)
    da = data.get('dap_an_chi_tiet', {})
    
    if da.get('trac_nghiem'):
        doc.add_paragraph().add_run("1. Đáp án phần Trắc nghiệm:").bold = True
        da_tn_table = doc.add_table(rows=1, cols=2)
        da_tn_table.style = 'Table Grid'
        da_tn_table.rows[0].cells[0].text = "Câu hỏi"
        da_tn_table.rows[0].cells[1].text = "Đáp án đúng"
        da_tn_table.rows[0].cells[0].paragraphs[0].runs[0].font.bold = True
        da_tn_table.rows[0].cells[1].paragraphs[0].runs[0].font.bold = True
        
        for q_id, ans in da['trac_nghiem'].items():
            r_cells = da_tn_table.add_row().cells
            r_cells[0].text = str(q_id)
            r_cells[1].text = str(ans)
            
    if da.get('tu_luan'):
        doc.add_paragraph().add_run("\n2. Hướng dẫn chấm phần Tự luận:").bold = True
        for tl_ans in da['tu_luan']:
            p_tl_id = doc.add_paragraph()
            p_tl_id.add_run(f"{tl_ans.get('id')}:").bold = True
            doc.add_paragraph(f"Hướng dẫn chung: {tl_ans.get('huong_dan','')}")
            
            # Bảng chia điểm nhỏ
            st_table = doc.add_table(rows=1, cols=2)
            st_table.style = 'Table Grid'
            st_table.rows[0].cells[0].text = "Nội dung đáp án chi tiết từng bước"
            st_table.rows[0].cells[1].text = "Điểm"
            
            for buoc, diem_buoc in tl_ans.get('thang_diem', {}).items():
                rc = st_table.add_row().cells
                rc[0].text = str(buoc)
                rc[1].text = str(diem_buoc)
                
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# GIAO DIỆN CHÍNH (STREAMLIT APP)
# ==========================================
st.markdown('<div class="main-title">SmartTest 2018: Trợ Lý Số Ra Đề Chuẩn Bộ GD&ĐT</div>', unsafe_allow_html=True)

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.stop()

# Khởi tạo model sau khi đã xác thực có API Key từ trang chủ
model = init_gemini_client(api_key_input)

# Thanh điều hướng Sidebar (Đã lược bỏ ô nhập Key thủ công để tránh dư thừa)
with st.sidebar:
    st.header("🕒 Lịch sử tạo đề")
    if st.session_state.history:
        for idx, item in enumerate(st.session_state.history):
            st.markdown(f"""
            <div class='history-card'>
                <strong>#{idx+1}: {item['subject']} - Lớp {item['grade']}</strong><br/>
                <small>{item['exam_type']} | {item['time']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Chưa có đề nào được tạo trong phiên làm việc này.")
        
# Thiết lập Giao diện chính chia làm các Tab chức năng
tab1, tab2, tab3 = st.tabs(["📋 1. Thiết lập cấu hình đề", "📊 2. Quản lý Ma trận & Đặc tả", "✨ 3. Xem trước & Xuất đề"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">Thông tin tổng quan</div>', unsafe_allow_html=True)
        subject = st.text_input("Môn học:", placeholder="Ví dụ: Toán học, Ngữ văn, Vật lí...")
        grade = st.selectbox("Khối lớp học:", [str(i) for i in range(1, 13)], index=7) # Default Lớp 8
        exam_type = st.selectbox("Loại hình đề kiểm tra:", ["15 phút", "45 phút (1 tiết)", "Giữa học kỳ", "Cuối học kỳ"])
        duration = st.number_input("Thời lượng làm bài (phút):", min_value=15, max_value=180, value=90, step=5)
        semester = st.selectbox("Học kỳ:", ["Học kỳ I", "Học kỳ II"])
        school_year = st.text_input("Năm học:", value="2026-2027")

    with col2:
        st.markdown('<div class="section-header">Nội dung kiến thức & Chủ đề</div>', unsafe_allow_html=True)
        input_method = st.radio("Phương thức xác định chủ đề:", ["Nhập thủ công danh sách chủ đề", "Tải tệp tài liệu giảng dạy lên (AI tự phân tích)"])
        
        topics_list = []
        if input_method == "Nhập thủ công danh sách chủ đề":
            raw_topics = st.text_area("Nhập các chủ đề (Mỗi chủ đề cách nhau bởi một dòng mới):", 
                                      value="Chủ đề 1: Hàm số và Đồ thị\nChủ đề 2: Phương trình bậc hai")
            topics_list = [t.strip() for t in raw_topics.split("\n") if t.strip()]
        else:
            uploaded_file = st.file_uploader("Tải tài liệu lên (Hỗ trợ định dạng .docx, .pdf, .txt):", type=["docx", "pdf", "txt"])
            if uploaded_file is not None:
                with st.spinner("Đang trích xuất và phân tích văn bản nội dung bằng AI..."):
                    file_bytes = uploaded_file.read()
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    
                    text_content = ""
                    if file_ext == "docx":
                        text_content = extract_text_from_docx(file_bytes)
                    elif file_ext == "pdf":
                        text_content = extract_text_from_pdf(file_bytes)
                    else:
                        text_content = file_bytes.decode("utf-8", errors="ignore")
                        
                    if text_content:
                        topics_list = analyze_topics_with_ai(model, text_content)
                        st.success(f"AI đã tìm thấy {len(topics_list)} chủ đề kiến thức lớn phù hợp chương trình học.")
                        for t in topics_list:
                            st.markdown(f"- **{t}**")

with tab2:
    st.markdown('<div class="section-header">Thiết lập ma trận tư duy và Tỷ lệ điểm số</div>', unsafe_allow_html=True)
    
    col_mat1, col_mat2 = st.columns(2)
    with col_mat1:
        st.subheader("1. Tỷ lệ mức độ nhận thức (%)")
        nb_ratio = st.slider("Nhận biết (Mặc định: 30%)", 0, 100, 30)
        th_ratio = st.slider("Thông hiểu (Mặc định: 30%)", 0, 100, 30)
        vd_ratio = st.slider("Vận dụng (Mặc định: 25%)", 0, 100, 25)
        vdc_ratio = st.slider("Vận dụng cao (Mặc định: 15%)", 0, 100, 15)
        
        total_ratio = nb_ratio + th_ratio + vd_ratio + vdc_ratio
        if total_ratio != 100:
            st.error(f"⚠️ Tổng tỷ lệ điểm nhận thức hiện tại là **{total_ratio}%**. Vui lòng cấu hình lại sao cho tổng bằng **100%**.")
        else:
            st.success("✅ Tỷ lệ mức độ phân hóa câu hỏi hợp lệ.")
            
    with col_mat2:
        st.subheader("2. Cấu hình cấu trúc câu hỏi")
        exam_format = st.radio("Cơ cấu hình thức câu hỏi trong đề:", ["Kết hợp Trắc nghiệm & Tự luận", "100% Trắc nghiệm khách quan", "100% Tự luận"])
        
        tn_ratio = 70
        tl_ratio = 30
        if exam_format == "100% Trắc nghiệm khách quan":
            tn_ratio, tl_ratio = 100, 0
        elif exam_format == "100% Tự luận":
            tn_ratio, tl_ratio = 0, 100
        else:
            tn_ratio = st.number_input("Tỷ lệ điểm Trắc nghiệm (%):", min_value=10, max_value=90, value=70, step=5)
            tl_ratio = 100 - tn_ratio
            st.info(f"Tỷ lệ câu hỏi Tự luận tự động tương ứng: {tl_ratio}%")

    st.markdown("---")
    
    # NÚT BẤM KÍCH HOẠT TIẾN TRÌNH AI
    if st.button("🔥 BẮT ĐẦU KHỞI TẠO ĐỀ KIỂM TRA ĐỒNG BỘ"):
        if not subject:
            st.error("Vui lòng điền thông tin Môn học ở Tab 1 trước khi khởi tạo.")
        elif total_ratio != 100:
            st.error("Tổng tỷ lệ nhận thức phải bằng 100% mới có thể tạo ma trận.")
        elif not topics_list:
            st.error("Danh sách chủ đề rỗng, hãy nhập dữ liệu đầu vào hoặc tải tài liệu.")
        else:
            # Tạo gói cấu hình
            config_package = {
                "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration,
                "semester": semester, "school_year": school_year, "nb_ratio": nb_ratio, "th_ratio": th_ratio,
                "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio, "tn_ratio": tn_ratio, "tl_ratio": tl_ratio
            }
            
            progress_bar = st.progress(10)
            status_text = st.empty()
            
            try:
                status_text.text("⚡ Bước 1: Đang phân tích ma trận tư duy & thiết lập bảng đặc tả...")
                progress_bar.progress(30)
                
                # Gọi AI thế hệ mới sinh dữ liệu tổng hợp
                result_json = generate_exam_data(model, config_package, topics_list, matrix_info=None)
                
                progress_bar.progress(70)
                status_text.text("⚡ Bước 2: AI đang thực hiện quy trình kiểm tra chất lượng (Self-Correction)...")
                
                # Lưu dữ liệu vào trạng thái ứng dụng
                st.session_state.generated_data = result_json
                
                # Chuyển đổi dữ liệu ma trận hiển thị thành Dataframe Pandas trực quan
                st.session_state.matrix_df = pd.DataFrame(result_json.get('ma_tran', []))
                st.session_state.spec_df = pd.DataFrame(result_json.get('bang_dac_ta', []))
                
                progress_bar.progress(100)
                status_text.text("🎉 Đã khởi tạo đề thành công! Mời thầy/cô chuyển sang Tab 3 để kiểm tra sản phẩm.")
                
                # Lưu vào lịch sử phiên
                st.session_state.history.append({
                    "subject": subject, "grade": grade, "exam_type": exam_type, "time": pd.Timestamp.now().strftime("%H:%M:%S")
                })
                
            except Exception as e:
                st.error(f"Quá trình sinh đề gặp lỗi từ hệ thống AI hoặc lỗi phân tích cú pháp JSON: {e}")

    # Hiển thị nhanh bảng ma trận nếu có dữ liệu
    if st.session_state.matrix_df is not None:
        st.subheader("📊 Xem trước bảng Ma trận phân bổ vừa sinh tự động")
        st.dataframe(st.session_state.matrix_df, use_container_width=True)

with tab3:
    if st.session_state.generated_data is None:
        st.info("Chưa có đề nào được tạo. Vui lòng hoàn thành thiết lập ở Tab 1, Tab 2 rồi nhấn nút Khởi tạo đề.")
    else:
        g_data = st.session_state.generated_data
        
        # --- THIẾT LẬP NÚT XUẤT TÀI LIỆU .DOCX WORD ---
        st.markdown('<div class="section-header">Tải xuống tài liệu đã hoàn thiện</div>', unsafe_allow_html=True)
        
        config_package = {
            "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration,
            "semester": semester, "school_year": school_year
        }
        
        docx_buffer = export_to_docx(config_package, g_data)
        
        st.download_button(
            label="📥 TẢI FILE ĐỀ KIỂM TRA HOÀN CHỈNH (.DOCX)",
            data=docx_buffer,
            file_name=f"De_kiem_tra_{subject}_Lop{grade}_{exam_type.replace(' ','_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        st.markdown("---")
        st.markdown('<div class="section-header">Bản xem trước trực quan trên Web (Có thể chỉnh sửa)</div>', unsafe_allow_html=True)
        
        # Cho phép giáo viên chỉnh sửa trực tiếp nội dung đề trước khi tải về
        de_preview = g_data.get('de_kiem_tra', {})
        
        st.subheader("✏️ Phần I. Trắc nghiệm")
        if de_preview.get('trac_nghiem'):
            for idx, q in enumerate(de_preview['trac_nghiem']):
                q['cau_hoi'] = st.text_area(f"Nội dung {q.get('id')}:", value=q.get('cau_hoi'), key=f"tn_q_{idx}")
                opts = q.get('options', {})
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a: opts['A'] = st.text_input(f"Đáp án A ({q.get('id')}):", value=opts.get('A'), key=f"tn_a_{idx}")
                with col_b: opts['B'] = st.text_input(f"Đáp án B ({q.get('id')}):", value=opts.get('B'), key=f"tn_b_{idx}")
                with col_c: opts['C'] = st.text_input(f"Đáp án C ({q.get('id')}):", value=opts.get('C'), key=f"tn_c_{idx}")
                with col_d: opts['D'] = st.text_input(f"Đáp án D ({q.get('id')}):", value=opts.get('D'), key=f"tn_d_{idx}")
                
        st.subheader("✏️ Phần II. Tự luận")
        if de_preview.get('tu_luan'):
            for idx, q in enumerate(de_preview['tu_luan']):
                q['cau_hoi'] = st.text_area(f"Nội dung {q.get('id')} ({q.get('diem')}đ):", value=q.get('cau_hoi'), key=f"tl_q_{idx}")
                
        st.success("💡 Thầy/cô có thể sửa đổi văn bản trực tiếp ở trên. File Word (.docx) được tải về sau đó sẽ cập nhật chính xác theo những chỉnh sửa này.")
