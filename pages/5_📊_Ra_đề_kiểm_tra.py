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
    .step-active { background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 10px; margin-bottom: 10px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DANH SÁCH CẤU HÌNH BỘ MÔN
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
# CÁC HÀM TIỆN ÍCH & TRÍCH XUẤT
# ==========================================
def extract_text_from_docx(file_bytes):
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
    if not text: return
    text = str(text).replace('\\n', '\n').replace('\\', '').replace('$', '').strip()
    lines = text.split('\n')
    for index, line in enumerate(lines):
        if index > 0:
            paragraph.add_run().add_break()
        if line.strip():
            paragraph.add_run(line)

def clean_and_parse_json(raw_text):
    raw_text = raw_text.strip()
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        json_str = match.group(1)
    else:
        match_brace = re.search(r'(\{.*)', raw_text, re.DOTALL)
        if match_brace:
            json_str = match_brace.group(1)
        else:
            json_str = raw_text

    # Thuật toán tự vá chuỗi dở dang
    json_str = json_str.strip()
    if json_str.endswith(','):
        json_str = json_str[:-1]
    open_braces, close_braces = json_str.count('{'), json_str.count('}')
    open_brackets, close_brackets = json_str.count('['), json_str.count(']')
    
    if json_str.endswith(':'):
        json_str += ' {}'
    if open_braces > close_braces:
        json_str += '}' * (open_braces - close_braces)
    if open_brackets > close_brackets:
        json_str += ']' * (open_brackets - close_brackets)

    json_str = json_str.replace('\r', '').replace('\n', ' ')
    return json.loads(json_str, strict=False)

# ==========================================
# KHỞI TẠO SESSION STATE
# ==========================================
if 'step1_matrix' not in st.session_state: st.session_state.step1_matrix = None
if 'step2_spec' not in st.session_state: st.session_state.step2_spec = None
if 'multi_codes_data' not in st.session_state: st.session_state.multi_codes_data = {}
if 'alignment_table' not in st.session_state: st.session_state.alignment_table = None
if 'current_document_content' not in st.session_state: st.session_state.current_document_content = ""

# ==========================================
# THUẬT TOÁN ĐẢO ĐỀ
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
# CÁC HÀM GỌI API GEMINI CHO TỪNG BƯỚC
# ==========================================
def generate_step1_matrix_only(model, config, raw_input_data):
    prompt_text = f"""
    Bạn là chuyên gia khảo thí. Hãy lập duy nhất bảng Ma trận phân bổ đề kiểm tra môn {config['subject']} - Khối Lớp {config['grade']}.
    Số câu Trắc nghiệm 4 lựa chọn: {config['num_tn_4_lua_chon']} ({config['score_part1']} điểm), 
    Số câu Đúng/Sai: {config['num_tn_dung_sai']} ({config['score_part2']} điểm), 
    Số câu Trả lời ngắn: {config['num_tn_tra_loi_ngan']} ({config['score_part3']} điểm), 
    Số câu Tự luận: {config['num_tl']} ({config['score_part4']} điểm).
    Đặc biệt, lưu ý phân phối điểm số riêng cho câu hỏi Vận dụng cao (VDC) trong đề là: {config['score_vdc_custom']} điểm.
    Tổng điểm của toàn đề bắt buộc là 10 điểm.
    Tỷ lệ nhận thức: Nhận biết {config['nb_ratio']}% , Thông hiểu {config['th_ratio']}%, Vận dụng {config['vd_ratio']}%, Vận dụng cao {config['vdc_ratio']}%.
    Dựa trên tài liệu nguồn, hãy phân tích và chia nhỏ thành các hàng tương ứng với các chủ đề kiến thức.
    
    YÊU CẦU BẮT BUỘC:
    - Phân tích thật sâu tài liệu/hình ảnh/yêu cầu đính kèm đi cùng lệnh này để phân chia thành các "chu_de" và "noi_dung".
    - Phân chia chi tiết số câu hỏi tương ứng dựa trên tổng điểm và số câu của từng phần đã định cấu hình.
    
    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN (KHÔNG CHỨA LỜI THOẠI):
    {{
      "ma_tran": [
        {{
          "tt": 1,
          "chu_de": "Tên chủ đề/Chương lớn",
          "noi_dung": "Nội dung kiến thức cụ thể",
          "nhieu_lua_chon": {{"nb": 2, "th": 1, "vd": 0}},
          "dung_sai": {{"nb": 0, "th": 1, "vd": 0}},
          "tra_loi_ngan": {{"nb": 1, "th": 0}},
          "tu_luan": {{"nb": 0, "th": 0, "vd": 0, "vdc": 0}},
          "tong_diem_phan_tram": 15
        }}
      ]
    }}
    """
    contents = [raw_input_data, prompt_text] if not isinstance(raw_input_data, dict) else [raw_input_data, prompt_text]
    response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
    return clean_and_parse_json(response.text)

def generate_step2_spec_only(model, config, matrix_data):
    matrix_str = json.dumps(matrix_data, ensure_ascii=False)
    prompt_text = f"""
    Bạn là chuyên gia khảo thí. Dựa trên Khung ma trận phân bổ sau đây:
    {matrix_str}
    
    Hãy thiết lập chi tiết Bản đặc tả đề kiểm tra môn {config['subject']} - Lớp {config['grade']}. 
    Với mỗi nội dung kiến thức trong ma trận, hãy tạo các hàng mô tả rõ mức độ đánh giá, yêu cầu cần đạt bám sát chương trình GDPT.
    Hãy viết ngắn gọn phần 'yeu_cau_can_dat' để tránh vượt giới hạn ký tự.

    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN:
    {{
      "bang_dac_ta": [
        {{
          "id_dac_ta": "DT_01",
          "chu_de": "Tên chủ đề",
          "noi_dung": "Kiến thức cụ thể",
          "muc_do": "Nhận biết / Thông hiểu / Vận dụng / Vận dụng cao",
          "yeu_cau_can_dat": "Mô tả ngắn gọn tiêu chí cần đạt...",
          "so_cau": "Ví dụ: 2 câu trắc nghiệm nhiều lựa chọn hoặc 1 câu tự luận",
          "diem": 0.5
        }}
      ]
    }}
    """
    response = model.generate_content(prompt_text, generation_config={"response_mime_type": "application/json"})
    return clean_and_parse_json(response.text)

def generate_step3_questions(model, config, matrix_data, spec_data, subject_rule, raw_input_data):
    matrix_str = json.dumps(matrix_data, ensure_ascii=False)
    spec_str = json.dumps(spec_data, ensure_ascii=False)
    prompt_text = f"""
    Bạn là chuyên gia soạn đề thi chuyên nghiệp. Dựa vào Ma trận: {matrix_str} và Bản đặc tả: {spec_str}
    Hãy viết chi tiết nội dung các câu hỏi thi cho môn {config['subject']}, Khối {config['grade']}.
    Đặc thù môn học: {subject_rule}

    Yêu cầu số lượng câu hỏi và cơ cấu điểm số:
    - Phần I (Trắc nghiệm nhiều lựa chọn): {config['num_tn_4_lua_chon']} câu. Tổng điểm: {config['score_part1']} điểm.
    - Phần II (Trắc nghiệm Đúng/Sai): {config['num_tn_dung_sai']} câu. Tổng điểm: {config['score_part2']} điểm.
    - Phần III (Trắc nghiệm Trả lời ngắn): {config['num_tn_tra_loi_ngan']} câu. Tổng điểm: {config['score_part3']} điểm.
    - Phần IV (Tự luận): {config['num_tl']} câu. Tổng điểm: {config['score_part4']} điểm.
    * Trọng số câu hỏi Vận dụng cao (VDC) trong đề phải chiếm tổng cộng: {config['score_vdc_custom']} điểm.

    QUY ĐỊNH ĐỊNH DẠNG (TUYỆT ĐỐI KHÔNG DÙNG LATEX):
    - KHÔNG sử dụng ký tự $, \, frac, neq, sim, triangle, hoặc ^.
    - Sử dụng ký tự Unicode toán học trực tiếp (Ví dụ: x², cm², ΔABC, ∽, ⊥, //, →, ⇌, ·, ≠, °).

    BẮT BUỘC TRẢ VỀ JSON NGUYÊN BẢN CÓ CẤU TRÚC:
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
    contents = [raw_input_data, prompt_text] if not isinstance(raw_input_data, dict) else [raw_input_data, prompt_text]
    response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
    return clean_and_parse_json(response.text)

# ==========================================
# HÀM XUẤT FILE DOCX TÍCH HỢP CẢ 2 BẢNG
# ==========================================
def build_single_docx(config, data, code_label, include_matrix=True):
    doc = Document()
    for s in doc.sections:
        s.top_margin = Inches(0.79)
        s.bottom_margin = Inches(0.79)
        s.left_margin = Inches(0.79)
        s.right_margin = Inches(0.79)
        
    doc.styles['Normal'].font.name = 'Times New Roman'
    doc.styles['Normal'].font.size = Pt(12)
    
    p_top = doc.add_paragraph()
    p_top.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.add_run("TRƯỜNG THCS & THPT Artificial Intelligence (AI)\n").bold = True
    r_title = p_top.add_run(f"ĐỀ KIỂM TRA {config.get('exam_type', '').upper()} - MÃ ĐỀ: {code_label}\n")
    r_title.bold = True
    r_title.size = Pt(14)
    p_top.add_run(f"Môn: {config['subject']} | Khối: {config['grade']} | Thời gian: {config['duration']} phút\n")
    p_top.add_run("-------------------------------------\n")
    
    if include_matrix:
        # Tầng 1: Vẽ Ma Trận
        doc.add_heading("I. MA TRẬN PHÂN BỔ ĐỀ KIỂM TRA", level=2)
        is_cv7991 = "7991" in config.get("matrix_template", "")
        
        if is_cv7991 and 'ma_tran' in data:
            m_table = doc.add_table(rows=1, cols=8)
            m_table.style = 'Table Grid'
            m_hdrs = ['TT', 'Chủ đề Chương', 'Nội dung kiến thức', 'Nhiều lựa chọn (NB/TH/VD)', 'Đúng - Sai (NB/TH/VD)', 'Trả lời ngắn (NB/TH)', 'Tự luận (NB/TH/VD/VDC)', 'Tổng %']
            for idx, h in enumerate(m_hdrs): 
                m_table.rows[0].cells[idx].text = h
                m_table.rows[0].cells[idx].paragraphs[0].runs[0].font.bold = True
            for item in data['ma_tran']:
                row = m_table.add_row().cells
                row[0].text = str(item.get('tt', '1'))
                row[1].text = str(item.get('chu_de', ''))
                row[2].text = str(item.get('noi_dung', ''))
                nlc, ds, tln, tl = item.get('nhieu_lua_chon',{}), item.get('dung_sai',{}), item.get('tra_loi_ngan',{}), item.get('tu_luan',{})
                row[3].text = f"{nlc.get('nb',0)}/{nlc.get('th',0)}/{nlc.get('vd',0)}"
                row[4].text = f"{ds.get('nb',0)}/{ds.get('th',0)}/{ds.get('vd',0)}"
                row[5].text = f"{tln.get('nb',0)}/{tln.get('th',0)}"
                row[6].text = f"{tl.get('nb',0)}/{tl.get('th',0)}/{tl.get('vd',0)}/{tl.get('vdc',0)}"
                row[7].text = f"{item.get('tong_diem_phan_tram', 10)}%"
        elif 'ma_tran' in data:
            # Tách rõ TN và TL cho từng mức độ tư duy
            m_table = doc.add_table(rows=1, cols=6)
            m_table.style = 'Table Grid'
            m_hdrs = ['Nội dung kiến thức', 'Hình thức', 'Nhận biết', 'Thông hiểu', 'Vận dụng', 'Vận dụng cao']
            
            for idx, h in enumerate(m_hdrs): 
                m_table.rows[0].cells[idx].text = h
                m_table.rows[0].cells[idx].paragraphs[0].runs[0].font.bold = True
                
            for item in data['ma_tran']:
                chu_de_text = f"{item.get('chu_de', '')} - {item.get('noi_dung', '')}"
                
                nlc = item.get('nhieu_lua_chon', {})
                ds = item.get('dung_sai', {})
                tln = item.get('tra_loi_ngan', {})
                tl = item.get('tu_luan', {})
                
                # 1. Tính tổng số câu Trắc nghiệm (gồm Nhiều lựa chọn + Đúng sai + Trả lời ngắn)
                tn_nb = nlc.get('nb', 0) + ds.get('nb', 0) + tln.get('nb', 0)
                tn_th = nlc.get('th', 0) + ds.get('th', 0) + tln.get('th', 0)
                tn_vd = nlc.get('vd', 0) + ds.get('vd', 0)
                tn_vdc = 0  # Trắc nghiệm thường không cấu hình VDC theo form của bạn
                
                # 2. Tính tổng số câu Tự luận
                tl_nb = tl.get('nb', 0)
                tl_th = tl.get('th', 0)
                tl_vd = tl.get('vd', 0)
                tl_vdc = tl.get('vdc', 0)
                
                # Hàng dành cho Trắc nghiệm (TN)
                row_tn = m_table.add_row().cells
                row_tn[0].text = chu_de_text
                row_tn[1].text = "Trắc nghiệm (TN)"
                row_tn[2].text = f"{tn_nb} câu" if tn_nb > 0 else "-"
                row_tn[3].text = f"{tn_th} câu" if tn_th > 0 else "-"
                row_tn[4].text = f"{tn_vd} câu" if tn_vd > 0 else "-"
                row_tn[5].text = f"{tn_vdc} câu" if tn_vdc > 0 else "-"
                
                # Hàng dành cho Tự luận (TL)
                row_tl = m_table.add_row().cells
                row_tl[0].text = ""  # Để trống tên chủ đề để tránh lặp chữ, nhìn bảng sẽ gọn hơn
                row_tl[1].text = "Tự luận (TL)"
                row_tl[2].text = f"{tl_nb} câu" if tl_nb > 0 else "-"
                row_tl[3].text = f"{tl_th} câu" if tl_th > 0 else "-"
                row_tl[4].text = f"{tl_vd} câu" if tl_vd > 0 else "-"
                row_tl[5].text = f"{tl_vdc} câu" if tl_vdc > 0 else "-"

        # Tầng 2: Vẽ Bản Đặc Tả (Cả hai dạng đề đều được chèn vào đây)
        if 'bang_dac_ta' in data and data['bang_dac_ta']:
            doc.add_paragraph()
            doc.add_heading("II. BẢN ĐẶC TẢ CHI TIẾT ĐỀ KIỂM TRA", level=2)
            s_table = doc.add_table(rows=1, cols=6)
            s_table.style = 'Table Grid'
            s_hdrs = ['Mã ĐT', 'Chủ đề / Kiến thức', 'Mức độ đánh giá', 'Yêu cầu cần đạt', 'Số câu hỏi', 'Điểm số']
            for idx, h in enumerate(s_hdrs):
                s_table.rows[0].cells[idx].text = h
                s_table.rows[0].cells[idx].paragraphs[0].runs[0].font.bold = True
            for item in data['bang_dac_ta']:
                row = s_table.add_row().cells
                row[0].text = str(item.get('id_dac_ta', ''))
                row[1].text = f"{item.get('chu_de','')}\n- {item.get('noi_dung','')}"
                row[2].text = str(item.get('muc_do', ''))
                row[3].text = str(item.get('yeu_cau_can_dat', ''))
                row[4].text = str(item.get('so_cau', ''))
                row[5].text = str(item.get('diem', ''))
        doc.add_paragraph()

    doc.add_heading("III. NỘI DUNG CÂU HỎI ĐỀ THI", level=2)
    de = data.get('de_kiem_tra', {})
    
    list_4lc = de.get("trac_nghiem_4_lua_chon", [])
    if list_4lc:
        doc.add_paragraph().add_run(f"PHẦN I. Câu trắc nghiệm nhiều phương án lựa chọn ({config.get('score_part1', 3.0)} điểm).").bold = True
        for q in list_4lc:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))
            p_opts = doc.add_paragraph()
            p_opts.paragraph_format.left_indent = Inches(0.3)
            p_opts.add_run("A. ").bold = True; add_math_run_to_paragraph(p_opts, q.get('A', ''))
            p_opts.add_run("   B. ").bold = True; add_math_run_to_paragraph(p_opts, q.get('B', ''))
            p_opts.add_run("   C. ").bold = True; add_math_run_to_paragraph(p_opts, q.get('C', ''))
            p_opts.add_run("   D. ").bold = True; add_math_run_to_paragraph(p_opts, q.get('D', ''))

    list_ds = de.get("trac_nghiem_dung_sai", [])
    if list_ds:
        doc.add_paragraph().add_run(f"\nPHẦN II. Câu trắc nghiệm đúng sai ({config.get('score_part2', 4.0)} điểm).").bold = True
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
        doc.add_paragraph().add_run(f"\nPHẦN III. Câu trắc nghiệm trả lời ngắn ({config.get('score_part3', 3.0)} điểm).").bold = True
        for q in list_tln:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))

    list_tl = de.get("tu_luan", [])
    if list_tl:
        doc.add_paragraph().add_run(f"\nPHẦN IV. Tự luận ({config.get('score_part4', 0.0)} điểm).").bold = True
        for q in list_tl:
            p_q = doc.add_paragraph()
            p_q.add_run(f"Câu {q.get('id', '')}: ").bold = True
            add_math_run_to_paragraph(p_q, q.get('cau_hoi', ''))

    doc.add_page_break()
    doc.add_paragraph().add_run(f"HƯỚNG DẪN CHẤM & ĐÁP ÁN CHI TIẾT - MÃ ĐỀ: {code_label}\n").bold = True
    da = data.get('dap_an_chi_tiet', {})
    
    if da.get('trac_nghiem_4_lua_chon'):
        doc.add_paragraph().add_run("Đáp án Phần I (Trắc nghiệm nhiều lựa chọn):").bold = True
        ans_table1 = doc.add_table(rows=1, cols=2)
        ans_table1.style = 'Table Grid'
        ans_table1.rows[0].cells[0].text = "Câu hỏi"
        ans_table1.rows[0].cells[1].text = "Đáp án mã hóa"
        for q_id, val in da['trac_nghiem_4_lua_chon'].items():
            rc = ans_table1.add_row().cells
            rc[0].text = f"Câu {q_id}"
            rc[1].text = str(val)

    if da.get('trac_nghiem_dung_sai'):
        doc.add_paragraph().add_run("\nĐáp án Phần II (Đúng / Sai):").bold = True
        ans_table2 = doc.add_table(rows=1, cols=5)
        ans_table2.style = 'Table Grid'
        ans_table2.rows[0].cells[0].text = "Câu hỏi"
        for idx, k in enumerate(['a','b','c','d']): ans_table2.rows[0].cells[idx+1].text = f"Ý {k}"
        for q_id, y_dict in da['trac_nghiem_dung_sai'].items():
            rc = ans_table2.add_row().cells
            rc[0].text = f"Câu {q_id}"
            if isinstance(y_dict, dict):
                for idx, k in enumerate(['a','b','c','d']): rc[idx+1].text = str(y_dict.get(k, ''))

    if da.get('trac_nghiem_tra_loi_ngan'):
        doc.add_paragraph().add_run("\nĐáp án Phần III (Trả lời ngắn):").bold = True
        for q_id, val in da['trac_nghiem_tra_loi_ngan'].items():
            doc.add_paragraph(f"Câu {q_id}: Tập số kết quả = {val}")

    if da.get('tu_luan'):
        doc.add_paragraph().add_run("\nHướng dẫn chi tiết Phần IV (Tự luận):").bold = True
        for q_id, detail in da['tu_luan'].items() if isinstance(da['tu_luan'], dict) else enumerate(da['tu_luan']):
            p_tl = doc.add_paragraph()
            p_tl.add_run(f"Câu {q_id}: ").bold = True
            add_math_run_to_paragraph(p_tl, str(detail))
            
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# ==========================================
# GIAO DIỆN STREAMLIT
# ==========================================
st.markdown('<div class="main-title">Trợ Lý Ra Đề Kiểm Tra (Quy trình 3 Bước Chuẩn Giáo Dục)</div>', unsafe_allow_html=True)

if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng cấu hình Google Gemini API Key tại Trang chủ trước.")
    st.stop()

model = genai.GenerativeModel('gemini-2.5-flash')

tab1, tab2, tab3 = st.tabs(["📋 Bước 1: Cấu hình & Lập Ma Trận", "📊 Bước 2: Thiết kế Bản Đặc Tả", "🔥 Bước 3: Tạo Đề Thi & Đảo Đề"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-header">Thông tin tổng quan bộ môn</div>', unsafe_allow_html=True)
        subject = st.selectbox("Chọn môn học:", list(SUBJECTS_CONFIG.keys()))
        grade = st.selectbox("Khối lớp:", [str(i) for i in range(1, 13)], index=7)
        exam_type = st.selectbox("Hình thức thi:", ["15 phút", "45 phút", "Giữa học kỳ I", "Cuối học kỳ I", "Giữa học kỳ II", "Cuối học kỳ II"])
        duration = st.number_input("Thời lượng (phút):", min_value=15, max_value=150, value=15, step=5)
        school_year = st.text_input("Năm học:", value="2026-2027")
        matrix_template = st.radio("Mẫu khung ma trận hiển thị:", ["Mẫu đơn giản truyền thống", "Mẫu quy chuẩn Công văn 7991/BGDĐT-GDTrH"], index=0)

    with col2:
        st.markdown('<div class="section-header">Cấu hình số lượng câu hỏi</div>', unsafe_allow_html=True)
        num_tn_4_lua_chon = st.number_input("Trắc nghiệm nhiều lựa chọn (Phần I):", value=12)
        num_tn_dung_sai = st.number_input("Trắc nghiệm Đúng/Sai (Phần II):", value=2, help="Mỗi câu có 4 ý")
        num_tn_tra_loi_ngan = st.number_input("Trắc nghiệm Trả lời ngắn (Phần III):", value=4)
        num_tl = st.number_input("Số câu hỏi Tự luận (Phần IV):", value=4)
        
        st.markdown('---')
        code_choice = st.selectbox("Số lượng mã đề đảo:", [1, 2, 4, 6, 8], index=2)
        num_codes = int(code_choice)
        code_prefix = st.text_input("Ký hiệu mã đề bắt đầu:", value="101")

    st.markdown('<div class="section-header">Nguồn nội dung & Điểm số</div>', unsafe_allow_html=True)
    content_source = st.radio("Phương thức nhập nội dung:", ["Nhập tay danh sách chủ đề", "Upload file tài liệu chứa chủ đề cần kiểm tra"], horizontal=True)
    
    if content_source == "Nhập tay danh sách chủ đề":
        topics_list = st.text_area("Danh sách chủ đề kiến thức cần kiểm tra:", value="Chương 1: Khái niệm cơ bản\nChương 2: Bài toán vận dụng liên quan", height=100)
        st.session_state.current_document_content = topics_list
    else:
        uploaded_doc = st.file_uploader("Tải lên tài liệu giảng dạy:", type=["docx", "txt", "pdf", "png", "jpg", "jpeg"])
        if uploaded_doc is not None:
            file_bytes = uploaded_doc.read()
            file_ext = uploaded_doc.name.split('.')[-1].lower()
            if file_ext == "txt": st.session_state.current_document_content = str(file_bytes, "utf-8")
            elif file_ext == "docx": st.session_state.current_document_content = extract_text_from_docx(file_bytes)
            elif file_ext == "pdf": st.session_state.current_document_content = {"mime_type": "application/pdf", "data": file_bytes}
            elif file_ext in ["png", "jpg", "jpeg"]: st.session_state.current_document_content = {"mime_type": f"image/{file_ext}", "data": file_bytes}

    c_s1, c_s2, c_s3, c_s4, c_vdc = st.columns(5)
    with c_s1: score_part1 = st.number_input("Điểm Phần I (Nhiều LC):", min_value=0.0, max_value=10.0, value=3.0, step=0.25)
    with c_s2: score_part2 = st.number_input("Điểm Phần II (Đúng/Sai):", min_value=0.0, max_value=10.0, value=2.0, step=0.25)
    with c_s3: score_part3 = st.number_input("Điểm Phần III (Trả lời ngắn):", min_value=0.0, max_value=10.0, value=2.0, step=0.25)
    with c_s4: score_part4 = st.number_input("Điểm Phần IV (Tự luận):", min_value=0.0, max_value=10.0, value=3.0, step=0.25)
    with c_vdc: score_vdc_custom = st.number_input("Điểm dành riêng cho VDC:", min_value=0.0, max_value=10.0, value=0.5, step=0.25, help="Chỉnh tăng lên cho lớp chọn hoặc giảm về 0 cho HS trung bình.")

    total_score = score_part1 + score_part2 + score_part3 + score_part4
    
    # Logic kiểm tra lỗi điểm số vượt quá hoặc không đạt 10 điểm
    if total_score > 10.0:
        st.error(f"❌ LỖI CẤU HÌNH ĐIỂM: Tổng số điểm hiện tại là **{total_score}** điểm, vượt quá giới hạn cho phép (Tối đa 10 điểm). Vui lòng điều chỉnh lại!")
        score_error = True
    elif total_score < 10.0:
        st.warning(f"⚠️ Tổng số điểm hiện tại là **{total_score}** điểm. Đề kiểm tra chuẩn cần đạt chính xác **10.0** điểm.")
        score_error = False
    else:
        st.success("✅ Cấu hình điểm số chính xác đạt 10/10 điểm chuẩn.")
        score_error = False
    st.markdown('**Phân bổ Tỷ lệ Ma trận tư duy (%)**')
    cl1, cl2, cl3, cl4 = st.columns(4)
    with cl1: nb_ratio = st.slider("Nhận biết", 0, 100, 40)
    with cl2: th_ratio = st.slider("Thông hiểu", 0, 100, 30)
    with cl3: vd_ratio = st.slider("Vận dụng", 0, 100, 20)
    with cl4: vdc_ratio = st.slider("Vận dụng cao", 0, 100, 10)

    config_pkg = {
        "subject": subject, "grade": grade, "num_tn_4_lua_chon": num_tn_4_lua_chon, 
        "num_tn_dung_sai": num_tn_dung_sai, "num_tn_tra_loi_ngan": num_tn_tra_loi_ngan, "num_tl": num_tl,
        "score_part1": score_part1, "score_part2": score_part2, "score_part3": score_part3, "score_part4": score_part4,
        "score_vdc_custom": score_vdc_custom, "nb_ratio": nb_ratio, "th_ratio": th_ratio, "vd_ratio": vd_ratio, "vdc_ratio": vdc_ratio,
        "matrix_template": matrix_template, "exam_type": exam_type, "duration": duration, "school_year": school_year
    }

    if st.button("📊 BƯỚC 1: KHỞI TẠO MA TRẬN PHÂN BỔ"):
        if not st.session_state.current_document_content:
            st.error("Vui lòng nhập chủ đề hoặc upload tài liệu trước.")
        else:
            with st.spinner("Hệ thống đang lập bảng ma trận kiến thức định lượng..."):
                try:
                    st.session_state.step1_matrix = generate_step1_matrix_only(model, config_pkg, st.session_state.current_document_content)
                    st.success("🎉 Đã tạo bảng Ma trận thành công! Vui lòng chuyển sang tab 'Bước 2'.")
                except Exception as e:
                    st.error(f"Lỗi khởi tạo ma trận: {e}")
                    
    if st.session_state.step1_matrix:
        st.markdown('<div class="step-active">**Dữ liệu Ma trận đã nạp thành công!**</div>', unsafe_allow_html=True)
        st.json(st.session_state.step1_matrix)

with tab2:
    st.markdown('<div class="section-header">Thiết kế Bản đặc tả từ Ma trận</div>', unsafe_allow_html=True)
    if not st.session_state.step1_matrix:
        st.info("Trạng thái: Chờ dữ liệu từ Bước 1. Thầy cô vui lòng chạy Bước 1 ở tab bên cạnh trước.")
    else:
        if st.button("📝 BƯỚC 2: TỰ ĐỘNG LẬP BẢN ĐẶC TẢ CHI TIẾT"):
            with st.spinner("AI đang xây dựng ma trận tiêu chí đánh giá và yêu cầu cần đạt..."):
                try:
                    st.session_state.step2_spec = generate_step2_spec_only(model, config_pkg, st.session_state.step1_matrix)
                    st.success("🎉 Đã lập Bản đặc tả năng lực thành công! Vui lòng chuyển sang tab 'Bước 3'.")
                except Exception as e:
                    st.error(f"Lỗi khởi tạo bản đặc tả: {e}")
                    
    if st.session_state.step2_spec:
        st.markdown('<div class="step-active">**Dữ liệu Bản đặc tả đã nạp thành công!**</div>', unsafe_allow_html=True)
        st.json(st.session_state.step2_spec)

with tab3:
    st.markdown('<div class="section-header">Tạo Đề bài & Đóng gói Đề thi</div>', unsafe_allow_html=True)
    if not st.session_state.step2_spec:
        st.info("Trạng thái: Chờ dữ liệu Bản đặc tả từ Bước 2.")
    else:
        if st.button("🔥 THỰC HIỆN BƯỚC 3: SINH CÂU HỎI THI & ĐẢO ĐỀ TỰ ĐỘNG"):
            with st.spinner("Đang bám sát Ma trận và Đặc tả để viết câu hỏi (Hệ thống tự động lọc bỏ Latex)..."):
                try:
                    rule = SUBJECTS_CONFIG[subject]
                    step3_data = generate_step3_questions(model, config_pkg, st.session_state.step1_matrix, st.session_state.step2_spec, rule, st.session_state.current_document_content)
                    
                    # Hợp nhất toàn bộ dữ liệu cấu trúc
                    full_data = {
                        "ma_tran": st.session_state.step1_matrix["ma_tran"],
                        "bang_dac_ta": st.session_state.step2_spec["bang_dac_ta"],
                        "de_kiem_tra": step3_data["de_kiem_tra"],
                        "dap_an_chi_tiet": step3_data["dap_an_chi_tiet"]
                    }
                    
                    try: s_code = int(code_prefix)
                    except: s_code = 101
                    
                    bundle, alignment_df = generate_shuffled_bundle(full_data, s_code, num_codes)
                    bundle["ĐỀ GỐC"] = full_data
                    st.session_state.multi_codes_data = bundle
                    st.session_state.alignment_table = alignment_df
                    st.success(f"🎉 Xuất sắc! Hệ thống đã tạo xong ĐỀ GỐC cùng {num_codes} mã đề đảo.")
                except Exception as e:
                    st.error(f"Lỗi sinh câu hỏi: {e}")

    if st.session_state.multi_codes_data:
        st.markdown('---')
        inc_mat = st.checkbox("Chèn bảng Ma trận & Đặc tả vào đầu tệp văn bản", value=True)
        export_mode = st.radio("Định dạng tải tệp bộ đề:", ["Tải file bản đề đơn lẻ", "Nén toàn bộ mã đề vào file ZIP", "Gộp chung tất cả vào một file Word"])
        
        if export_mode == "Tải file bản đề đơn lẻ":
            all_codes = list(st.session_state.multi_codes_data.keys())
            if "ĐỀ GỐC" in all_codes: all_codes.remove("ĐỀ GỐC"); all_codes = ["ĐỀ GỐC"] + all_codes
            sel_code = st.selectbox("Chọn tệp đề cần tải:", all_codes)
            docx_buf = build_single_docx(config_pkg, st.session_state.multi_codes_data[sel_code], sel_code, include_matrix=inc_mat)
            st.download_button(label=f"📥 TẢI FILE WORD MÃ ĐỀ [{sel_code}]", data=docx_buf, file_name=f"De_{subject}_{sel_code}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            
        elif export_mode == "Nén toàn bộ mã đề vào file ZIP":
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for c_code, c_data in st.session_state.multi_codes_data.items():
                    d_buf = build_single_docx(config_pkg, c_data, c_code, include_matrix=inc_mat)
                    filename = f"De_Goc_{subject}_Lop{grade}.docx" if c_code == "ĐỀ GỐC" else f"De_{subject}_Lop{grade}_MaDe_{c_code}.docx"
                    zip_file.writestr(filename, d_buf.getvalue())
            zip_buffer.seek(0)
            st.download_button(label="📥 TẢI FILE NÉN ZIP TRỌN BỘ", data=zip_buffer, file_name=f"Bo_De_{subject}_TronGoi.zip", mime="application/zip")
            
        else:
            main_doc = Document()
            all_codes = list(st.session_state.multi_codes_data.keys())
            if "ĐỀ GỐC" in all_codes: all_codes.remove("ĐỀ GỐC"); all_codes = ["ĐỀ GỐC"] + all_codes
            for idx, c_code in enumerate(all_codes):
                c_data = st.session_state.multi_codes_data[c_code]
                temp_buf = build_single_docx(config_pkg, c_data, c_code, include_matrix=inc_mat)
                t_doc = Document(temp_buf)
                for element in t_doc.element.body: main_doc.element.body.append(element)
                if idx < len(all_codes) - 1: main_doc.add_page_break()
                
            all_buf = BytesIO()
            main_doc.save(all_buf)
            all_buf.seek(0)
            st.download_button(label="📥 TẢI FILE WORD GỘP TOÀN BỘ", data=all_buf, file_name=f"Gop_Bo_De_{subject}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

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
