import streamlit as st
import json
import os
import re
import random
import copy
from io import BytesIO
import pandas as pd

# Thư viện xử lý tài liệu
import docx
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

import PyPDF2
import google.generativeai as genai

# ==========================================
# CẤU HÌNH TRANG & GIAO DIỆN
# ==========================================
st.set_page_config(
    page_title="SmartTest 2018 - Hệ thống Tạo Đề Tự động (Chuẩn Ký hiệu Khoa học)",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if 'multi_codes_data' not in st.session_state:
    st.session_state.multi_codes_data = {}

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
# THUẬT TOÁN ĐẢO CÂU HỎI VÀ ĐÁP ÁN (TẠO MÃ ĐỀ)
# ==========================================
def shuffle_exam(original_data, code_number):
    shuffled_data = copy.deepcopy(original_data)
    de_goc = shuffled_data.get('de_kiem_tra', {})
    tn_questions = de_goc.get('trac_nghiem', [])
    
    if not tn_questions:
        return shuffled_data
        
    random.seed(int(code_number) + 42)
    random.shuffle(tn_questions)
    
    new_dap_an_tn = {}
    
    for idx, q in enumerate(tn_questions):
        new_id = f"Câu {idx + 1}"
        q['id'] = new_id
        
        opts = q.get('options', {})
        old_correct_key = q.get('dap_an')
        old_correct_value = opts.get(old_correct_key)
        
        opt_items = list(opts.items())
        opt_values = [item[1] for item in opt_items]
        random.shuffle(opt_values)
        
        new_opts = {}
        new_correct_key = "A"
        for o_idx, char in enumerate(['A', 'B', 'C', 'D']):
            new_opts[char] = opt_values[o_idx]
            if opt_values[o_idx] == old_correct_value:
                new_correct_key = char
                
        q['options'] = new_opts
        q['dap_an'] = new_correct_key
        new_dap_an_tn[new_id] = new_correct_key

    shuffled_data['de_kiem_tra']['trac_nghiem'] = tn_questions
    shuffled_data['dap_an_chi_tiet']['trac_nghiem'] = new_dap_an_tn
    return shuffled_data

# ==========================================
# KẾT NỐI VÀ XỬ LÝ GEMINI AI (ĐỊNH DẠNG KHÓA KÝ HIỆU)
# ==========================================
def init_gemini_client(api_key):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Lỗi cấu hình Gemini Client: {e}")
        return None

def analyze_topics_with_ai(model, text_content):
    prompt = f"""
    Bạn là chuyên gia thẩm định chương trình GDPT 2018. Hãy đọc văn bản kiến thức sau và trích xuất ra các Chủ đề/Chương cốt lõi.
    Chỉ trả về danh sách tên các chủ đề, cách nhau bằng dấu gạch đầu dòng (-), không kèm theo lời giải thích nào khác.
    Nội dung tài liệu: {text_content[:3000]}
    """
    try:
        response = model.generate_content(prompt)
        return [line.strip("- ").strip() for line in response.text.split("\n") if line.strip()]
    except Exception as e:
        st.error(f"Lỗi phân tích tài liệu: {e}")
        return []

def generate_exam_data(model, config, topics):
    # Prompt nâng cấp bắt buộc định dạng ký hiệu toán lý hóa chuẩn xác cao bằng LaTeX lồng Unicode
    prompt = f"""
    Bạn là chuyên gia xây dựng đề kiểm tra các môn khoa học Tự nhiên (Toán, Lý, Hóa) theo chuẩn Chương trình GDPT 2018 của Bộ Giáo dục và Đào tạo Việt Nam.
    Hãy tạo một bộ dữ liệu kiểm tra hoàn chỉnh bao gồm: Ma trận, Bảng đặc tả, Đề kiểm tra và Đáp án/Hướng dẫn chấm chi tiết dựa trên các thông tin sau:
    
    THÔNG TIN CHUNG:
    - Môn học: {config['subject']} | Lớp: {config['grade']}
    - Loại đề: {config['exam_type']} | Thời lượng: {config['duration']} phút
    - Học kỳ: {config['semester']} | Năm học: {config['school_year']}
    - Danh sách các chủ đề: {", ".join(topics)}
    
    CẤU TRÚC SỐ LƯỢNG CÂU HỎI & TỶ LỆ ĐIỂM:
    - BẮT BUỘC sinh đúng số lượng: {config['num_tn']} câu trắc nghiệm (TN) và {config['num_tl']} câu tự luận (TL).
    - Phân bổ nhận thức: Nhận biết ({config['nb_ratio']}%), Thông hiểu ({config['th_ratio']}%), Vận dụng ({config['vd_ratio']}%), Vận dụng cao ({config['vdc_ratio']}%)
    
    QUY ĐỊNH BẮT BUỘC VỀ KÝ HIỆU KHOA HỌC:
    1. ĐỐI VỚI MÔN TOÁN: Mọi công thức, biểu thức, phương trình, phân số, căn thức, ký hiệu hình học phải viết bằng cú pháp LaTeX lồng trong dấu đô-la đơn ($...$) để hiển thị trên web, đồng thời dùng các ký tự Unicode toán học trực quan (ví dụ: dùng x², √x, 1/2 hoặc phân số rõ ràng, ∈, ∉, ⊥, ∥, ΔABC) để khi xuất sang file Word (.docx) không bị lỗi hiển thị.
    2. ĐỐI VỚI MÔN VẬT LÍ: Ghi rõ ký hiệu đơn vị chuẩn (V, A, Ω, m/s², N, J, W, λ, u, kg...). Công thức tính phải rõ ràng, ví dụ: $A = F \\cdot s \\cdot \\cos\\alpha$ hoặc sử dụng các ký tự rõ ràng.
    3. ĐỐI VỚI MÔN HÓA HỌC: Công thức hóa học phải viết đúng chỉ số dưới (ví dụ viết H₂SO₄, CO₂, Fe(OH)₃), mũi tên phản ứng dùng dấu (→ hoặc ⇌) và ghi rõ điều kiện nhiệt độ (t°) nếu có. Không viết ngang hàng dạng H2SO4.
    
    BẮT BUỘC TRẢ VỀ ĐỊNH DẠNG JSON NGUYÊN BẢN (KHÔNG CHỨA KHỐI CODE ```json VÀ ```), cấu trúc chính xác như sau:
    {{
      "ma_tran": [
        {{"chu_de": "Tên chủ đề", "nb_tn": 0, "nb_tl": 0, "th_tn": 0, "th_tl": 0, "vd_tn": 0, "vd_tl": 0, "vdc_tn": 0, "vdc_tl": 0}}
      ],
      "bang_dac_ta": [
        {{"chu_de": "Tên chủ đề", "noi_dung": "Nội dung kiến thức", "muc_do": "Nhận biết/Thông hiểu/...", "yeu_cau_can_dat": "Mô tả yêu cầu đạt", "so_cau": "1 câu TN/TL", "diem": 0.25}}
      ],
      "de_kiem_tra": {{
        "trac_nghiem": [
          {{"id": "Câu 1", "muc_do": "Nhận biết", "chu_de": "...", "cau_hoi": "Nội dung câu hỏi chứa ký hiệu khoa học?", "options": {{"A": "Phương án A", "B": "Phương án B", "C": "Phương án C", "D": "Phương án D"}}, "dap_an": "A"}}
        ],
        "tu_luan": [
          {{"id": "Câu 1 (TL)", "muc_do": "Vận dụng", "chu_de": "...", "cau_hoi": "Nội dung bài tập tự luận chứa công thức?", "diem": 1.5}}
        ]
      }},
      "dap_an_chi_tiet": {{
        "trac_nghiem": {{"Câu 1": "A"}},
        "tu_luan": [
          {{"id": "Câu 1 (TL)", "huong_dan": "Các bước chấm kèm biểu thức toán lý hóa...", "thang_diem": {{"Bước 1...": 0.5, "Bước 2...": 1.0}}}}
        ]
      }}
    }}
    """
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    raw_text = re.sub(r'^```json\s*', '', raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r'```$', '', raw_text).strip()
    return json.loads(raw_text)

# ==========================================
# XUẤT FILE TÀI LIỆU WORD (.DOCX)
# ==========================================
def export_to_docx(config, data, code_label="ĐỀ GỐC"):
    doc = Document()
    
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)
        
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    
    # --- TRANG BÌA ---
    p_header = doc.add_paragraph()
    p_header.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_header.add_run("SỞ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG THCS & THPT THÔNG MINH\n").bold = True
    
    title_p = doc.add_paragraph()
    title_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(20)
    run_title = title_p.add_run(f"ĐỀ KIỂM TRA {config['exam_type'].upper()}\nMÔN: {config['subject'].upper()} - LỚP {config['grade']}\n")
    run_title.bold = True
    run_title.size = Pt(16)
    
    sub_title = doc.add_paragraph()
    sub_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_title.add_run(f"Học kỳ: {config['semester']} | Năm học: {config['school_year']}\nMÃ ĐỀ: {code_label}\nThời gian làm bài: {config['duration']} phút\n")
    
    doc.add_page_break()
    
    # Kiện toàn hàm loại bỏ dấu $ khi ghi vào Word để tránh làm rối chữ của giáo viên
    def clean_math_text(text):
        return str(text).replace('$', '')

    # --- PHẦN MA TRẬN & ĐẶC TẢ ---
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
        row_cells[0].text = clean_math_text(item.get('chu_de', ''))
        row_cells[1].text = str(item.get('nb_tn', 0))
        row_cells[2].text = str(item.get('nb_tl', 0))
        row_cells[3].text = str(item.get('th_tn', 0))
        row_cells[4].text = str(item.get('th_tl', 0))
        row_cells[5].text = str(item.get('vd_tn', 0))
        row_cells[6].text = str(item.get('vd_tl', 0))
        row_cells[7].text = str(item.get('vdc_tn', 0))
        row_cells[8].text = str(item.get('vdc_tl', 0))
        total_q = sum([int(item.get(k, 0)) for k in ['nb_tn', 'nb_tl', 'th_tn', 'th_tl', 'vd_tn', 'vd_tl', 'vdc_tn', 'vdc_tl']])
        row_cells[9].text = str(total_q)
        
    doc.add_page_break()
    
    # --- PHẦN ĐỀ KIỂM TRA CHÍNH THỨC ---
    doc.add_heading(f"II. ĐỀ KIỂM TRA CHÍNH THỨC - MÃ ĐỀ: {code_label}", level=1)
    de = data.get('de_kiem_tra', {})
    
    if de.get('trac_nghiem'):
        p_tn_head = doc.add_paragraph()
        p_tn_head.add_run("PHẦN I. TRẮC NGHIỆM KHÁCH QUAN").bold = True
        
        for q in de['trac_nghiem']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')}: ").bold = True
            p_q.add_run(clean_math_text(q.get('cau_hoi')))
            
            opts = q.get('options', {})
            p_opt = doc.add_paragraph()
            p_opt.paragraph_format.left_indent = Inches(0.25)
            p_opt.add_run(f"A. {clean_math_text(opts.get('A',''))}      B. {clean_math_text(opts.get('B',''))}      C. {clean_math_text(opts.get('C',''))}      D. {clean_math_text(opts.get('D',''))}")
            
    if de.get('tu_luan'):
        p_tl_head = doc.add_paragraph()
        p_tl_head.paragraph_format.space_before = Pt(15)
        p_tl_head.add_run("PHẦN II. TỰ LUẬN").bold = True
        
        for q in de['tu_luan']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')} ({q.get('diem')} điểm): ").bold = True
            p_q.add_run(clean_math_text(q.get('cau_hoi')))
            
    doc.add_page_break()
    
    # --- ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM ---
    doc.add_heading(f"III. ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM - MÃ ĐỀ: {code_label}", level=1)
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
            doc.add_paragraph(f"Hướng dẫn chung: {clean_math_text(tl_ans.get('huong_dan',''))}")
            
            st_table = doc.add_table(rows=1, cols=2)
            st_table.style = 'Table Grid'
            st_table.rows[0].cells[0].text = "Nội dung đáp án chi tiết từng bước"
            st_table.rows[0].cells[1].text = "Điểm"
            
            for buoc, diem_buoc in tl_ans.get('thang_diem', {}).items():
                rc = st_table.add_row().cells
                rc[0].text = clean_math_text(buoc)
                rc[1].text = str(diem_buoc)
                
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# GIAO DIỆN CHÍNH (STREAMLIT APP)
# ==========================================
# Lấy API Key tập trung từ trang chủ
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.stop()

model = init_gemini_client(api_key_input)

tab1, tab2, tab3 = st.tabs(["📋 1. Cấu hình thông tin", "📊 2. Quản lý Ma trận đề", "✨ 3. Xem trước & Xuất đề"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Thông tin tổng quan</div>', unsafe_allow_html=True)
        subject = st.selectbox("Môn học khoa học tự nhiên:", ["Toán học", "Vật lí", "Hóa học", "Khoa học tự nhiên (KHTN)"])
        grade = st.selectbox("Khối lớp học:", [str(i) for i in range(6, 13)], index=2) # Thường tập trung cấp 2-3
        exam_type = st.selectbox("Loại hình đề kiểm tra:", ["15 phút", "45 phút (1 tiết)", "Giữa học kỳ", "Cuối học kỳ"])
        duration = st.number_input("Thời lượng làm bài (phút):", min_value=15, max_value=180, value=45, step=5)
        semester = st.selectbox("Học kỳ:", ["Học kỳ I", "Học kỳ II"])
        school_year = st.text_input("Năm học:", value="2026-2027")

    with col2:
        st.markdown('<div class="section-header">Nội dung kiến thức</div>', unsafe_allow_html=True)
        input_method = st.radio("Phương thức xác định chủ đề:", ["Nhập thủ công danh sách chủ đề", "Tải tệp tài liệu giảng dạy lên (AI tự phân tích)"])
        
        topics_list = []
        if input_method == "Nhập thủ công danh sách chủ đề":
            # Tạo sẵn ví dụ thực tế chuẩn ký hiệu theo môn học được lựa chọn
            default_val = "Chủ đề: Phương trình bậc hai và hệ thức Vi-ét"
            if subject == "Vật lí": default_val = "Chủ đề: Định luật Ôm - Điện trở của dây dẫn"
            elif subject == "Hóa học": default_val = "Chủ đề: Axit Sunfuric H₂SO₄ và muối Sunfat"
            raw_topics = st.text_area("Nhập các chủ đề kiểm tra:", value=default_val)
            topics_list = [t.strip() for t in raw_topics.split("\n") if t.strip()]
        else:
            uploaded_file = st.file_uploader("Tải tài liệu lên (.docx, .pdf, .txt):", type=["docx", "pdf", "txt"])
            if uploaded_file is not None:
                with st.spinner("Đang phân tích dữ liệu..."):
                    file_bytes = uploaded_file.read()
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    text_content = ""
                    if file_ext == "docx": text_content = extract_text_from_docx(file_bytes)
                    elif file_ext == "pdf": text_content = extract_text_from_pdf(file_bytes)
                    else: text_content = file_bytes.decode("utf-8", errors="ignore")
                        
                    if text_content:
                        topics_list = analyze_topics_with_ai(model, text_content)
                        st.success(f"AI đã tìm thấy {len(topics_list)} chủ đề lý tưởng.")
                        for t in topics_list: st.markdown(f"- **{t}**")

with tab2:
    st.markdown('<div class="section-header">Thiết lập cấu trúc câu hỏi & Số lượng đề</div>', unsafe_allow_html=True)
    col_mat1, col_mat2 = st.columns(2)
    with col_mat1:
        st.subheader("1. Cơ cấu số câu hỏi")
        num_tn = st.number_input("Số câu hỏi Trắc nghiệm khách quan:", min_value=0, max_value=40, value=10, step=1)
        num_tl = st.number_input("Số câu hỏi Tự luận định lượng/định tính:", min_value=0, max_value=10, value=2, step=1)
        num_codes = st.number_input("Số lượng mã đề cần đảo vị trí:", min_value=1, max_value=6, value=2, step=1)
        code_prefix = st.text_input("Mã số đề bắt đầu:", value="201")
            
    with col_mat2:
        st.subheader("2. Tỷ lệ điểm nhận thức (%)")
        nb_ratio = st.slider("Nhận biết (%)", 0, 100, 40)
        th_ratio = st.slider("Thông hiểu (%)", 0, 100, 30)
        vd_ratio = st.slider("Vận dụng (%)", 0, 100, 20)
        vdc_ratio = st.slider("Vận dụng cao (%)", 0, 100, 10)
        
        total_ratio = nb_ratio + th_ratio + vd_ratio + vdc_ratio
        if total_ratio != 100:
            st.error(f"⚠️ Tổng tỷ lệ điểm nhận thức là {total_ratio}%. Vui lòng cấu hình lại cho đúng 100%.")

    st.markdown("---")
    
    if st.button("🔥 TIẾN HÀNH SINH ĐỀ TOÁN - LÝ - HÓA HOÀN CHỈNH"):
        if not subject: st.error("Vui lòng xác định môn học.")
        elif total_ratio != 100: st.error("Tổng tỷ lệ phải bằng 100%.")
        elif not topics_list: st.error("Thiếu chủ đề kiểm tra.")
        else:
            config_package = {
                "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration,
                "semester": semester, "school_year": school_year, "nb_ratio": nb_ratio, "th_ratio": th_ratio,
                "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio, "num_tn": num_tn, "num_tl": num_tl
            }
            
            progress_bar = st.progress(20)
            status_text = st.empty()
            
            try:
                status_text.text("⚙️ AI đang lập luận, căn chỉnh công thức và tạo đề khoa học gốc...")
                result_json = generate_exam_data(model, config_package, topics_list)
                st.session_state.generated_data = result_json
                progress_bar.progress(60)
                
                status_text.text("🔄 Đang triển khai hoán vị đảo đề và đáp án...")
                st.session_state.multi_codes_data = {}
                try: start_code = int(code_prefix)
                except ValueError: start_code = 201
                    
                for i in range(num_codes):
                    current_code = str(start_code + i)
                    st.session_state.multi_codes_data[current_code] = shuffle_exam(result_json, current_code)
                
                st.session_state.matrix_df = pd.DataFrame(result_json.get('ma_tran', []))
                progress_bar.progress(100)
                st.success("🎉 Hệ thống đã sinh bộ đề chuẩn hóa ký hiệu thành công!")
                
            except Exception as e:
                st.error(f"Lỗi phân tách cấu trúc dữ liệu khoa học: {e}")

with tab3:
    if st.session_state.generated_data is None:
        st.info("Hệ thống đang chờ lệnh khởi tạo từ Tab 2.")
    else:
        config_package = {
            "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration,
            "semester": semester, "school_year": school_year
        }
        
        st.markdown('<div class="section-header">Xuất bản tài liệu văn bản</div>', unsafe_allow_html=True)
        available_codes = ["ĐỀ GỐC"] + list(st.session_state.multi_codes_data.keys())
        selected_code_to_download = st.selectbox("Chọn phiên bản đề để xuất file Word (.docx):", available_codes)
        
        if selected_code_to_download == "ĐỀ GỐC":
            target_data = st.session_state.generated_data
            file_label = "De_Goc"
        else:
            target_data = st.session_state.multi_codes_data[selected_code_to_download]
            file_label = f"Ma_De_{selected_code_to_download}"
            
        docx_buffer = export_to_docx(config_package, target_data, code_label=selected_code_to_download)
        st.download_button(
            label=f"📥 TẢI FILE WORD [.DOCX] CỦA MÃ: {selected_code_to_download}",
            data=docx_buffer,
            file_name=f"De_{subject}_Lop{grade}_{file_label}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        st.markdown("---")
        st.markdown('<div class="section-header">Xem trước giao diện hiển thị chuẩn LaTeX trên Web</div>', unsafe_allow_html=True)
        selected_code_preview = st.radio("Mã đề hiển thị:", available_codes, horizontal=True)
        
        preview_data = st.session_state.generated_data if selected_code_preview == "ĐỀ GỐC" else st.session_state.multi_codes_data[selected_code_preview]
        de_preview = preview_data.get('de_kiem_tra', {})
        da_preview = preview_data.get('dap_an_chi_tiet', {})
        
        if de_preview.get('trac_nghiem'):
            st.write("### I. TRẮC NGHIỆM KHÁCH QUAN")
            for q in de_preview['trac_nghiem']:
                st.markdown(f"**{q.get('id')}:** {q.get('cau_hoi')}")
                opts = q.get('options', {})
                st.markdown(f"- **A.** {opts.get('A')} &nbsp;&nbsp;&nbsp;&nbsp; **B.** {opts.get('B')} &nbsp;&nbsp;&nbsp;&nbsp; **C.** {opts.get('C')} &nbsp;&nbsp;&nbsp;&nbsp; **D.** {opts.get('D')}")
                
        if de_preview.get('tu_luan'):
            st.write("### II. TỰ LUẬN")
            for q in de_preview['tu_luan']:
                st.markdown(f"**{q.get('id')} ({q.get('diem')}đ):** {q.get('cau_hoi')}")
