import streamlit as st
import json
import os
import re
import random
import copy
import zipfile
from io import BytesIO
import pandas as pd

# Thư viện xử lý tài liệu Word chuyên sâu
import docx
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

import google.generativeai as genai

# ==========================================
# CẤU HÌNH TRANG & GIAO DIỆN
# ==========================================
st.set_page_config(
    page_title="SmartTest MultiSport - Hệ thống Tạo Đề Đa Môn Toàn Diện",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title { font-size: 2.3rem; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 1.5rem; }
    .section-header { font-size: 1.3rem; font-weight: 600; color: #0F766E; margin-top: 1.5rem; margin-bottom: 1rem; border-left: 5px solid #0F766E; padding-left: 10px; }
    .stButton>button { width: 100%; background-color: #0F766E; color: white; border-radius: 8px; font-weight: 600; padding: 10px; }
    .stButton>button:hover { background-color: #0D9488; color: white; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DANH SÁCH TẤT CẢ CÁC MÔN HỌC & ĐẶC THÙ KÝ HIỆU
# ==========================================
SUBJECTS_CONFIG = {
    "Toán học": "Mọi công thức, phân số, căn thức, hệ phương trình, ma trận phải viết bằng LaTeX bọc trong dấu $...$. Ví dụ: $\\frac{a}{b}$, $\\sqrt{x}$, dập khuôn hệ phương trình.",
    "Vật lý": "Đơn vị đo lường phải chuẩn hóa (Ω, W, J, m/s²). Công thức tính toán bọc trong dấu $...$ như $P = U \\cdot I$, $F = m \\cdot a$.",
    "Hóa học": "BẮT BUỘC dùng chỉ số dưới Unicode thực tế cho công thức phân tử: H₂SO₄, Ca(OH)₂, Al₂(SO₄)₃. Mũi tên phản ứng dạng → hoặc ⇌.",
    "Tin học": "Các đoạn mã giả, code Python, C++, HTML hoặc ký hiệu logic (AND, OR, NOT, ⊕) phải đặt trong dấu `...` hoặc bọc khối rõ ràng.",
    "Công nghệ": "Ký hiệu mạch điện, thông số kỹ thuật điện trở, bản vẽ kỹ thuật hoặc sơ đồ khối phải mô tả tường minh bằng ký hiệu hoa văn chuẩn.",
    "Ngữ văn": "Các ngữ liệu văn học, đoạn thơ, đoạn văn trích dẫn phải được bọc trong dấu ngoặc kép hoặc ghi rõ nguồn. Câu hỏi trắc nghiệm/tự luận tập trung vào đọc hiểu và làm văn.",
    "Tiếng Anh / Ngoại ngữ": "Toàn bộ câu hỏi, phương án lựa chọn và văn bản đọc hiểu phải viết bằng ngôn ngữ đích chuẩn bản xứ, không sai chính tả, có phần trọng âm, ngữ âm rõ ràng.",
    "Lịch sử & Địa lý": "Mốc thời gian, số liệu thống kê tọa độ, ký hiệu bản đồ, số liệu kinh tế - xã hội phải chính xác tuyệt đối theo dòng sự kiện và Atlat.",
    "Giáo dục Kinh tế và Pháp luật": "Các thuật ngữ pháp lý, điều luật, tình huống thực tế phải bọc trong quy chuẩn trích dẫn lập pháp.",
    "Sinh học / KHTN": "Ký hiệu sơ đồ phép lai (P, F₁, F₂), alen ($A_1$, $a$), nhiễm sắc thể (2n, n) hoặc công thức phân tử sinh học phải viết chuẩn xác."
}

# ==========================================
# BỘ CHUYỂN ĐỔI LATEX SANG WORD EQUATION (OMML)
# ==========================================
def convert_latex_to_omml_xml(latex_str):
    """
    Bộ chuyển đổi mở rộng: Xử lý thêm các ký hiệu so sánh, hình học Toán 8
    """
    latex_str = str(latex_str)
    # Tự động dọn dẹp nếu AI sinh thừa chữ 'text ' bên trong công thức
    latex_str = latex_str.replace('text ', '').strip()
    
    # 1. Ký hiệu khác (\neq hoặc \ne) -> ≠
    if '\\neq' in latex_str or '\\ne' in latex_str:
        val = latex_str.replace('\\neq', '').replace('\\ne', '').strip()
        return f'<m:r {nsdecls("m")}><m:t>x ≠ {val}</m:t></m:r>'
        
    # 2. Tam giác (\triangle OAB) -> △OAB
    if '\\triangle' in latex_str:
        val = latex_str.replace('\\triangle', '').strip()
        return f'<m:r {nsdecls("m")}><m:t>Δ{val}</m:t></m:r>'
        
    # 3. Đồng dạng (\sim) -> ∽
    if '\\sim' in latex_str:
        return f'<m:r {nsdecls("m")}><m:t> ∽ </m:t></m:r>'

    # 4. Phân số \frac{a}{b}
    frac_match = re.findall(r'\\frac\{([^}]+)\}\{([^}]+)\}', latex_str)
    if frac_match:
        num, den = frac_match[0]
        return f'<m:f {nsdecls("m")}><m:num><m:r><m:t>{num}</m:t></m:r></m:num><m:den><m:r><m:t>{den}</m:t></m:r></m:den></m:f>'
        
    # 5. Căn thức \sqrt{x}
    sqrt_match = re.findall(r'\\sqrt\{([^}]+)\}', latex_str)
    if sqrt_match:
        inner = sqrt_match[0]
        return f'<m:rad {nsdecls("m")}><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e><m:r><m:t>{inner}</m:t></m:r></m:e></m:rad>'

    # Mặc định
    clean_text = latex_str.replace('\\', '').replace('{', '').replace('}', '')
    return f'<m:r {nsdecls("m")}><m:t>{clean_text}</m:t></m:r>'

def add_math_run_to_paragraph(paragraph, text):
    """
    Quét và tách chuỗi văn bản, đồng thời dọn dẹp các chữ 'text' đứng độc lập ở ngoài dấu $
    """
    if not text: return
    # Xóa bỏ chữ 'text ' đứng lỗi trước đơn vị km, h, phút bên ngoài công thức
    text = re.sub(r'\btext\s+(km/h|km|phút|giờ)\b', r'\1', text)
    
    parts = re.split(r'(\$.*?\$)', text)
    for part in parts:
        if part.startswith('$') and part.endswith('$'):
            latex_content = part[1:-1]
            try:
                omml_xml_str = convert_latex_to_omml_xml(latex_content)
                oMath_elm = parse_xml(f'<m:oMath {nsdecls("m")}>{omml_xml_str}</m:oMath>')
                paragraph._p.append(oMath_elm)
            except Exception:
                paragraph.add_run(latex_content.replace('\\', ''))
        else:
            if part: paragraph.add_run(part)

# ==========================================
# KHỞI TẠO SESSION STATE
# ==========================================
if 'generated_data' not in st.session_state: st.session_state.generated_data = None
if 'multi_codes_data' not in st.session_state: st.session_state.multi_codes_data = {}
if 'alignment_table' not in st.session_state: st.session_state.alignment_table = None

# ==========================================
# THUẬT TOÁN ĐẢO ĐỀ MULTI-CODE & ALIGNMENT
# ==========================================
def generate_shuffled_bundle(original_data, start_code, num_codes):
    bundle = {}
    alignment_records = []
    de_goc = original_data.get('de_kiem_tra', {})
    tn_goc = de_goc.get('trac_nghiem', [])
    
    if not tn_goc: return bundle, None

    for i in range(num_codes):
        current_code = str(start_code + i)
        shuffled_data = copy.deepcopy(original_data)
        tn_current = shuffled_data['de_kiem_tra']['trac_nghiem']
        
        random.seed(int(current_code) + 200)
        indexed_tn = list(enumerate(tn_current))
        random.shuffle(indexed_tn)
        
        new_tn_list = []
        new_dap_an_tn = {}
        
        for new_idx, (old_idx, q) in enumerate(indexed_tn):
            new_id = f"Câu {new_idx + 1}"
            old_id = f"Câu {old_idx + 1}"
            
            q['id'] = new_id
            opts = q.get('options', {})
            old_correct_key = q.get('dap_an')
            old_correct_value = opts.get(old_correct_key)
            
            opt_values = list(opts.values())
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
            new_tn_list.append(q)
            
            alignment_records.append({
                "Mã đề": current_code, "Câu hỏi gốc": old_id, "Vị trí mới": new_id, "Đáp án mới": new_correct_key
            })
            
        shuffled_data['de_kiem_tra']['trac_nghiem'] = new_tn_list
        shuffled_data['dap_an_chi_tiet']['trac_nghiem'] = new_dap_an_tn
        bundle[current_code] = shuffled_data

    df_log = pd.DataFrame(alignment_records)
    pivot_df = df_log.pivot(index='Câu hỏi gốc', columns='Mã đề', values='Vị trí mới')
    pivot_df = pivot_df.reindex(index=sorted(pivot_df.index, key=lambda x: int(re.search(r'\d+', x).group()))).reset_index()
    return bundle, pivot_df

# ==========================================
# TRÍCH XUẤT VÀ KẾT NỐI GEMINI AI ĐA MÔN ĐỘNG
# ==========================================
def init_gemini_client(api_key):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Lỗi API Key: {e}")
        return None

def generate_exam_data(model, config, topics, subject_rule):
    prompt = f"""
    Bạn là chuyên gia khảo thí và đo lường giáo dục. Hãy tạo đề kiểm tra môn {config['subject']} - Khối {config['grade']}.
    Tổng điểm: 10.0 điểm. Số câu TN: {config['num_tn']}, Số câu TL: {config['num_tl']}.
    
    QUY ĐỊNH KÝ HIỆU TOÁN HỌC KHÔNG LỖI:
    - Ký hiệu khác: Viết là $x \\neq 3$, không được ghi chữ 'text'.
    - Ký hiệu tam giác và đồng dạng: Viết là $\\triangle OAB$ và $\\sim$. Bắt buộc bọc trong dấu $.
    - Phân số: $\\frac{{2}}{{5}}$. Đơn vị đo như km/h, phút, giờ viết thường bình thường ngoài dấu $, TUYỆT ĐỐI không chèn chữ 'text' phía trước.

    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN CÓ CHỨA CẢ MA TRẬN VÀ BẢN ĐẶC TẢ CHI TIẾT:
    {{
      "ma_tran": [
        {{"chu_de": "Phân thức đại số", "nb_tn": 1, "nb_tl": 0, "th_tn": 0, "th_tl": 0, "vd_tn": 0, "vd_tl": 0, "vdc_tn": 0, "vdc_tl": 0}}
      ],
      "bang_dac_ta": [
        {{
          "chu_de": "Phân thức đại số",
          "noi_dung": "Phân thức đại số và điều kiện xác định",
          "muc_do": "Nhận biết",
          "yeu_cau_can_dat": "Nhận biết được điều kiện xác định của một phân thức đại số.",
          "so_cau": "1 câu (Câu 1 TN)",
          "diem": 0.25
        }}
      ],
      "de_kiem_tra": {{
        "trac_nghiem": [
          {{"id": "Câu 1", "muc_do": "Nhận biết", "chu_de": "Phân thức đại số", "cau_hoi": "Điều kiện xác định của phân thức $\\frac{{x+1}}{{x-3}}$ là:", "options": {{"A": "$x \\neq 3$", "B": "$x \\neq 0$", "C": "$x \\neq -1$", "D": "$x \\neq 1$"}}, "dap_an": "A"}}
        ],
        "tu_luan": []
      }},
      "dap_an_chi_tiet": {{
        "trac_nghiem": {{"Câu 1": "A"}},
        "tu_luan": []
      }}
    }}
    """
    # (Giữ nguyên đoạn code gọi model và json.loads ở phía dưới...)
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r'^```json\s*', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'```$', '', raw).strip()
    raw = raw.replace('\n', ' ').replace('\t', ' ')
    return json.loads(raw, strict=False)

def build_single_docx(config, data, code_label, include_matrix=True):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.79)
        section.bottom_margin = Inches(0.79)
        section.left_margin = Inches(0.79)
        section.right_margin = Inches(0.79)
        
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(12)
    
    # Tiêu đề
    p_top = doc.add_paragraph()
    p_top.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.add_run("TRƯỜNG THCS & THPT THÔNG MINH\n").bold = True
    run_title = p_top.add_run(f"ĐỀ KIỂM TRA CHÍNH THỨC - MÃ ĐỀ: {code_label}\n")
    run_title.bold = True
    run_title.size = Pt(14)
    p_top.add_run(f"Môn: {config['subject']} | Khối: {config['grade']} | Thời gian: {config['duration']} phút\n")
    p_top.add_run("-------------------------------------\n")
    
    # Ma trận
    if include_matrix and 'ma_tran' in data:
        doc.add_heading("I. MA TRẬN PHÂN BỔ ĐỀ KIỂM TRA", level=2)
        m_table = doc.add_table(rows=1, cols=5)
        m_table.style = 'Table Grid'
        m_hdrs = ['Nội dung kiến thức', 'Nhận biết', 'Thông hiểu', 'Vận dụng', 'Vận dụng cao']
        for idx, h in enumerate(m_hdrs): m_table.rows[0].cells[idx].text = h
        for item in data['ma_tran']:
            row = m_table.add_row().cells
            row[0].text = str(item.get('chu_de', ''))
            row[1].text = f"TN:{item.get('nb_tn',0)}|TL:{item.get('nb_tl',0)}"
            row[2].text = f"TN:{item.get('th_tn',0)}|TL:{item.get('th_tl',0)}"
            row[3].text = f"TN:{item.get('vd_tn',0)}|TL:{item.get('vd_tl',0)}"
            row[4].text = f"TN:{item.get('vdc_tn',0)}|TL:{item.get('vdc_tl',0)}"
        doc.add_paragraph()
# --- BẢN ĐẶC TẢ ĐỀ KIỂM TRA ---
    if include_matrix and 'bang_dac_ta' in data:
        doc.add_heading("II. BẢNG ĐẶC TẢ KỸ THUẬT ĐỀ KIỂM TRA", level=2)
        dt_table = doc.add_table(rows=1, cols=6)
        dt_table.style = 'Table Grid'
        
        hdrs = ['Chủ đề', 'Nội dung kiến thức', 'Mức độ', 'Yêu cầu cần đạt', 'Số câu', 'Điểm']
        for idx, h in enumerate(hdrs): 
            dt_table.rows[0].cells[idx].text = h
            
        for item in data['bang_dac_ta']:
            row = dt_table.add_row().cells
            row[0].text = str(item.get('chu_de', ''))
            row[1].text = str(item.get('noi_dung', ''))
            row[2].text = str(item.get('muc_do', ''))
            row[3].text = str(item.get('yeu_cau_can_dat', ''))
            row[4].text = str(item.get('so_cau', ''))
            row[5].text = f"{item.get('diem', 0)} đ"
        doc.add_paragraph()
        
    # Đề thi
    doc.add_heading("III. NỘI DUNG CÂU HỎI", level=2)
    de = data.get('de_kiem_tra', {})
    
    if de.get('trac_nghiem'):
        doc.add_paragraph().add_run("PHẦN I. TRẮC NGHIỆM KHÁCH QUAN").bold = True
        for q in de['trac_nghiem']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))
            
            opts = q.get('options', {})
            p_o = doc.add_paragraph()
            p_o.paragraph_format.left_indent = Inches(0.3)
            p_o.add_run("A. ")
            add_math_run_to_paragraph(p_o, opts.get('A',''))
            p_o.add_run("   B. ")
            add_math_run_to_paragraph(p_o, opts.get('B',''))
            p_o.add_run("   C. ")
            add_math_run_to_paragraph(p_o, opts.get('C',''))
            p_o.add_run("   D. ")
            add_math_run_to_paragraph(p_o, opts.get('D',''))

    if de.get('tu_luan'):
        doc.add_paragraph().add_run("\nPHẦN II. TỰ LUẬN").bold = True
        for q in de['tu_luan']:
            p_q = doc.add_paragraph()
            p_q.add_run(f"{q.get('id')} ({q.get('diem', 1)} điểm): ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))

    # Đáp án
    doc.add_page_break()
    doc.add_paragraph().add_run(f"HƯỚNG DẪN CHẤM & ĐÁP ÁN - MÃ ĐỀ: {code_label}\n").bold = True
    da = data.get('dap_an_chi_tiet', {})
    if da.get('trac_nghiem'):
        ans_table = doc.add_table(rows=1, cols=2)
        ans_table.style = 'Table Grid'
        ans_table.rows[0].cells[0].text = "Câu hỏi"
        ans_table.rows[0].cells[1].text = "Đáp án"
        for q_id, val in da['trac_nghiem'].items():
            rc = ans_table.add_row().cells
            rc[0].text = str(q_id)
            rc[1].text = str(val)
            
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# GIAO DIỆN ĐIỀU KHIỂN STREAMLIT
# ==========================================
st.markdown('<div class="main-title">Trợ Lý Thiết Kế Đề Thi Đa Môn Chuẩn Ký Hiệu Khoa Học v3.0</div>', unsafe_allow_html=True)

# Kiểm tra khóa API tập trung
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng cấu hình Google Gemini API Key tại Trang chủ trước khi vận hành.")
    st.stop()

model = init_gemini_client(api_key_input)

tab1, tab2, tab3 = st.tabs(["📋 1. Chọn Môn học & Thiết lập số câu", "📊 2. Phân bổ Ma trận kiến thức", "📥 3. Đóng gói & Xuất các Mã đề"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Lựa chọn bộ môn & Thông tin chung</div>', unsafe_allow_html=True)
        # CHO PHÉP CHỌN TẤT CẢ CÁC MÔN HỌC TRONG HỆ THỐNG GIÁO DỤC phổ thông
        subject = st.selectbox("Chọn môn học cần thiết lập đề thi:", list(SUBJECTS_CONFIG.keys()))
        grade = st.selectbox("Khối lớp học:", [str(i) for i in range(1, 13)], index=7)
        exam_type = st.selectbox("Hình thức kiểm tra:", ["Giữa học kỳ", "Cuối học kỳ", "Khảo sát chất lượng định kỳ"])
        duration = st.number_input("Thời lượng làm bài (phút):", min_value=15, max_value=150, value=60, step=5)
        school_year = st.text_input("Năm học:", value="2026-2027")

    with col2:
        st.markdown('<div class="section-header">Cấu hình số lượng câu hỏi tùy ý</div>', unsafe_allow_html=True)
        tn_choice = st.selectbox("Số câu Trắc nghiệm khách quan:", [10, 15, 20, 25, 30, "Nhập số lượng tùy chọn khác"], index=2)
        num_tn = st.number_input("Số câu trắc nghiệm thực tế:", min_value=0, max_value=60, value=12) if tn_choice == "Nhập số lượng tùy chọn khác" else int(tn_choice)
        
        tl_choice = st.selectbox("Số câu hỏi Tự luận định lượng:", [1, 2, 3, 4, "Nhập số lượng tùy chọn khác"], index=1)
        num_tl = st.number_input("Số câu tự luận thực tế:", min_value=0, max_value=15, value=2) if tl_choice == "Nhập số lượng tùy chọn khác" else int(tl_choice)
        
        st.markdown('---')
        code_choice = st.selectbox("Số lượng mã đề đảo tự động:", [1, 2, 4, 6, 8, "Nhập số lượng bất kỳ"], index=2)
        num_codes = st.number_input("Số mã đề đảo thực tế:", min_value=1, max_value=24, value=3) if code_choice == "Nhập số lượng bất kỳ" else int(code_choice)
        code_prefix = st.text_input("Ký hiệu mã đề bắt đầu:", value="101")

with tab2:
    st.markdown('<div class="section-header">Ma trận nhận thức & Nội dung kiến thức cốt lõi</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: nb_ratio = st.slider("Nhận biết (%)", 0, 100, 40)
    with c2: th_ratio = st.slider("Thông hiểu (%)", 0, 100, 30)
    with c3: vd_ratio = st.slider("Vận dụng (%)", 0, 100, 20)
    with c4: vdc_ratio = st.slider("Vận dụng cao (%)", 0, 100, 10)
    
    total_ratio = nb_ratio + th_ratio + vd_ratio + vdc_ratio
    if total_ratio != 100:
        st.warning(f"⚠️ Tổng tỷ lệ hiện tại đạt {total_ratio}%. Thầy cô vui lòng căn chỉnh về chính xác 100%.")
        
    topics_list = st.text_area("Nhập các chủ đề/nội dung kiến thức cần quét (Mỗi nội dung một dòng):", 
                               value="Nội dung 1: Kiến thức trọng tâm chương học cũ\nNội dung 2: Kiến thức nâng cao bổ trợ")

    st.markdown("---")
    if st.button("🚀 BẮT ĐẦU GENERATE ĐỀ THI ĐA MÔN ĐÚNG KÝ HIỆU CHUẨN"):
        if total_ratio != 100:
            st.error("Tổng tỷ lệ phần trăm phân bổ điểm phải bằng 100%.")
        else:
            config_pkg = {
                "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration, "school_year": school_year,
                "num_tn": num_tn, "num_tl": num_tl, "nb_ratio": nb_ratio, "th_ratio": th_ratio, "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio
            }
            with st.spinner(f"Hệ thống đang nạp quy tắc đặc thù môn {subject} để tạo cấu trúc đề thi gốc..."):
                try:
                    # Gọi AI sinh dữ liệu dựa theo luật của môn học được chọn
                    rule = SUBJECTS_CONFIG[subject]
                    res_json = generate_exam_data(model, config_pkg, [t.strip() for t in topics_list.split('\n') if t.strip()], rule)
                    st.session_state.generated_data = res_json
                    
                    try: s_code = int(code_prefix)
                    except ValueError: s_code = 101
                    
                    # Tiến hành đảo đề tự động
                    bundle, alignment_df = generate_shuffled_bundle(res_json, s_code, num_codes)
                    st.session_state.multi_codes_data = bundle
                    st.session_state.alignment_table = alignment_df
                    
                    st.success(f"🎉 Xuất bản thành công đề thi môn {subject} gốc kèm {num_codes} mã đề đảo!")
                except Exception as e:
                    st.error(f"Lỗi phân tách cấu trúc khoa học bộ môn: {e}")

with tab3:
    if st.session_state.generated_data is None:
        st.info("Hệ thống đang ở trạng thái chờ nạp dữ liệu từ Tab 2.")
    else:
        config_pkg = { "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration, "school_year": school_year }
        inc_mat = st.checkbox("Chèn bảng Ma trận phân bổ vào đầu file Word", value=True)
        
        export_mode = st.radio("Đóng gói đầu ra tài liệu (.docx):", 
                               ["Tải file đơn lẻ của từng mã đề", "Nén tất cả mã đề vào file ZIP", "Gộp chung tất cả mã đề vào 1 file Word duy nhất"])
        
        if export_mode == "Tải file đơn lẻ của từng mã đề":
            sel_code = st.selectbox("Chọn Mã đề cần xuất bản:", list(st.session_state.multi_codes_data.keys()))
            docx_buf = build_single_docx(config_pkg, st.session_state.multi_codes_data[sel_code], sel_code, include_matrix=inc_mat)
            st.download_button(label=f"📥 TẢI FILE WORD MÃ ĐỀ [{sel_code}]", data=docx_buf, file_name=f"De_{subject}_MaDe_{sel_code}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        elif export_mode == "Nén tất cả mã đề vào file ZIP":
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for c_code, c_data in st.session_state.multi_codes_data.items():
                    d_buf = build_single_docx(config_pkg, c_data, c_code, include_matrix=inc_mat)
                    zip_file.writestr(f"De_{subject}_Lop{grade}_MaDe_{c_code}.docx", d_buf.getvalue())
            zip_buffer.seek(0)
            st.download_button(label="📥 TẢI FILE NÉN ZIP TRỌN BỘ MÃ ĐỀ", data=zip_buffer, file_name=f"Bo_De_{subject}_TronGoi.zip", mime="application/zip")
            
        else:
            main_doc = Document()
            for idx, (c_code, c_data) in enumerate(st.session_state.multi_codes_data.items()):
                temp_buf = build_single_docx(config_pkg, c_data, c_code, include_matrix=inc_mat)
                t_doc = Document(temp_buf)
                for element in t_doc.element.body: main_doc.element.body.append(element)
                if idx < len(st.session_state.multi_codes_data) - 1: main_doc.add_page_break()
            all_buf = BytesIO()
            main_doc.save(all_buf)
            all_buf.seek(0)
            st.download_button(label="📥 TẢI FILE GỘP TOÀN BỘ MÃ ĐỀ (.DOCX)", data=all_buf, file_name=f"Gop_Bo_De_{subject}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        if st.session_state.alignment_table is not None:
            st.markdown("---")
            st.markdown("### 📊 Bảng đối chiếu mã đề nội bộ tra cứu nhanh")
            st.dataframe(st.session_state.alignment_table, use_container_width=True)
