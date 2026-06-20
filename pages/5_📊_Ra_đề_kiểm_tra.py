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
import latex2mathml.commands
from latex2mathml.converter import convert as convert_latex_to_mathml

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
    Bộ dịch Regex thực chiến v5.0: Chấp nhận và xử lý cả mã toán học BỊ MẤT DẤU GẠCH CHÉO (frac, neq, triangle, sim)
    """
    # Làm sạch khoảng trắng rác và đồng bộ hóa chữ thường để dễ lọc
    latex_str = str(latex_str).replace('text ', '').replace('\\\\', '\\').strip()
    
    # 1. Xử lý Phân số (Bắt cả \frac{a}{b} và frac{a}{b})
    frac_match = re.findall(r'\\?frac\{([^}]+)\}\{([^}]+)\}', latex_str)
    if frac_match:
        num, den = frac_match[0]
        return f'<m:f {nsdecls("m")}><m:num><m:r><m:t>{num}</m:t></m:r></m:num><m:den><m:r><m:t>{den}</m:t></m:r></m:den></m:f>'

    # 2. Xử lý dấu Khác (Bắt cả \neq, neq, \ne, ne, x neq 3)
    if 'ne' in latex_str or 'neq' in latex_str or '≠' in latex_str:
        # Lấy phần ký tự xung quanh nếu có (ví dụ: x neq 3 -> lấy x và 3)
        parts = re.split(r'\\?neq|\\?ne|≠', latex_str)
        left = parts[0].strip() if len(parts) > 0 else ""
        right = parts[1].strip() if len(parts) > 1 else ""
        return f'<m:r {nsdecls("m")}><m:t>{left} ≠ {right}</m:t></m:r>'

    # 3. Xử lý Đồng dạng & Tam giác (Bắt cả \triangle, triangle, \sim, sim)
    if 'sim' in latex_str or 'triangle' in latex_str or 'Δ' in latex_str:
        # Thay thế các chữ rác thành ký hiệu Unicode đẹp trong Word
        val = latex_str.replace('\\triangle', '').replace('triangle', '').replace('Δ', '')
        val = val.replace('\\sim', ' ∽ ').replace('sim', ' ∽ ')
        return f'<m:r {nsdecls("m")}><m:t>Δ{val.strip()}</m:t></m:r>'

    # 4. Xử lý số mũ đa năng (x^2, cm^2, x^2+9)
    bracket_pow = re.findall(r'([a-zA-Z0-9]+)\^\{([^}]+)\}', latex_str)
    if bracket_pow:
        base, exp = bracket_pow[0]
        return f'<m:sSup {nsdecls("m")}><m:e><m:r><m:t>{base}</m:t></m:r></m:e><m:sup><m:r><m:t>{exp}</m:t></m:r></m:sup></m:sSup>'
    
    simple_pow = re.findall(r'([a-zA-Z0-9]+)\^([a-zA-Z0-9+-]+)', latex_str)
    if simple_pow:
        base, exp = simple_pow[0]
        return f'<m:sSup {nsdecls("m")}><m:e><m:r><m:t>{base}</m:t></m:r></m:e><m:sup><m:r><m:t>{exp}</m:t></m:r></m:sup></m:sSup>'

    # Nếu là văn bản bình thường, trả về text sạch không chứa dấu gạch chéo rác
    clean_text = latex_str.replace('\\', '')
    return f'<m:r {nsdecls("m")}><m:t>{clean_text}</m:t></m:r>'


def add_math_run_to_paragraph(paragraph, text):
    """
    Quét và ép xử lý tất cả các vùng chứa công thức toán học kể cả khi AI quên bọc dấu $
    """
    if not text: return
    
    # 1. Triệt tiêu chữ 'text ' rác đứng cạnh đơn vị đo lường
    text = re.sub(r'\btext\s+(km/h|km|phút|giờ|cm\^2|cm|s|kg|m)\b', r'\1', text)
    text = text.replace('\\n', '\n').replace('\r', '')
    
    # 2. TỰ ĐỘNG BỌC GIẢ LẬP: Nếu AI quên bọc $, nhưng chuỗi chứa cấu trúc toán học (frac, neq, ^) thì tự bọc lại
    if '$' not in text:
        # Nếu dòng chứa chữ frac{...}{...} hoặc neq hoặc số mũ, bọc toàn bộ phân đoạn đó
        text = re.sub(r'(\bfrac\{[^}]+\}\{[^}]+\})', r'$\1$', text)
        text = re.sub(r'([a-zA-Z0-9]+\s+neq\s+[a-zA-Z0-9\-]+)', r'$\1$', text)
        text = re.sub(r'([a-zA-Z0-9]+\^[a-zA-Z0-9+\-]+)', r'$\1$', text)
        text = re.sub(r'(triangle\s+[A-Z]+\s+sim\s+triangle\s+[A-Z]+)', r'$\1$', text)

    # 3. Tiến hành phân tách bằng dấu $ và ghi vào Word
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if index > 0:
            new_run = paragraph.add_run()
            new_run.add_break()
            
        parts = re.split(r'(\$.*?\$)', line)
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
                if part: 
                    paragraph.add_run(part)
# ==========================================
# KHỞI TẠO SESSION STATE
# ==========================================
if 'generated_data' not in st.session_state: st.session_state.generated_data = None
if 'step1_data' not in st.session_state: st.session_state.step1_data = None
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
def generate_step1_matrix(model, config, topics):
    """
    LƯỢT 1: Chỉ sinh Ma trận và Bản đặc tả kỹ thuật
    """
    prompt = f"""
    Bạn là chuyên gia khảo thí. Hãy lập Ma trận và Bản đặc tả đề kiểm tra môn {config['subject']} - Khối Lớp {config['grade']}.
    Số câu TN: {config['num_tn']}, Số câu TL: {config['num_tl']}. 
    Tỷ lệ nhận thức: Nhận biết {config['nb_ratio']}%, Thông hiểu {config['th_ratio']}%, Vận dụng {config['vd_ratio']}%, Vận dụng cao {config['vdc_ratio']}%.
    
    Chủ đề cần quét: {", ".join(topics)}

    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN CÓ CẤU TRÚC:
    {{
      "ma_tran": [
        {{"chu_de": "Tên chủ đề", "nb_tn": 1, "nb_tl": 0, "th_tn": 1, "th_tl": 0, "vd_tn": 0, "vd_tl": 1, "vdc_tn": 0, "vdc_tl": 0}}
      ],
      "bang_dac_ta": [
        {{"id_dac_ta": "DT_01", "chu_de": "Tên chủ đề", "noi_dung": "Kiến thức", "muc_do": "Nhận biết", "yeu_cau_can_dat": "Mô tả...", "so_cau": "1 câu TN", "diem": 0.25}}
      ]
    }}
    """
    response = model.generate_content(prompt)
    raw = response.text.strip().replace('\n', ' ').replace('\t', ' ')
    raw = re.sub(r'^```json\s*|```$', '', raw, flags=re.IGNORECASE).strip()
    return json.loads(raw, strict=False)


def generate_step2_questions(model, config, matrix_data, subject_rule):
    """
    LƯỢT 2: Nạp Bản đặc tả từ Lượt 1 để sinh Đề thi và Đáp án chi tiết
    """
    # Chuyển bảng đặc tả thành chuỗi văn bản để làm tiền đề cho AI viết câu hỏi
    dac_ta_str = json.dumps(matrix_data.get('bang_dac_ta', []), ensure_ascii=False)
    
    prompt = f"""
    Bạn là chuyên gia soạn đề thi. Dựa trên Bản đặc tả kỹ thuật sau đây, hãy viết nội dung câu hỏi chi tiết và đáp án tương ứng.
    Bản đặc tả: {dac_ta_str}
    
    Thông số đề thi: Môn {config['subject']}, Khối {config['grade']}. Tổng điểm: 10.0. 
    Mỗi câu trắc nghiệm trị giá {10 * 0.7 / max(1, config['num_tn']):.2f} điểm. Tổng điểm tự luận là {10 * 0.3:.1f} điểm.

    QUY ĐỊNH KÝ HIỆU CHUYÊN BIỆT (BẮT BUỘC):
    - Tuyệt đối KHÔNG sử dụng chữ 'text' trong công thức và đơn vị. Đơn vị diện tích viết là $cm^2$, không viết trơn.
    - Ký hiệu đồng dạng viết là $\\sim$ (Phải có 2 dấu gạch chéo ngược để chống nuốt ký tự trong JSON).
    - Ký hiệu tam giác viết là $\\triangle ABC$.
    - Mọi đa thức, số mũ, phân số bắt buộc phải nằm gọn trong cặp dấu $...$. Ví dụ: $P = 5x^2y - 3xy^2$.
    "Vật lý": "Mọi góc số độ PHẢI viết dạng $30 \\circ$, tên gương hoặc ký hiệu nguồn có chỉ số dưới PHẢI viết dạng $G_1$, $G_2$. Đơn vị đo lường thông thường (km/h, kg, m, s) viết thường, TUYỆT ĐỐI không chèn chữ 'text' phía trước. Để xuống dòng các câu ý a, b, c, hãy sử dụng dấu xuống dòng thực tế, không dùng ký tự thoát chuỗi lỗi.",
    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN CÓ CẤU TRÚC (Tuyệt đối không lặp lại phần ma_tran):
    {{
      "de_kiem_tra": {{
        "trac_nghiem": [
          {{"id": "Câu 1", "muc_do": "...", "chu_de": "...", "cau_hoi": "Nội dung câu hỏi chứa ký hiệu khoa học chuẩn...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "dap_an": "A"}}
        ],
        "tu_luan": [
          {{"id": "Câu 1 (TL)", "muc_do": "...", "chu_de": "...", "cau_hoi": "Nội dung bài tự luận...", "diem": 1.5}}
        ]
      }},
      "dap_an_chi_tiet": {{
        "trac_nghiem": {{"Câu 1": "A"}},
        "tu_luan": [
          {{"id": "Câu 1 (TL)", "huong_dan": "Các bước giải...", "thang_diem": {{"Ý 1...": 0.5}}}}
        ]
      }}
    }}
    """
    response = model.generate_content(prompt)
    raw = response.text.strip().replace('\n', ' ').replace('\t', ' ')
    raw = re.sub(r'^```json\s*|```$', '', raw, flags=re.IGNORECASE).strip()
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
st.markdown('<div class="main-title">Trợ Lý Thiết Kế Đề Thi</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-header">Ma trận nhận thức & Quy trình 2 bước chống nghẽn</div>', unsafe_allow_html=True)
    
    # 1. KHAI BÁO CÁC SLIDER NHẬP LIỆU TRƯỚC ĐỂ ĐỊNH NGHĨA BIẾN (Quan trọng)
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

    # 2. KHỞI TẠO BIẾN TRẠNG THÁI SESSION STATE
    if 'step1_data' not in st.session_state: 
        st.session_state.step1_data = None

    # 3. THIẾT LẬP LUỒNG XỬ LÝ 2 NÚT BẤM
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("📊 BƯỚC 1: KHỞI TẠO MA TRẬN & ĐẶC TẢ"):
            if total_ratio != 100:
                st.error("Tổng tỷ lệ phần trăm phân bổ điểm phải bằng 100% trước khi khởi tạo.")
            else:
                # Lúc này các biến nb_ratio, th_ratio... đã được định nghĩa ở trên nên sẽ chạy mượt mà
                config_pkg = {
                    "subject": subject, "grade": grade, "num_tn": num_tn, "num_tl": num_tl,
                    "nb_ratio": nb_ratio, "th_ratio": th_ratio, "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio
                }
                with st.spinner("AI đang tính toán phân bổ ma trận và đặc tả..."):
                    try:
                        t_list = [t.strip() for t in topics_list.split('\n') if t.strip()]
                        st.session_state.step1_data = generate_step1_matrix(model, config_pkg, t_list)
                        st.success("✅ Đã thiết lập xong Khung đặc tả bộ môn!")
                    except Exception as e:
                        st.error(f"Bạn đã hết thời hạn miễn phí, xin quay lại vào ngày mai")

    # Hiển thị cấu trúc sau khi xong Bước 1
    if st.session_state.step1_data:
        with st.expander("🔍 Xem trước Bản đặc tả kỹ thuật vừa sinh"):
            st.json(st.session_state.step1_data)
            
        with col_btn2:
            if st.button("🔥 BƯỚC 2: SINH CÂU HỎI & ĐẢO MÃ ĐỀ"):
                config_pkg = {
                    "subject": subject, "grade": grade, "num_tn": num_tn, "num_tl": num_tl,
                    "exam_type": exam_type, "duration": duration, "school_year": school_year
                }
                with st.spinner("AI đang lấy Khung đặc tả để soạn nội dung câu hỏi chi tiết..."):
                    try:
                        rule = SUBJECTS_CONFIG[subject]
                        step2_data = generate_step2_questions(model, config_pkg, st.session_state.step1_data, rule)
                        
                        # Hợp nhất dữ liệu
                        full_data = {
                            "ma_tran": st.session_state.step1_data["ma_tran"],
                            "bang_dac_ta": st.session_state.step1_data["bang_dac_ta"],
                            "de_kiem_tra": step2_data["de_kiem_tra"],
                            "dap_an_chi_tiet": step2_data["dap_an_chi_tiet"]
                        }
                        st.session_state.generated_data = full_data
                        
                        # Chạy thuật toán hoán vị đảo mã đề
                        try: s_code = int(code_prefix)
                        except ValueError: s_code = 101
                        bundle, alignment_df = generate_shuffled_bundle(full_data, s_code, num_codes)
                        st.session_state.multi_codes_data = bundle
                        st.session_state.alignment_table = alignment_df
                        
                        st.success(f"🎉 Hoàn tất trọn vẹn! Đã tạo xong đề gốc và {num_codes} mã đề đảo.")
                    except Exception as e:
                        st.error(f"Bạn đã hết thời hạn miễn phí, xin quay lại vào ngày mai")
                        
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
