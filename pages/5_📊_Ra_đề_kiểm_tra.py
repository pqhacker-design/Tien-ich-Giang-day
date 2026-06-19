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

st.markdown("""
<style>
    .main-title { font-size: 2.4rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 2rem; }
    .section-header { font-size: 1.4rem; font-weight: 600; color: #0F766E; margin-top: 1.5rem; margin-bottom: 1rem; border-left: 5px solid #0F766E; padding-left: 10px; }
    .stButton>button { width: 100%; background-color: #0F766E; color: white; border-radius: 8px; font-weight: 600; }
    .stButton>button:hover { background-color: #0D9488; color: white; }
    .history-card { padding: 10px; border-radius: 5px; border: 1px solid #E5E7EB; margin-bottom: 10px; }
    .code-box { background-color: #F3F4F6; padding: 10px; border-radius: 5px; font-family: monospace; }
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
    st.session_state.multi_codes_data = {}  # Lưu trữ danh sách các mã đề sau khi đảo

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
    """
    Hàm nhận vào đề gốc và tiến hành xáo trộn thứ tự câu hỏi trắc nghiệm,
    đồng thời xáo trộn thứ tự các phương án A, B, C, D của từng câu hỏi.
    """
    # Sao chép sâu (deep copy) để tránh ghi đè lên dữ liệu đề gốc
    shuffled_data = copy.deepcopy(original_data)
    
    de_goc = shuffled_data.get('de_kiem_tra', {})
    tn_questions = de_goc.get('trac_nghiem', [])
    
    if not tn_questions:
        return shuffled_data
        
    # 1. Đảo thứ tự toàn bộ danh sách các câu hỏi trắc nghiệm
    random.seed(int(code_number) + 42) # Khóa seed cố định theo mã đề để kết quả nhất quán
    random.shuffle(tn_questions)
    
    new_dap_an_tn = {}
    
    # 2. Đảo các phương án lựa chọn trong từng câu hỏi
    for idx, q in enumerate(tn_questions):
        old_id = q['id']  # Ví dụ: "Câu 1"
        new_id = f"Câu {idx + 1}"
        q['id'] = new_id  # Đánh lại số thứ tự câu sau khi đảo
        
        opts = q.get('options', {})
        old_correct_key = q.get('dap_an') # Ví dụ: "A"
        old_correct_value = opts.get(old_correct_key)
        
        # Chuyển dictionary key-value thành danh sách các cặp giá trị để xáo trộn
        opt_items = list(opts.items()) # [('A', 'nd1'), ('B', 'nd2')...]
        opt_values = [item[1] for item in opt_items]
        
        random.shuffle(opt_values) # Đảo ngẫu nhiên nội dung các phương án
        
        # Tạo lại dictionary phương án mới tương ứng với A, B, C, D
        new_opts = {}
        new_correct_key = "A"
        for o_idx, char in enumerate(['A', 'B', 'C', 'D']):
            new_opts[char] = opt_values[o_idx]
            if opt_values[o_idx] == old_correct_value:
                new_correct_key = char
                
        # Cập nhật lại nội dung câu hỏi
        q['options'] = new_opts
        q['dap_an'] = new_correct_key
        
        # Cập nhật vào từ điển đáp án chi tiết mới cho mã đề này
        new_dap_an_tn[new_id] = new_correct_key

    # Gán phần trắc nghiệm đã đảo và bảng đáp án mới vào cấu trúc dữ liệu
    shuffled_data['de_kiem_tra']['trac_nghiem'] = tn_questions
    shuffled_data['dap_an_chi_tiet']['trac_nghiem'] = new_dap_an_tn
    
    return shuffled_data

# ==========================================
# KẾT NỐI VÀ XỬ LÝ GEMINI AI
# ==========================================
def init_gemini_client(api_key):
    try:
        genai.configure(api_key=api_key)
        # Sử dụng gemini-2.5-flash để tối ưu hạn mức Free Tier và tốc độ xử lý nhanh
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Lỗi cấu hình Gemini Client: {e}")
        return None

def analyze_topics_with_ai(model, text_content):
    prompt = f"""
    Bạn là chuyên gia thẩm định chương trình GDPT 2018. Hãy đọc văn bản nội dung kiến thức sau và trích xuất ra các Chủ đề/Chương cốt lõi.
    Chỉ trả về danh sách tên các chủ đề, cách nhau bằng dấu gạch đầu dòng (-), không kèm theo lời giải thích nào khác.
    
    Nội dung tài liệu:
    {text_content[:3000]}
    """
    try:
        response = model.generate_content(prompt)
        topics = [line.strip("- ").strip() for line in response.text.split("\n") if line.strip()]
        return topics
    except Exception as e:
        st.error(f"Lỗi phân tích tài liệu bằng AI: {e}")
        return []

def generate_exam_data(model, config, topics):
    prompt = f"""
    Bạn là chuyên gia xây dựng đề kiểm tra và đo lường giáo dục theo chuẩn Chương trình GDPT 2018 của Bộ Giáo dục và Đào tạo Việt Nam.
    Hãy tạo một bộ dữ liệu kiểm tra hoàn chỉnh bao gồm: Ma trận, Bảng đặc tả, Đề kiểm tra và Đáp án/Hướng dẫn chấm chi tiết dựa trên các thông tin sau:
    
    THÔNG TIN CHUNG:
    - Môn học: {config['subject']} | Lớp: {config['grade']}
    - Loại đề: {config['exam_type']} | Thời lượng: {config['duration']} phút
    - Học kỳ: {config['semester']} | Năm học: {config['school_year']}
    - Danh sách các chủ đề cốt lõi: {", ".join(topics)}
    
    CẤU TRÚC SỐ LƯỢNG CÂU HỎI & TỶ LỆ ĐIỂM:
    - BẮT BUỘC sinh đúng số lượng: {config['num_tn']} câu trắc nghiệm (TN) và {config['num_tl']} câu tự luận (TL).
    - Hình thức: Trắc nghiệm ({config['tn_ratio']}%) và Tự luận ({config['tl_ratio']}%) trên tổng số điểm là 10.
    - Tỷ lệ nhận thức: Nhận biết ({config['nb_ratio']}%), Thông hiểu ({config['th_ratio']}%), Vận dụng ({config['vd_ratio']}%), Vận dụng cao ({config['vdc_ratio']}%)
    
    YÊU CẦU ĐỀ KIỂM TRA:
    1. Ngôn ngữ chính xác, khoa học, bám sát ma trận tư duy, phù hợp với tâm sinh lý lứa tuổi học sinh lớp {config['grade']}.
    2. Các câu trắc nghiệm khách quan (TN) phải có 4 lựa chọn (A, B, C, D), phương án nhiễu phải có độ nhiễu hợp lý, không trùng lặp, chỉ có DUY NHẤT 1 đáp án đúng.
    3. Các câu tự luận (TL) phải đi kèm hướng dẫn chấm và thang điểm chi tiết từng bước.
    4. Hãy thực hiện quy trình tự kiểm tra (Self-Correction): Rà soát trùng lặp, kiểm tra logic đáp án trước khi xuất kết quả.

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
        ]
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
def export_to_docx(config, data, code_label="ĐỀ GỐC"):
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
    sub_title.add_run(f"Học kỳ: {config['semester']} | Năm học: {config['school_year']}\nMÃ ĐỀ: {code_label}\n")
    sub_title.add_run(f"Thời gian làm bài: {config['duration']} phút (Không kể thời gian giao đề)\n")
    
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
    doc.add_heading(f"III. ĐỀ KIỂM TRA CHÍNH THỨC - MÃ ĐỀ: {code_label}", level=1)
    de = data.get('de_kiem_tra', {})
    
    if de.get('trac_nghiem'):
        p_tn_head = doc.add_paragraph()
        r_tn_head = p_tn_head.add_run("PHẦN I. TRẮC NGHIỆM KHÁCH QUAN")
        r_tn_head.bold = True
        
        for q in de['trac_nghiem']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')}: ").bold = True
            p_q.add_run(q.get('cau_hoi'))
            
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
    doc.add_heading(f"IV. ĐÁP ÁN VÀ HƯỚNG DẪN CHẤM - MÃ ĐỀ: {code_label}", level=1)
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

model = init_gemini_client(api_key_input)

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
        st.info("Chưa có đề nào được tạo.")

tab1, tab2, tab3 = st.tabs(["📋 1. Thiết lập cấu hình đề", "📊 2. Quản lý Ma trận & Đặc tả", "✨ 3. Xem trước & Xuất đề"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-header">Thông tin tổng quan</div>', unsafe_allow_html=True)
        subject = st.text_input("Môn học:", value="Toán học")
        grade = st.selectbox("Khối lớp học:", [str(i) for i in range(1, 13)], index=7)
        exam_type = st.selectbox("Loại hình đề kiểm tra:", ["15 phút", "45 phút (1 tiết)", "Giữa học kỳ", "Cuối học kỳ"], index=2)
        duration = st.number_input("Thời lượng làm bài (phút):", min_value=15, max_value=180, value=90, step=5)
        semester = st.selectbox("Học kỳ:", ["Học kỳ I", "Học kỳ II"])
        school_year = st.text_input("Năm học:", value="2026-2027")

    with col2:
        st.markdown('<div class="section-header">Nội dung kiến thức & Chủ đề</div>', unsafe_allow_html=True)
        input_method = st.radio("Phương thức xác định chủ đề:", ["Nhập thủ công danh sách chủ đề", "Tải tệp tài liệu giảng dạy lên (AI tự phân tích)"])
        
        topics_list = []
        if input_method == "Nhập thủ công danh sách chủ đề":
            raw_topics = st.text_area("Nhập các chủ đề (Mỗi chủ đề một dòng):", 
                                      value="Chủ đề 1: Hàm số và Đồ thị\nChủ đề 2: Phương trình bậc hai")
            topics_list = [t.strip() for t in raw_topics.split("\n") if t.strip()]
        else:
            uploaded_file = st.file_uploader("Tải tài liệu lên (.docx, .pdf, .txt):", type=["docx", "pdf", "txt"])
            if uploaded_file is not None:
                with st.spinner("Đang trích xuất..."):
                    file_bytes = uploaded_file.read()
                    file_ext = uploaded_file.name.split(".")[-1].lower()
                    text_content = ""
                    if file_ext == "docx": text_content = extract_text_from_docx(file_bytes)
                    elif file_ext == "pdf": text_content = extract_text_from_pdf(file_bytes)
                    else: text_content = file_bytes.decode("utf-8", errors="ignore")
                        
                    if text_content:
                        topics_list = analyze_topics_with_ai(model, text_content)
                        st.success(f"AI đã tìm thấy {len(topics_list)} chủ đề.")
                        for t in topics_list: st.markdown(f"- **{t}**")

with tab2:
    st.markdown('<div class="section-header">Thiết lập cấu trúc câu hỏi & Ma trận số đề</div>', unsafe_allow_html=True)
    
    col_mat1, col_mat2 = st.columns(2)
    with col_mat1:
        st.subheader("1. Số lượng câu hỏi thành phần")
        num_tn = st.number_input("Số câu hỏi Trắc nghiệm cần tạo:", min_value=0, max_value=50, value=12, step=1)
        num_tl = st.number_input("Số câu hỏi Tự luận cần tạo:", min_value=0, max_value=10, value=3, step=1)
        
        st.subheader("2. Tùy chọn trộn đề & Phân tách mã đề")
        num_codes = st.number_input("Số lượng mã đề cần đảo (Hoán vị câu hỏi/đáp án):", min_value=1, max_value=10, value=4, step=1)
        code_prefix = st.text_input("Ký hiệu mã đề (Ví dụ nhập 101 thì hệ thống sinh 101, 102, 103...):", value="101")
            
    with col_mat2:
        st.subheader("3. Tỷ lệ mức độ nhận thức (%)")
        nb_ratio = st.slider("Nhận biết (%)", 0, 100, 30)
        th_ratio = st.slider("Thông hiểu (%)", 0, 100, 30)
        vd_ratio = st.slider("Vận dụng (%)", 0, 100, 25)
        vdc_ratio = st.slider("Vận dụng cao (%)", 0, 100, 15)
        
        total_ratio = nb_ratio + th_ratio + vd_ratio + vdc_ratio
        if total_ratio != 100:
            st.error(f"⚠️ Tổng tỷ lệ điểm nhận thức là {total_ratio}%. Vui lòng điều chỉnh về đúng 100%.")

    st.markdown("---")
    
    if st.button("🔥 BẮT ĐẦU KHỞI TẠO ĐỀ GỐC & TỰ ĐỘNG ĐẢO MÃ ĐỀ"):
        if not subject: st.error("Vui lòng điền thông tin Môn học.")
        elif total_ratio != 100: st.error("Tổng tỷ lệ nhận thức phải bằng 100%.")
        elif not topics_list: st.error("Danh sách chủ đề rỗng.")
        else:
            # Tự động tính toán tỷ lệ phân chia TN/TL để gửi lên Prompt AI
            tn_ratio = 70 if num_tn > 0 else 0
            tl_ratio = 30 if num_tl > 0 else 100
            
            config_package = {
                "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration,
                "semester": semester, "school_year": school_year, "nb_ratio": nb_ratio, "th_ratio": th_ratio,
                "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio, "tn_ratio": tn_ratio, "tl_ratio": tl_ratio,
                "num_tn": num_tn, "num_tl": num_tl
            }
            
            progress_bar = st.progress(10)
            status_text = st.empty()
            
            try:
                status_text.text("⚡ Bước 1: AI đang thiết kế đề gốc bám sát số câu hỏi yêu cầu...")
                progress_bar.progress(40)
                
                # Gọi AI sinh đề gốc
                result_json = generate_exam_data(model, config_package, topics_list)
                st.session_state.generated_data = result_json
                
                progress_bar.progress(70)
                status_text.text(f"⚡ Bước 2: Khởi chạy thuật toán hoán vị nội bộ để tạo {num_codes} mã đề...")
                
                # Tiến hành đảo đề tự động dựa theo số lượng mã đề giáo viên nhập
                st.session_state.multi_codes_data = {}
                try:
                    start_code = int(code_prefix)
                except ValueError:
                    start_code = 101
                    
                for i in range(num_codes):
                    current_code = str(start_code + i)
                    # Thực hiện đảo câu hỏi/phương án từ đề gốc
                    st.session_state.multi_codes_data[current_code] = shuffle_exam(result_json, current_code)
                
                st.session_state.matrix_df = pd.DataFrame(result_json.get('ma_tran', []))
                st.session_state.spec_df = pd.DataFrame(result_json.get('bang_dac_ta', []))
                
                progress_bar.progress(100)
                status_text.text(f"🎉 Đã sinh thành công đề gốc và {num_codes} mã đề đảo liên quan!")
                
                st.session_state.history.append({
                    "subject": subject, "grade": grade, "exam_type": exam_type, "time": pd.Timestamp.now().strftime("%H:%M:%S")
                })
                
            except Exception as e:
                st.error(f"Lỗi hệ thống AI hoặc cấu trúc dữ liệu: {e}")

    if st.session_state.matrix_df is not None:
        st.subheader("📊 Ma trận phân bổ của Đề gốc")
        st.dataframe(st.session_state.matrix_df, use_container_width=True)

with tab3:
    if st.session_state.generated_data is None:
        st.info("Chưa có dữ liệu đề. Vui lòng thiết lập cấu hình và nhấn nút Khởi tạo đề ở Tab 2.")
    else:
        config_package = {
            "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration,
            "semester": semester, "school_year": school_year
        }
        
        st.markdown('<div class="section-header">Tải xuống các phiên bản mã đề</div>', unsafe_allow_html=True)
        
        # Tạo danh sách các mã đề để giáo viên lựa chọn xuất file
        available_codes = ["ĐỀ GỐC"] + list(st.session_state.multi_codes_data.keys())
        
        selected_code_to_download = st.selectbox("Chọn Mã đề cụ thể muốn tải về máy (.docx):", available_codes)
        
        if selected_code_to_download == "ĐỀ GỐC":
            target_data = st.session_state.generated_data
            file_label = "De_Goc"
        else:
            target_data = st.session_state.multi_codes_data[selected_code_to_download]
            file_label = f"Ma_De_{selected_code_to_download}"
            
        docx_buffer = export_to_docx(config_package, target_data, code_label=selected_code_to_download)
        
        st.download_button(
            label=f"📥 TẢI FILE WORD CỦA [{selected_code_to_download.upper()}] (.DOCX)",
            data=docx_buffer,
            file_name=f"De_{subject}_Lop{grade}_{file_label}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        st.markdown("---")
        st.markdown('<div class="section-header">Bản xem trước dữ liệu hiển thị</div>', unsafe_allow_html=True)
        
        # Đồng bộ bộ lọc xem trước trên giao diện Web
        selected_code_preview = st.radio("Chọn mã đề để hiển thị xem trước trực quan dưới đây:", available_codes, horizontal=True)
        
        if selected_code_preview == "ĐỀ GỐC":
            preview_data = st.session_state.generated_data
        else:
            preview_data = st.session_state.multi_codes_data[selected_code_preview]
            
        de_preview = preview_data.get('de_kiem_tra', {})
        da_preview = preview_data.get('dap_an_chi_tiet', {})
        
        col_view1, col_view2 = st.columns(2)
        
        with col_view1:
            st.subheader("✏️ Nội dung Đề kiểm tra")
            if de_preview.get('trac_nghiem'):
                st.markdown("**I. TRẮC NGHIỆM KHÁCH QUAN**")
                for q in de_preview['trac_nghiem']:
                    st.markdown(f"**{q.get('id')}:** {q.get('cau_hoi')}")
                    opts = q.get('options', {})
                    st.markdown(f"- A. {opts.get('A')} | B. {opts.get('B')} | C. {opts.get('C')} | D. {opts.get('D')}")
            
            if de_preview.get('tu_luan'):
                st.markdown("**II. TỰ LUẬN**")
                for q in de_preview['tu_luan']:
                    st.markdown(f"**{q.get('id')} ({q.get('diem')}đ):** {q.get('cau_hoi')}")
                    
        with col_view2:
            st.subheader("🔑 Đáp án & Hướng dẫn chấm")
            if da_preview.get('trac_nghiem'):
                st.markdown("**1. Đáp án Trắc nghiệm nhanh:**")
                st.dataframe(pd.DataFrame(list(da_preview['trac_nghiem'].items()), columns=['Câu hỏi', 'Đáp án đúng']), use_container_width=True)
                
            if da_preview.get('tu_luan'):
                st.markdown("**2. Hướng dẫn chấm Tự luận:**")
                for tl_ans in da_preview['tu_luan']:
                    st.markdown(f"**{tl_ans.get('id')}:**")
                    st.caption(f"Yêu cầu: {tl_ans.get('huong_dan')}")
                    for buoc, diem_buoc in tl_ans.get('thang_diem', {}).items():
                        st.markdown(f"- {buoc}: `{diem_buoc} điểm`")
