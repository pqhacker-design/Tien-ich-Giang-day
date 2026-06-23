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
    "Toán học": "Sử dụng ký tự Unicode toán học trực tiếp trong văn bản trơn. Số mũ dùng kí tự mũ trực tiếp như ², ³, ⁴ (x², cm²). Phân số viết dạng chia ngang (x + 1)/(x - 3). Hình học dùng ΔABC, ∽, ⊥, //.",
    "Vật lý": "Đơn vị đo lường phải chuẩn hóa (Ω, W, J, m/s²). Kí hiệu mũ trực tiếp như s², m³.",
    "Hóa học": "BẮT BUỘC dùng chỉ số dưới Unicode thực tế cho công thức phân tử: H₂SO₄, Ca(OH)₂, Al₂(SO₄)₃. Mũi tên phản ứng dạng → hoặc ⇌.",
    "Tin học": "Các đoạn mã giả, code Python, C++, HTML hoặc ký hiệu logic (AND, OR, NOT, ⊕) phải đặt trong dấu `...` hoặc bọc khối rõ ràng.",
    "Công nghệ": "Ký hiệu mạch điện, thông số kỹ thuật điện trở, bản vẽ kỹ thuật hoặc sơ đồ khối phải mô tả tường minh bằng ký hiệu hoa văn chuẩn.",
    "Ngữ văn": "Các ngữ liệu văn học, đoạn thơ, đoạn văn trích dẫn phải được bọc trong dấu ngoặc kép hoặc ghi rõ nguồn. Câu hỏi trắc nghiệm/tự luận tập trung vào đọc hiểu và làm văn.",
    "Tiếng Anh / Ngoại ngữ": "Toàn bộ câu hỏi, phương án lựa chọn và văn bản đọc hiểu phải viết bằng ngôn ngữ đích chuẩn bản xứ, không sai chính tả, có phần trọng âm, ngữ âm rõ ràng.",
    "Lịch sử & Địa lý": "Mốc thời gian, số liệu thống kê tọa độ, ký hiệu bản đồ, số liệu kinh tế - xã hội phải chính xác tuyệt đối theo dòng sự kiện và Atlat.",
    "Giáo dục Kinh tế và Pháp luật": "Các thuật ngữ pháp lý, điều luật, tình huống thực tế phải bọc trong quy chuẩn trích dẫn lập pháp.",
    "Sinh học / KHTN": "Ký hiệu sơ đồ phép lai (P, F₁, F₂), alen (A₁, a), nhiễm sắc thể (2n, n) hoặc công thức phân tử sinh học phải viết chuẩn xác."
}

# ==========================================
# CÁC HÀM BỔ TRỢ XỬ LÝ VĂN BẢN & ĐỌC FILE
# ==========================================
def extract_text_from_docx(file_bytes):
    """Trích xuất chuỗi văn bản thuần sạch từ file .docx"""
    try:
        doc = Document(BytesIO(file_bytes))
        fullText = []
        for para in doc.paragraphs:
            if para.text.strip():
                fullText.append(para.text)
        return "\n".join(fullText)
    except Exception as e:
        return f"Lỗi đọc file Word: {str(e)}"

def add_math_run_to_paragraph(paragraph, text):
    """
    Kiến trúc Unicode Thực chiến: Loại bỏ hoàn toàn gánh nặng render XML/LaTeX,
    ghi trực tiếp text chứa ký tự toán học Unicode giúp triệt tiêu 100% lỗi hiển thị.
    """
    if not text: return
    text = str(text).replace('\\n', '\n').replace('\\', '').replace('$', '').strip()
    text = re.sub(r'\btext\s+(km/h|km|phút|giờ|cm²|cm|s|kg|m)\b', r'\1', text)
    
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if index > 0:
            new_run = paragraph.add_run()
            new_run.add_break()
        if line.strip():
            paragraph.add_run(line)

# ==========================================
# KHỞI TẠO SESSION STATE
# ==========================================
if 'generated_data' not in st.session_state: st.session_state.generated_data = None
if 'step1_data' not in st.session_state: st.session_state.step1_data = None
if 'multi_codes_data' not in st.session_state: st.session_state.multi_codes_data = {}
if 'alignment_table' not in st.session_state: st.session_state.alignment_table = None
if 'user_custom_req' not in st.session_state: st.session_state.user_custom_req = ""

# ==========================================
# THUẬT TOÁN ĐẢO ĐỀ MULTI-CODE CHO PHIÊN BẢN CẤU TRÚC MỚI
# ==========================================
def generate_shuffled_bundle(original_data, start_code, num_codes):
    bundle = {}
    alignment_records = []
    de_goc = original_data.get('de_kiem_tra', {})
    
    tn_4_lua_chon_goc = de_goc.get('trac_nghiem_4_lua_chon', [])
    
    if not tn_4_lua_chon_goc and not de_goc.get('trac_nghiem_dung_sai') and not de_goc.get('trac_nghiem_tra_loi_ngan'):
        return bundle, None

    for i in range(num_codes):
        current_code = str(start_code + i)
        shuffled_data = copy.deepcopy(original_data)
        
        if tn_4_lua_chon_goc:
            tn_current = shuffled_data['de_kiem_tra']['trac_nghiem_4_lua_chon']
            random.seed(int(current_code) + 200)
            indexed_tn = list(enumerate(tn_current))
            random.shuffle(indexed_tn)
            
            new_tn_list = []
            new_dap_an_tn = {}
            
            for new_idx, (old_idx, q) in enumerate(indexed_tn):
                new_id = f"{new_idx + 1}"
                old_id = f"Câu {old_idx + 1}"
                
                q['id'] = int(new_id)
                opts = { "A": q.get("A",""), "B": q.get("B",""), "C": q.get("C",""), "D": q.get("D","") }
                old_correct_key = shuffled_data['dap_an_chi_tiet']['trac_nghiem_4_lua_chon'].get(str(old_idx + 1))
                old_correct_value = opts.get(old_correct_key)
                
                opt_values = list(opts.values())
                random.shuffle(opt_values)
                
                for o_idx, char in enumerate(['A', 'B', 'C', 'D']):
                    q[char] = opt_values[o_idx]
                    if opt_values[o_idx] == old_correct_value:
                        new_correct_key = char
                
                new_dap_an_tn[str(new_id)] = new_correct_key
                new_tn_list.append(q)
                
                alignment_records.append({
                    "Mã đề": current_code, "Câu hỏi gốc": old_id, "Vị trí mới": f"Câu {new_id}", "Đáp án mới": new_correct_key
                })
                
            shuffled_data['de_kiem_tra']['trac_nghiem_4_lua_chon'] = new_tn_list
            shuffled_data['dap_an_chi_tiet']['trac_nghiem_4_lua_chon'] = new_dap_an_tn
            
        bundle[current_code] = shuffled_data

    if alignment_records:
        df_log = pd.DataFrame(alignment_records)
        pivot_df = df_log.pivot(index='Câu hỏi gốc', columns='Mã đề', values='Vị trí mới')
        pivot_df = pivot_df.reindex(index=sorted(pivot_df.index, key=lambda x: int(re.search(r'\d+', x).group()))).reset_index()
        return bundle, pivot_df
    return bundle, None

# ==========================================
# TRÍCH XUẤT VÀ KẾT NỐI GEMINI AI ĐA MÔN ĐỘNG
# ==========================================
def init_gemini_client(api_key):
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"Lỗi API Key hoặc cấu hình kết nối: {e}")
        return None

def generate_step1_matrix(model, config, raw_input_data):
    """
    LƯỢT 1: Hỗ trợ xử lý đa phương thức văn bản/hình ảnh/PDF để sinh Ma trận & Bản đặc tả
    """
    prompt_text = f"""
    Bạn là chuyên gia khảo thí cấp cao của Bộ Giáo dục. Hãy lập Ma trận và Bản đặc tả đề kiểm tra môn {config['subject']} - Khối Lớp {config['grade']}.
    Độ khó mục tiêu: {config['difficulty']}.
    Số câu Trắc nghiệm 4 lựa chọn: {config['num_tn_4_lua_chon']}, Số câu Đúng/Sai: {config['num_tn_dung_sai']}, Số câu Trả lời ngắn: {config['num_tn_tra_loi_ngan']}, Số câu Tự luận: {config['num_tl']}. 
    Tỷ lệ nhận thức: Nhận biết {config['nb_ratio']}% , Thông hiểu {config['th_ratio']}%, Vận dụng {config['vd_ratio']}%, Vận dụng cao {config['vdc_ratio']}%.
    
    YÊU CẦU BẮT BUỘC:
    - Hãy phân tích thật sâu tài liệu/hình ảnh/yêu cầu đính kèm đi cùng lệnh này để phân chia thành các "chu_de" và "noi_dung" tương ứng trong ma trận và bản đặc tả.
    - Tuyệt đối bám sát nội dung từ nguồn dữ liệu được cung cấp, không tự ý bịa thêm kiến thức nằm ngoài phạm vi tài liệu.
    """
    
    if st.session_state.get("user_custom_req"):
        prompt_text += f"\n[Yêu cầu tùy biến bổ sung từ giáo viên: {st.session_state.user_custom_req}]\n"

    contents_to_send = []
    if isinstance(raw_input_data, dict) and "mime_type" in raw_input_data:
        contents_to_send.append(raw_input_data)
        prompt_text += "\n(Hãy đọc nội dung từ file đính kèm đa phương thức ở trên để lập ma trận)"
        contents_to_send.append(prompt_text)
    else:
        prompt_text += f"\nNGUỒN DỮ LIỆU KIẾN THỨC BẮT BUỘC:\n\"\"\"\n{raw_input_data}\n\"\"\""
        contents_to_send.append(prompt_text)

    response = model.generate_content(contents_to_send)
    raw = response.text.strip().replace('\n', ' ').replace('\t', ' ')
    raw = re.sub(r'^```json\s*|```$', '', raw, flags=re.IGNORECASE).strip()
    return json.loads(raw, strict=False)

def generate_step2_questions(model, config, matrix_data, subject_rule, raw_input_data):
    """
    LƯỢT 2: Sinh Đề thi chuẩn cấu trúc dựa trên Ma trận và nội dung tài liệu gốc đa phương thức
    """
    dac_ta_str = json.dumps(matrix_data.get('bang_dac_ta', []), ensure_ascii=False)
    
    prompt_text = f"""
    Bạn là chuyên gia soạn đề thi bám sát cấu trúc đề minh họa mới của Bộ Giáo dục. Dựa trên Bản đặc tả sau: {dac_ta_str}
    Hãy thiết lập chi tiết nội dung đề kiểm tra môn {config['subject']}, Khối {config['grade']}.
    Đặc thù môn học cần bám sát: {subject_rule}

    Yêu cầu số lượng câu hỏi cần tạo:
    - Phần I (Trắc nghiệm nhiều lựa chọn): {config['num_tn_4_lua_chon']} câu.
    - Phần II (Trắc nghiệm Đúng/Sai): {config['num_tn_dung_sai']} câu (mỗi câu gồm 4 ý lựa chọn a, b, c, d).
    - Phần III (Trắc nghiệm Trả lời ngắn): {config['num_tn_tra_loi_ngan']} câu.
    - Phần IV (Tự luận): {config['num_tl']} câu.
    
    YÊU CẦU ĐỘ KHÓ VÀ TÍNH PHÂN HÓA (BẮT BUỘC):
    - Đề thi này đang được thiết lập ở mức độ: "{config['difficulty']}".
    - Hãy phân phối độ sâu tư duy, độ phức tạp của ngữ cảnh và các bước tính toán của câu hỏi bám sát theo mức độ khó này. 

    QUY ĐỊNH ĐỊNH DẠNG TOÁN HỌC & KHTN (BẮT BUỘC KHÔNG DÙNG LATEX):
    - TUYỆT ĐỐI KHÔNG sử dụng ký tự $, \, frac, neq, sim, triangle, cdot, circ hoặc ^.
    - Sử dụng ký tự Unicode toán học trực tiếp trong văn bản trơn (Ví dụ: x², cm², ΔABC, ∽, ⊥, //, →, ⇌, ·, ≠, °).
    - Xuống dòng các ý a), b), c) bằng cách gõ ký tự xuống dòng thực tế.

    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN CÓ CẤU TRÚC SAU:
    {{
      "de_kiem_tra": {{
        "trac_nghiem_4_lua_chon": [
          {{"id": 1, "cau_hoi": "Nội dung câu hỏi...", "A": "Đáp án A", "B": "Đáp án B", "C": "Đáp án C", "D": "Đáp án D"}}
        ],
        "trac_nghiem_dung_sai": [
          {{"id": 1, "cau_hoi": "Nội dung câu hỏi...", "cac_y": {{"a": "Ý a", "b": "Ý b", "c": "Ý c", "d": "Ý d"}}}}
        ],
        "trac_nghiem_tra_loi_ngan": [
          {{"id": 1, "cau_hoi": "Nội dung câu hỏi..."}}
        ],
        "tu_luan": [
          {{"id": 1, "cau_hoi": "Nội dung câu hỏi..."}}
        ]
      }},
      "dap_an_chi_tiet": {{
        "trac_nghiem_4_lua_chon": {{"1": "A"}},
        "trac_nghiem_dung_sai": {{"1": {{"a": "Đúng", "b": "Sai", "c": "Đúng", "d": "Sai"}}}},
        "trac_nghiem_tra_loi_ngan": {{"1": "25"}},
        "tu_luan": {{"1": "Lời giải..."}}
      }}
    }}
    """
    
    contents_to_send = []
    if isinstance(raw_input_data, dict) and "mime_type" in raw_input_data:
        contents_to_send.append(raw_input_data)
        prompt_text += "\n(Hãy trích xuất kiến thức/ngữ liệu thực tế từ file đính kèm đa phương thức ở trên để soạn câu hỏi chuẩn xác)"
        contents_to_send.append(prompt_text)
    else:
        prompt_text += f"\nNGUỒN KIẾN THỨC BẮT BUỘC ĐỂ SOẠN CÂU HỎI:\n\"\"\"\n{raw_input_data}\n\"\"\""
        contents_to_send.append(prompt_text)

    response = model.generate_content(contents_to_send)
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
    
    p_top = doc.add_paragraph()
    p_top.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.add_run("TRƯỜNG THCS & THPT Artificial Intelligence (AI)\n").bold = True
    
    exam_title = f"ĐỀ KIỂM TRA {config.get('exam_type', '').upper()} - MÃ ĐỀ: {code_label}\n"
    run_title = p_top.add_run(exam_title)
    run_title.bold = True
    run_title.size = Pt(14)
    
    p_top.add_run(f"Môn: {config['subject']} | Khối: {config['grade']} | Thời gian: {config['duration']} phút\n")
    p_top.add_run("-------------------------------------\n")
    
    if include_matrix and 'ma_tran' in data:
        doc.add_heading("I. MA TRẬN PHÂN BỔ ĐỀ KIỂM TRA", level=2)
        m_table = doc.add_table(rows=1, cols=5)
        m_table.style = 'Table Grid'
        m_hdrs = ['Nội dung kiến thức', 'Nhận biết', 'Thông hiểu', 'Vận dụng', 'Vận dụng cao']
        for idx, h in enumerate(m_hdrs): m_table.rows[0].cells[idx].text = h
        
        total_nb_tn, total_nb_tl = 0, 0
        total_th_tn, total_th_tl = 0, 0
        total_vd_tn, total_vd_tl = 0, 0
        total_vdc_tn, total_vdc_tl = 0, 0
        
        for item in data['ma_tran']:
            row = m_table.add_row().cells
            row[0].text = str(item.get('chu_de', ''))
            
            nb_tn, nb_tl = item.get('nb_tn', 0), item.get('nb_tl', 0)
            th_tn, th_tl = item.get('th_tn', 0), item.get('th_tl', 0)
            vd_tn, vd_tl = item.get('vd_tn', 0), item.get('vd_tl', 0)
            vdc_tn, vdc_tl = item.get('vdc_tn', 0), item.get('vdc_tl', 0)
            
            row[1].text = f"TN:{nb_tn}|TL:{nb_tl}"
            row[2].text = f"TN:{th_tn}|TL:{th_tl}"
            row[3].text = f"TN:{vd_tn}|TL:{vd_tl}"
            row[4].text = f"TN:{vdc_tn}|TL:{vdc_tl}"
            
            total_nb_tn += nb_tn; total_nb_tl += nb_tl
            total_th_tn += th_tn; total_th_tl += th_tl
            total_vd_tn += vd_tn; total_vd_tl += vd_tl
            total_vdc_tn += vdc_tn; total_vdc_tl += vdc_tl

        row_total_q = m_table.add_row().cells
        row_total_q[0].text = "Tổng số câu"
        row_total_q[0].paragraphs[0].runs[0].font.bold = True
        
        row_total_q[1].text = f"TN: {total_nb_tn} | TL: {total_nb_tl}"
        row_total_q[2].text = f"TN: {total_th_tn} | TL: {total_th_tl}"
        row_total_q[3].text = f"TN: {total_vd_tn} | TL: {total_vd_tl}"
        row_total_q[4].text = f"TN: {total_vdc_tn} | TL: {total_vdc_tl}"
        
        row_total_p = m_table.add_row().cells
        row_total_p[0].text = "Tổng số điểm"
        row_total_p[0].paragraphs[0].runs[0].font.bold = True
        
        row_total_p[1].text = f"{config.get('nb_ratio', 40) / 10} điểm"
        row_total_p[2].text = f"{config.get('th_ratio', 30) / 10} điểm"
        row_total_p[3].text = f"{config.get('vd_ratio', 20) / 10} điểm"
        row_total_p[4].text = f"{config.get('vdc_ratio', 10) / 10} điểm"
        
        for i in range(1, 5):
            row_total_q[i].paragraphs[0].runs[0].font.bold = True
            row_total_p[i].paragraphs[0].runs[0].font.bold = True

        doc.add_paragraph()

    if include_matrix and 'bang_dac_ta' in data:
        doc.add_heading("II. BẢNG ĐẶC TẢ KỸ THUẬT ĐỀ KIỂM TRA", level=2)
        dt_table = doc.add_table(rows=1, cols=6)
        dt_table.style = 'Table Grid'
        hdrs = ['Chủ đề', 'Nội dung kiến thức', 'Mức độ', 'Yêu cầu cần đạt', 'Số câu', 'Điểm']
        for idx, h in enumerate(hdrs): dt_table.rows[0].cells[idx].text = h
        for item in data['bang_dac_ta']:
            row = dt_table.add_row().cells
            row[0].text = str(item.get('chu_de', ''))
            row[1].text = str(item.get('noi_dung', ''))
            row[2].text = str(item.get('muc_do', ''))
            row[3].text = str(item.get('yeu_cau_can_dat', ''))
            row[4].text = str(item.get('so_cau', ''))
            row[5].text = f"{item.get('diem', 0)} đ"
        doc.add_paragraph()
        
    doc.add_heading("III. NỘI DUNG CÂU HỎI", level=2)
    de = data.get('de_kiem_tra', {})
    
    list_4lc = de.get("trac_nghiem_4_lua_chon", [])
    if list_4lc:
        p_hdr1 = doc.add_paragraph()
        p_hdr1.add_run("PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn. ").bold = True
        p_hdr1.add_run("Thí sinh trả lời từ câu 1 đến câu hết phần này. Mỗi câu hỏi chỉ chọn một phương án.")
        
        for q in list_4lc:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))
            
            p_opts = doc.add_paragraph()
            p_opts.paragraph_format.left_indent = Inches(0.3)
            p_opts.add_run("A. ").bold = True
            add_math_run_to_paragraph(p_opts, q.get('A', ''))
            p_opts.add_run("   B. ").bold = True
            add_math_run_to_paragraph(p_opts, q.get('B', ''))
            p_opts.add_run("   C. ").bold = True
            add_math_run_to_paragraph(p_opts, q.get('C', ''))
            p_opts.add_run("   D. ").bold = True
            add_math_run_to_paragraph(p_opts, q.get('D', ''))

    list_ds = de.get("trac_nghiem_dung_sai", [])
    if list_ds:
        p_hdr2 = doc.add_paragraph()
        p_hdr2.add_run("\nPHẦN II. Câu trắc nghiệm đúng sai. ").bold = True
        p_hdr2.add_run("Thí sinh trả lời từ câu 1 đến câu hết phần này. Trong mỗi ý a), b), c), d) ở mỗi câu, thí sinh chọn đúng hoặc sai.")
        
        for q in list_ds:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))
            
            cac_y = q.get("cac_y", {})
            for key in ['a', 'b', 'c', 'd']:
                if key in cac_y:
                    p_y = doc.add_paragraph()
                    p_y.paragraph_format.left_indent = Inches(0.4)
                    p_y.add_run(f"{key}) ").bold = True
                    add_math_run_to_paragraph(p_y, cac_y.get(key, ''))

    list_tln = de.get("trac_nghiem_tra_loi_ngan", [])
    if list_tln:
        p_hdr3 = doc.add_paragraph()
        p_hdr3.add_run("\nPHẦN III. Câu trắc nghiệm trả lời ngắn. ").bold = True
        p_hdr3.add_run("Thí sinh trả lời từ câu 1 đến câu hết phần này. Viết kết quả ngắn gọn vào ô trống tương ứng.")
        
        for q in list_tln:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))

    list_tl = de.get("tu_luan", [])
    if list_tl:
        p_hdr4 = doc.add_paragraph()
        p_hdr4.add_run("\nPHẦN IV. Tự luận. ").bold = True
        p_hdr4.add_run("Thí sinh trình bày chi tiết các bước giải quyết bài toán vào tờ giấy thi.")
        
        for q in list_tl:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))

    doc.add_page_break()
    doc.add_paragraph().add_run(f"HƯỚNG DẪN CHẤM & ĐÁP ÁN - MÃ ĐỀ: {code_label}\n").bold = True
    da = data.get('dap_an_chi_tiet', {})
    
    if da.get('trac_nghiem_4_lua_chon'):
        doc.add_paragraph().add_run("Đáp án Phần I (Trắc nghiệm nhiều lựa chọn):").bold = True
        ans_table1 = doc.add_table(rows=1, cols=2)
        ans_table1.style = 'Table Grid'
        ans_table1.rows[0].cells[0].text = "Câu hỏi"
        ans_table1.rows[0].cells[1].text = "Đáp án"
        for q_id, val in da['trac_nghiem_4_lua_chon'].items():
            rc = ans_table1.add_row().cells
            rc[0].text = f"Câu {q_id}"
            rc[1].text = str(val)
        doc.add_paragraph()

    if da.get('trac_nghiem_dung_sai'):
        doc.add_paragraph().add_run("Đáp án Phần II (Trắc nghiệm Đúng/Sai):").bold = True
        ans_table2 = doc.add_table(rows=1, cols=2)
        ans_table2.style = 'Table Grid'
        ans_table2.rows[0].cells[0].text = "Câu hỏi"
        ans_table2.rows[0].cells[1].text = "Hướng dẫn đáp án từng ý"
        for q_id, val_dict in da['trac_nghiem_dung_sai'].items():
            rc = ans_table2.add_row().cells
            rc[0].text = f"Câu {q_id}"
            if isinstance(val_dict, dict):
                rc[1].text = ", ".join([f"{k}: {v}" for k, v in val_dict.items()])
            else:
                rc[1].text = str(val_dict)
        doc.add_paragraph()

    if da.get('trac_nghiem_tra_loi_ngan'):
        doc.add_paragraph().add_run("Đáp án Phần III (Trắc nghiệm trả lời ngắn):").bold = True
        ans_table3 = doc.add_table(rows=1, cols=2)
        ans_table3.style = 'Table Grid'
        ans_table3.rows[0].cells[0].text = "Câu hỏi"
        ans_table3.rows[0].cells[1].text = "Kết quả ngắn"
        for q_id, val in da['trac_nghiem_tra_loi_ngan'].items():
            rc = ans_table3.add_row().cells
            rc[0].text = f"Câu {q_id}"
            rc[1].text = str(val)
        doc.add_paragraph()

    if da.get('tu_luan'):
        doc.add_paragraph().add_run("Hướng dẫn giải chi tiết Phần IV (Tự luận):").bold = True
        for q_id, detail in da['tu_luan'].items() if isinstance(da['tu_luan'], dict) else enumerate(da['tu_luan']):
            p_tl = doc.add_paragraph()
            p_tl.add_run(f"Câu {q_id}: ").bold = True
            add_math_run_to_paragraph(p_tl, str(detail))
            
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# GIAO DIỆN ĐIỀU KHIỂN STREAMLIT
# ==========================================
st.markdown('<div class="main-title">Trợ Lý Ra Đề Kiểm Tra</div>', unsafe_allow_html=True)
st.write("Hỗ trợ GV ra đề kiểm tra với ma trận và bảng đặc tả bám sát thông tư, hướng dẫn mới.")
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng cấu hình Google Gemini API Key tại Trang chủ trước khi vận hành.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop()

model = init_gemini_client(api_key_input)

# Biến toàn cục nhận diện dữ liệu nạp đầu vào cho cả 2 bước
if 'current_document_content' not in st.session_state: 
    st.session_state.current_document_content = ""

tab1, tab2, tab3 = st.tabs(["📋 1. Chọn Môn học & Thiết lập số câu", "📊 2. Phân bổ Ma trận kiến thức", "📥 3. Đóng gói & Xuất các Mã đề"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Lựa chọn bộ môn & Thông tin chung</div>', unsafe_allow_html=True)
        subject = st.selectbox("Chọn môn học cần thiết lập đề thi:", list(SUBJECTS_CONFIG.keys()))
        grade = st.selectbox("Khối lớp học:", [str(i) for i in range(1, 13)], index=7)
        exam_type = st.selectbox("Hình thức kiểm tra:", ["15 phút", "45 phút", "Giữa học kỳ I", "Cuối học kỳ I", "Giữa học kỳ II", "Cuối học kỳ II"])
        duration = st.number_input("Thời lượng làm bài (phút):", min_value=15, max_value=150, value=60, step=5)
        school_year = st.text_input("Năm học:", value="2026-2027")
        
        difficulty_levels = {
            "Cơ bản (Phù hợp HS Yếu - Trung bình)": {"nb": 50, "th": 30, "vd": 16, "vdc": 4},
            "Tiêu chuẩn (Bám sát SGK, đại trà)": {"nb": 40, "th": 30, "vd": 20, "vdc": 10},
            "Nâng cao (Phù hợp lớp khá - lớp chọn)": {"nb": 30, "th": 30, "vd": 25, "vdc": 15},
            "Phân hóa mạnh (Bồi dưỡng giỏi, thi học sinh giỏi)": {"nb": 20, "th": 30, "vd": 30, "vdc": 20}
        }
        level_choice = st.selectbox("Độ khó mục tiêu của đề thi:", list(difficulty_levels.keys()), index=1)
        target_ratios = difficulty_levels[level_choice]

    with col2:
        st.markdown('<div class="section-header">Cấu hình số lượng câu hỏi</div>', unsafe_allow_html=True)
        num_tn_4_lua_chon = st.number_input("Trắc nghiệm nhiều lựa chọn (Phần I):", min_value=0, max_value=40, value=12)
        num_tn_dung_sai = st.number_input("Trắc nghiệm Đúng/Sai (Phần II):", min_value=0, max_value=10, value=4)
        num_tn_tra_loi_ngan = st.number_input("Trắc nghiệm Trả lời ngắn (Phần III):", min_value=0, max_value=15, value=6)
        num_tl = st.number_input("Số câu hỏi Tự luận (Phần IV):", min_value=0, max_value=10, value=0)
        
        st.markdown('---')
        code_choice = st.selectbox("Số lượng mã đề đảo tự động:", [1, 2, 4, 6, 8, "Nhập số lượng bất kỳ"], index=2)
        num_codes = st.number_input("Số mã đề đảo thực tế:", min_value=1, max_value=24, value=4) if code_choice == "Nhập số lượng bất kỳ" else int(code_choice)
        code_prefix = st.text_input("Ký hiệu mã đề bắt đầu:", value="101")

with tab2:
    st.markdown('<div class="section-header">Nguồn nội dung kiến thức ra đề</div>', unsafe_allow_html=True)
    
    content_source = st.radio(
        "Chọn phương thức cung cấp nội dung/chủ đề kiến thức:",
        ["Nhập tay danh sách chủ đề", "Upload file tài liệu đa phương thức (Word, TXT, PDF, Ảnh)"],
        horizontal=True
    )
    
    if content_source == "Nhập tay danh sách chủ đề":
        topics_list = st.text_area(
            "Danh sách các chủ đề kiến thức (Mỗi dòng một chủ đề):", 
            value="Nội dung 1: Kiến thức trọng tâm chương học cũ\nNội dung 2: Kiến thức nâng cao bổ trợ",
            height=120
        )
        st.session_state.current_document_content = topics_list
    else:
        uploaded_doc = st.file_uploader(
            "Tải lên tài liệu, đề cương, ảnh chụp sách hoặc file PDF (.docx, .txt, .pdf, .png, .jpg, .jpeg):", 
            type=["docx", "txt", "pdf", "png", "jpg", "jpeg"]
        )
        user_custom_req = st.text_input("Yêu cầu bổ sung khi đọc tài liệu (Ví dụ: 'Chỉ tập trung vào Chương 2', 'Bỏ qua các bài đọc hiểu'):", value="")
        st.session_state.user_custom_req = user_custom_req.strip()
        
        if uploaded_doc is not None:
            file_bytes = uploaded_doc.read()
            file_ext = uploaded_doc.name.split('.')[-1].lower()
            
            if file_ext == "txt":
                st.session_state.current_document_content = str(file_bytes, "utf-8")
                st.info(f"✅ Đã trích xuất văn bản từ file TXT: {uploaded_doc.name}")
            elif file_ext == "docx":
                st.session_state.current_document_content = extract_text_from_docx(file_bytes)
                st.info(f"✅ Đã trích xuất văn bản từ file Word: {uploaded_doc.name}")
            elif file_ext == "pdf":
                st.session_state.current_document_content = {
                    "mime_type": "application/pdf",
                    "data": file_bytes
                }
                st.info(f"📂 Đã đính kèm file PDF: {uploaded_doc.name} (Gemini sẽ quét toàn bộ tài liệu)")
            elif file_ext in ["png", "jpg", "jpeg"]:
                mime_type = "image/png" if file_ext == "png" else "image/jpeg"
                st.session_state.current_document_content = {
                    "mime_type": mime_type,
                    "data": file_bytes
                }
                st.info(f"🖼️ Đã đính kèm file Ảnh: {uploaded_doc.name} (Gemini sẽ phân tích hình ảnh trực quan)")

    st.markdown('<div class="section-header">Phân bổ Ma trận tư duy</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: nb_ratio = st.slider("Nhận biết (%)", 0, 100, target_ratios["nb"])
    with c2: th_ratio = st.slider("Thông hiểu (%)", 0, 100, target_ratios["th"])
    with c3: vd_ratio = st.slider("Vận dụng (%)", 0, 100, target_ratios["vd"])
    with c4: vdc_ratio = st.slider("Vận dụng cao (%)", 0, 100, target_ratios["vdc"])
    
    total_ratio = nb_ratio + th_ratio + vd_ratio + vdc_ratio
    if total_ratio != 100:
        st.warning(f"⚠️ Tổng tỷ lệ hiện tại đạt {total_ratio}%. Thầy cô vui lòng căn chỉnh về chính xác 100%.")

    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("📊 BƯỚC 1: KHỞI TẠO MA TRẬN & ĐẶC TẢ"):
            if total_ratio != 100:
                st.error("Tổng tỷ lệ phần trăm phân bổ điểm phải bằng 100% trước khi khởi tạo.")
            elif not st.session_state.current_document_content:
                st.error("Vui lòng cung cấp danh sách chủ đề hoặc tải file tài liệu đính kèm lên trước.")
            else:
                config_pkg = {
                    "subject": subject, "grade": grade, "num_tn_4_lua_chon": num_tn_4_lua_chon, 
                    "num_tn_dung_sai": num_tn_dung_sai, "num_tn_tra_loi_ngan": num_tn_tra_loi_ngan, "num_tl": num_tl,
                    "nb_ratio": nb_ratio, "th_ratio": th_ratio, "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio,
                    "difficulty": level_choice
                }
                with st.spinner("AI đang đọc tài liệu và tính toán khung ma trận đặc tả..."):
                    try:
                        st.session_state.step1_data = generate_step1_matrix(model, config_pkg, st.session_state.current_document_content)
                        st.success("✅ Đã thiết lập xong Khung đặc tả bộ môn!")
                    except Exception as e:
                        st.error(f"Lỗi phân tích kết nối: {e}. Xin vui lòng thử lại sau.")

    if st.session_state.step1_data:
        with st.expander("🔍 Xem trước Bản đặc tả kỹ thuật vừa sinh"):
            st.json(st.session_state.step1_data)
            
        with col_btn2:
            if st.button("🔥 BƯỚC 2: SINH CÂU HỎI & ĐẢO MÃ ĐỀ"):
                config_pkg = {
                    "subject": subject, "grade": grade, "num_tn_4_lua_chon": num_tn_4_lua_chon, 
                    "num_tn_dung_sai": num_tn_dung_sai, "num_tn_tra_loi_ngan": num_tn_tra_loi_ngan, "num_tl": num_tl,
                    "nb_ratio": nb_ratio, "th_ratio": th_ratio, "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio,
                    "difficulty": level_choice
                }
                with st.spinner("AI đang bám sát Khung đặc tả để soạn nội dung câu hỏi thi..."):
                    try:
                        rule = SUBJECTS_CONFIG[subject]
                        step2_data = generate_step2_questions(model, config_pkg, st.session_state.step1_data, rule, st.session_state.current_document_content)
                        
                        full_data = {
                            "ma_tran": st.session_state.step1_data["ma_tran"],
                            "bang_dac_ta": st.session_state.step1_data["bang_dac_ta"],
                            "de_kiem_tra": step2_data["de_kiem_tra"],
                            "dap_an_chi_tiet": step2_data["dap_an_chi_tiet"]
                        }
                        st.session_state.generated_data = full_data
                        
                        try: s_code = int(code_prefix)
                        except ValueError: s_code = 101
                        
                        bundle, alignment_df = generate_shuffled_bundle(full_data, s_code, num_codes)
                        # Đảm bảo lưu cả "ĐỀ GỐC" vào gói dữ liệu chung
                        bundle["ĐỀ GỐC"] = full_data
                        st.session_state.multi_codes_data = bundle
                        st.session_state.alignment_table = alignment_df
                        
                        st.success(f"🎉 Hoàn tất trọn vẹn! Đã tạo xong ĐỀ GỐC và {num_codes} mã đề đảo hoán vị.")
                    except Exception as e:
                        st.error(f"Lỗi tạo câu hỏi: {e}. Vui lòng kiểm tra lại API Key hoặc file đính kèm.")
                        
with tab3:
    if not st.session_state.get('multi_codes_data'):
        st.info("Hệ thống đang ở trạng thái chờ nạp dữ liệu câu hỏi thành công từ Bước 2.")
    else:
        config_pkg = { 
            "subject": subject, "grade": grade, "exam_type": exam_type, "duration": duration, "school_year": school_year,
            "nb_ratio": nb_ratio, "th_ratio": th_ratio, "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio
        }
        inc_mat = st.checkbox("Chèn bảng Ma trận phân bổ vào đầu tài liệu", value=True)
        
        export_mode = st.radio("Hình thức xuất bản bộ đề:", 
                               ["Tải file đơn lẻ (Tùy chọn tải Đề gốc hoặc Mã đề đảo)", 
                                "Nén tất cả mã đề (Bao gồm cả Đề gốc) vào file ZIP", 
                                "Gộp chung tất cả mã đề vào 1 file Word duy nhất"])
        
        if export_mode == "Tải file đơn lẻ (Tùy chọn tải Đề gốc hoặc Mã đề đảo)":
            all_available_codes = list(st.session_state.multi_codes_data.keys())
            
            # Đẩy "ĐỀ GỐC" lên đầu danh sách để dễ lựa chọn
            if "ĐỀ GỐC" in all_available_codes:
                all_available_codes.remove("ĐỀ GỐC")
                all_available_codes = ["ĐỀ GỐC"] + all_available_codes
                
            sel_code = st.selectbox("Chọn bản đề cần xuất bản:", all_available_codes)
            docx_buf = build_single_docx(config_pkg, st.session_state.multi_codes_data[sel_code], sel_code, include_matrix=inc_mat)
            
            st.download_button(
                label=f"📥 TẢI FILE WORD [{sel_code}]", 
                data=docx_buf, 
                file_name=f"De_{subject}_{sel_code}.docx", 
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        elif export_mode == "Nén tất cả mã đề (Bao gồm cả Đề gốc) vào file ZIP":
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for c_code, c_data in st.session_state.multi_codes_data.items():
                    d_buf = build_single_docx(config_pkg, c_data, c_code, include_matrix=inc_mat)
                    filename_in_zip = f"De_Goc_{subject}_Lop{grade}.docx" if c_code == "ĐỀ GỐC" else f"De_{subject}_Lop{grade}_MaDe_{c_code}.docx"
                    zip_file.writestr(filename_in_zip, d_buf.getvalue())
            zip_buffer.seek(0)
            st.download_button(label="📥 TẢI FILE NÉN ZIP TRỌN BỘ MÃ ĐỀ + ĐỀ GỐC", data=zip_buffer, file_name=f"Bo_De_{subject}_TronGoi.zip", mime="application/zip")
            
        else:
            main_doc = Document()
            all_codes = list(st.session_state.multi_codes_data.keys())
            if "ĐỀ GỐC" in all_codes:
                all_codes.remove("ĐỀ GỐC")
                all_codes = ["ĐỀ GỐC"] + all_codes
                
            for idx, c_code in enumerate(all_codes):
                c_data = st.session_state.multi_codes_data[c_code]
                temp_buf = build_single_docx(config_pkg, c_data, c_code, include_matrix=inc_mat)
                t_doc = Document(temp_buf)
                for element in t_doc.element.body: main_doc.element.body.append(element)
                if idx < len(all_codes) - 1: main_doc.add_page_break()
                
            all_buf = BytesIO()
            main_doc.save(all_buf)
            all_buf.seek(0)
            st.download_button(label="📥 TẢI FILE GỘP TOÀN BỘ MÃ ĐỀ (.DOCX)", data=all_buf, file_name=f"Gop_Bo_De_{subject}_KemDeGoc.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        if st.session_state.alignment_table is not None:
            st.markdown("---")
            st.markdown("### 📊 Bảng đối chiếu hoán vị mã đề nội bộ tra cứu nhanh")
            st.dataframe(st.session_state.alignment_table, use_container_width=True)

# --- FOOTER CỐ ĐỊNH ---
st.divider()
st.markdown("---")

# 5. Chân trang (Footer)
col_left, col_right = st.columns(2)
with col_left:
    st.caption("Phát triển bởi Ngo Thanh Hung © 2026")
with col_right:
    st.markdown(
        "<div style='text-align: right; color: gray; font-size: 0.85em;'>"
        "AI có thể mắc lỗi. Cần kiểm tra kỹ các thông tin quan trọng."
        "</div>", 
        unsafe_allow_html=True
    )
