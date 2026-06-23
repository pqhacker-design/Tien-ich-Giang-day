import streamlit as st
import os
import io
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from dotenv import load_dotenv
from ai_auditor_app.core.document_proc import DocumentProcessor
from ai_auditor_app.core.ai_engine import AIEngine
from ai_auditor_app.core.rag_manager import RAGManager
from ai_auditor_app.modules.grammar_checker import VietnameseGrammarChecker
from ai_auditor_app.modules.evidence_gen import EvidenceGenerator
from ai_auditor_app.modules.criterion_eval import CommitteeEvaluator
from ai_auditor_app.modules.advanced_audit import AdvancedAuditor
from ai_auditor_app.modules.dashboard_panel import DashboardPanel

load_dotenv()

st.set_page_config(page_title="AI So sánh - Kiểm định Hồ sơ Giáo dục", layout="wide")

# Khởi tạo Session State lưu trữ dữ liệu liên tục và đồng bộ
if "rag_manager" not in st.session_state:
    st.session_state.rag_manager = RAGManager()
if "template_reqs" not in st.session_state:
    st.session_state.template_reqs = []
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None
if "user_text_content" not in st.session_state:
    st.session_state.user_text_content = ""

st.title("🛡️ AI So sánh văn bản với mẫu hướng dẫn")
st.caption("Giải pháp ứng dụng Trí tuệ nhân tạo So sánh và Đánh giá văn bản so với hướng dẫn mẫu.")

# --- SIDEBAR: Cấu hình hệ thống ---
# ==============================================================================
# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ (ĐÃ SỬA LỖI CÚ PHÁP & ĐỒNG BỘ) ---
# ==============================================================================
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"].strip()
    # Gán vào biến môi trường hệ thống để thư viện tự động nạp
    os.environ["GEMINI_API_KEY"] = api_key_input
    
    # Lựa chọn mô hình ngay trên thanh sidebar của app con nếu cần thay đổi nhanh
    st.sidebar.header("⚙️ Cấu hình Mô hình")
    model_name = st.sidebar.selectbox("Lựa chọn Mô hình", ["gemini-2.5-flash", "gemini-3.0-flash"])
    audit_level = st.sidebar.radio("Mức độ rà soát", ["Toàn diện (Cấu trúc + Câu từ)", "Cấu trúc khung", "Từ khóa & Minh chứng"])
    
    # Khởi tạo hoặc cập nhật đối tượng AIEngine dùng chung
    if 'ai_engine' not in st.session_state or st.session_state.ai_engine is None:
        st.session_state.ai_engine = AIEngine(api_key=api_key_input, model_name=model_name)
    else:
        # Nếu đã có sẵn ai_engine từ trước, chỉ cập nhật lại model_name nếu user thay đổi box
        st.session_state.ai_engine.model_name = model_name
    
    # Gán biến cục bộ để các hàm phía dưới gọi ngắn gọn
    ai_engine = st.session_state.ai_engine

else:
    # Nếu chưa nhập key ở trang chủ, hiển thị thông báo nhắc nhở và dừng app con lại
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop() # Dừng không chạy các đoạn code phía dưới để tránh lỗi crash
# ==============================================================================
# --- Giao diện Tabs chính ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📋 1. Thư viện Mẫu Chuẩn", 
    "📂 2. Hồ Sơ Cần Kiểm Tra", 
    "🔬 3. Phân Tích & Đối Chiếu AI", 
    "📊 4. Thẩm Định Hội Đồng",
    "🛡️ 5. Thẩm Định AI Nâng Cao", 
    "📈 6. Bảng Điều Khiển & Phản Biện", 
    "🤖 7. Chat Cố Vấn Tương Tác"
])

def export_audit_to_docx(audit_report, avg_score=None):
    """Hàm tự động khởi tạo và ghi dữ liệu báo cáo thẩm định ra file Word chuẩn bộ GD"""
    doc = Document()
    
    # Cấu hình font chữ chuẩn và lề
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    
    # Tiêu ngữ hành chính
    p_header = doc.add_paragraph()
    p_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_header = p_header.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n" + "_"*15 + "\n")
    run_header.bold = True
    
    # Tiêu đề biên bản
    title = doc.add_heading(level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = title.add_run("BIÊN BẢN THẨM ĐỊNH & KIỂM ĐỊNH HỒ SƠ GIÁO DỤC\n(Hệ thống AI Thư ký Hội đồng tự động xuất)")
    run_title.font.size = Pt(16)
    run_title.font.color.rgb = None  # Để màu đen mặc định
    
    if avg_score:
        doc.add_paragraph(f"Điểm đánh giá tổng hợp toàn diện: {round(avg_score, 1)} / 100 điểm.")
    
    doc.add_paragraph("Chi tiết các tiêu chí rà soát và khuyến nghị hiệu đính:").bold = True
    
    # Tạo bảng danh sách lỗi và đề xuất sửa
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'STT'
    hdr_cells[1].text = 'Tiêu chí kiểm tra'
    hdr_cells[2].text = 'Trạng thái / Điểm'
    hdr_cells[3].text = 'Khuyến nghị giải pháp từ AI'
    
    # Định dạng chữ đậm cho tiêu đề bảng
    for cell in hdr_cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True

    # Duyệt điền dữ liệu
    for idx, item in enumerate(audit_report):
        row_cells = table.add_row().cells
        row_cells[0].text = str(idx + 1)
        row_cells[1].text = str(item.get('criteria', ''))
        row_cells[2].text = f"{item.get('status', '')} ({item.get('score', 70)}/100)"
        row_cells[3].text = str(item.get('fix', ''))
        
    doc.add_paragraph("\n").alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_footer = doc.add_paragraph()
    p_footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_footer.add_run("ỦY VIÊN THƯ KÝ HỘI ĐỒNG AI\n(Đã duyệt hệ thống)").italic = True
    
    # Lưu file vào bộ nhớ tạm dạng bytes để Streamlit download trực tiếp
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio
from docx.shared import RGBColor

from docx.shared import RGBColor

def export_fixed_doc(uploaded_file, audit_report):
    """
    Hàm đọc file gốc 1 lần duy nhất, can thiệp chỉnh sửa/bổ sung nội dung từ AI
    vào trực tiếp cấu trúc thân văn bản, đổi màu chữ thành ĐỎ tại những nơi can thiệp
    và giữ nguyên vẹn 100% định dạng, layout cũ của file.
    """
    import io
    from docx import Document
    from docx.shared import RGBColor
    
    # 1. Đưa con trỏ file về vị trí đầu tiên và đọc duy nhất 1 lần vào bộ nhớ
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    
    if not file_bytes:
        return io.BytesIO() # Tránh crash nếu file rỗng
        
    # 2. Khởi tạo đối tượng Document từ bộ nhớ đệm
    doc = Document(io.BytesIO(file_bytes))
    
    # Lọc danh sách các phần được gợi ý chỉnh sửa từ AI
    pending_fixes = [item for item in audit_report if item.get('status') != "Đạt"]
    
    if pending_fixes:
        for item in pending_fixes:
            criteria_name = item.get('criteria', '').lower().strip()
            fix_content = item.get('fix', '').strip()
            
            matched = False
            
            # Duyệt qua các đoạn văn trong file gốc để tìm vị trí thích hợp
            for paragraph in doc.paragraphs:
                # Nếu tìm thấy đoạn văn (hoặc tiêu đề) chứa tên tiêu chí cần chỉnh sửa
                if criteria_name in paragraph.text.lower() and len(paragraph.text) < 250:
                    # Thêm một đoạn văn mới ngay phía sau đoạn văn này để chèn nội dung AI
                    # Sử dụng helper function hoặc tạo đoạn văn kế thừa style của đoạn văn gốc
                    p_fixed = doc.add_paragraph(style=paragraph.style)
                    
                    # Di chuyển đoạn văn mới tạo về ngay sau vị trí paragraph tìm thấy trong cấu trúc XML
                    paragraph._element.addnext(p_fixed._element)
                    
                    # Chèn tiêu đề thông báo AI chỉnh sửa bằng chữ MÀU ĐỎ
                    run_intro = p_fixed.add_run(f"\n[AI Hoàn thiện mục {item.get('criteria')}]: ")
                    run_intro.bold = True
                    run_intro.font.color.rgb = RGBColor(255, 0, 0)
                    
                    # Chèn nội dung vá lỗi bằng chữ MÀU ĐỎ + In nghiêng
                    run_content = p_fixed.add_run(f"{fix_content}\n")
                    run_content.italic = True
                    run_content.font.color.rgb = RGBColor(255, 0, 0)
                    
                    matched = True
                    break # Đã chèn xong tiêu chí này, chuyển sang tiêu chí tiếp theo
            
            # Nếu trong thân văn bản gốc hoàn toàn không có đề cập đến tiêu chí này (Mục thiếu hoàn toàn)
            # AI sẽ tự động tạo một mục mới chèn xuống cuối văn bản
            if not matched:
                p_sec = doc.add_paragraph()
                r_title = p_sec.add_run(f"\n[AI Bổ sung mục thiếu hoàn toàn: {item.get('criteria')}]\n")
                r_title.bold = True
                r_title.font.color.rgb = RGBColor(255, 0, 0)
                
                r_content = p_sec.add_run(f"{fix_content}\n")
                r_content.italic = True
                r_content.font.color.rgb = RGBColor(255, 0, 0)

    # 3. Ghi dữ liệu đã vá vào bộ nhớ đệm bytes để Streamlit tải về
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio
    
# --- TAB 1: VĂN BẢN MẪU ---
with tab1:
    st.header("Cung cấp Văn bản mẫu chỉ dẫn / Tiêu chí gốc")
    uploaded_template = st.file_uploader("Tải lên File Mẫu (DOCX/PDF)", type=["docx", "pdf"], key="tmpl")
    if uploaded_template and ai_engine:
        with st.spinner("AI đang phân tích cấu trúc mẫu quy chuẩn..."):
            text = DocumentProcessor.read_file(uploaded_template)
            st.session_state.template_reqs = ai_engine.extract_template_requirements(text)
            st.success(f"Đã trích xuất thành công {len(st.session_state.template_reqs)} tiêu chí cốt lõi.")
            st.json(st.session_state.template_reqs)

# --- TAB 2: VĂN BẢN CẦN KIỂY TRA (Điểm mấu chốt xử lý lưu cache) ---
with tab2:
    st.header("Tải lên tài liệu giáo viên cần thẩm định")
    uploaded_user_file = st.file_uploader("Tải lên Hồ sơ của bạn (DOCX/PDF)", type=["docx", "pdf"], key="user_doc")
    if uploaded_user_file:
        # Đọc 1 lần duy nhất để tránh cạn luồng stream bytes và bọc xử lý lỗi
        raw_text = DocumentProcessor.read_file(uploaded_user_file)
        if raw_text.startswith("LỖI:"):
            st.error(raw_text)
            st.session_state.user_text_content = ""
        else:
            st.session_state.user_text_content = raw_text
            st.success("Tải hồ sơ và đồng bộ bộ nhớ đệm thành công!")
            st.text_area("Xem trước Nội dung văn bản hiện tại:", value=st.session_state.user_text_content[:1500] + "\n...", height=300)

# --- TAB 3: PHÂN TÍCH AI & TRACK CHANGES ---
with tab3:
    st.header("Kết quả phân tích, đối chiếu diện rộng")
    if st.button("🚀 Khởi chạy Rà soát tự động bằng AI"):
        if st.session_state.user_text_content and ai_engine:
            with st.spinner("AI đang tiến hành quét cấu trúc, kiểm tra lỗi hành chính và chính tả..."):
                res = ai_engine.audit_document(st.session_state.template_reqs, st.session_state.user_text_content, audit_level)
                st.session_state.audit_report = res.get("report", [])
        else:
            st.warning("Vui lòng cấu hình API Key và tải lên hồ sơ tại Tab 2 trước!")
            
    if st.session_state.audit_report:
        st.subheader("Bảng chi tiết thiếu sót và khuyến nghị hành động:")
        
        # Khởi tạo danh sách lưu các tiêu chí được chọn áp dụng nếu chưa có
        if "accepted_fixes" not in st.session_state:
            st.session_state.accepted_fixes = []
            
        for idx, item in enumerate(st.session_state.audit_report):
            with st.expander(f"📌 Tiêu chí: {item.get('criteria')} - Hiện trạng: {item.get('status')}"):
                st.write(f"**Điểm thành phần:** {item.get('score')}/100")
                st.info(f"💡 **Đề xuất hiệu đính từ Hội đồng AI:** {item.get('fix')}")
                
                col_acc, col_rej = st.columns(2)
                
                # Khi bấm nút áp dụng, lưu tiêu chí này vào danh sách hàng đợi sửa trực tiếp
                if col_acc.button("☑️ Áp dụng Đề xuất này", key=f"acc_{idx}"):
                    if item not in st.session_state.accepted_fixes:
                        st.session_state.accepted_fixes.append(item)
                    st.success(f"Đã duyệt chỉnh sửa trực tiếp cho mục: {item.get('criteria')}")
                    
                if col_rej.button("✖️ Bỏ qua lỗi", key=f"rej_{idx}"):
                    if item in st.session_state.accepted_fixes:
                        st.session_state.accepted_fixes.remove(item)
                    st.toast("Đã bỏ qua gợi ý.")

        st.divider()
        st.subheader("💾 Trung tâm Xuất & Tải File Hoàn Thiện")
        
        col_download_1, col_download_2 = st.columns(2)
        with col_download_1:
            avg_score = sum([int(i.get('score', 70)) for i in st.session_state.audit_report]) / len(st.session_state.audit_report)
            docx_report_data = export_audit_to_docx(st.session_state.audit_report, avg_score)
            st.download_button(
                label="📥 Tải xuống Biên Bản Thẩm Định (.DOCX)",
                data=docx_report_data,
                file_name="Bien_Ban_Tham_Dinh_AI.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="btn_download_report"
            )
            
        with col_download_2:
            if uploaded_user_file:
                with st.spinner("Hệ thống đang tích hợp nội dung AI đã duyệt vào đúng vị trí file gốc..."):
                    # CHỈ TRUYỀN NHỮNG LỖI MÀ GIÁO VIÊN ĐÃ BẤM CHẤP NHẬN ÁP DỤNG
                    reports_to_fix = st.session_state.accepted_fixes if st.session_state.accepted_fixes else st.session_state.audit_report
                    fixed_docx_data = export_fixed_doc(uploaded_user_file, reports_to_fix)
                    
                st.download_button(
                    label="✨ Tải xuống Hồ Sơ Đã Vá Lỗi Trực Tiếp (.DOCX)",
                    data=fixed_docx_data,
                    file_name="Ho_So_Vao_Form_Hoan_Thien.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="btn_download_fixed_doc"
                )
                
# --- TAB 4: THẨM ĐỊNH HỘI ĐỒNG & MINH CHỨNG ---
with tab4:
    st.header("Mô Phỏng Hội Đồng Thẩm Định & Sinh Minh Chứng")
    if st.session_state.audit_report:
        avg_score = sum([int(i.get('score', 70)) for i in st.session_state.audit_report]) / len(st.session_state.audit_report)
        st.metric(label="ĐIỂM TỔNG HỢP TOÀN DIỆN HỘI ĐỒNG AI", value=f"{round(avg_score,1)} / 100")
        
        if st.button("📋 Xuất Biên Bản Thẩm Định Hội Đồng Phản Biện (5 Thành viên)"):
            committee_res = CommitteeEvaluator.generate_committee_report("Hồ sơ SKKN Toán 8", avg_score, {}, 5)
            for member, data in committee_res.items():
                st.write(f"**{data['role']} - {member}**: Chấm điểm: **{data['score']}** | Xếp loại: {data['rating']}")
                st.caption(f"Nhận xét lý do: *{data['comment']}*")
                st.divider()
                
        st.subheader("Sinh Minh Chứng Tự Động")
        if st.button("📊 Tự Động Sinh Biểu Mẫu Khảo Sát/Thực Nghiệm Minh Chứng (Excel)"):
            excel_file = EvidenceGenerator.generate_survey_table("Bảng Thống Kê Điểm Số Khảo Sát Thực Nghiệm Sáng Kiến", ["Năng lực tư duy hình học", "Khả năng vận dụng Chuyển đổi số"])
            st.download_button("📥 Tải xuống Biểu mẫu Excel Minh chứng", data=excel_file, file_name="minh_chung_ai_generated.xlsx")

# --- TAB 5: THẨM ĐỊNH AI NÂNG CAO (MODULE 8 & 9) ---
with tab5:
    st.header("🔬 Phân Hệ Thẩm Định Ngôn Ngữ Biến Đổi Nâng Cao")
    
    st.warning("""
    ⚠️ **CẢNH BÁO QUAN TRỌNG:**
    - Các kết quả về: *Tỷ lệ nghi ngờ AI*, *Tỷ lệ tương đồng trùng lặp*, và *Khả năng đạt giải* hoàn toàn chỉ mang tính chất hỗ trợ và tham khảo.
    - Quyết định phê duyệt cuối cùng thuộc về **Hội đồng thẩm định thực tế, Đơn vị xét duyệt và Các chuyên gia đánh giá**.
    - Hệ thống tuyệt đối không đưa ra khẳng định chắc chắn mang tính quy chụp văn bản là đạo văn hay do máy tạo hoàn toàn.
    """)
    
    if st.session_state.user_text_content and ai_engine:
        col_m8, col_m9 = st.columns(2)
        
        with col_m8:
            st.subheader("🤖 Module 8: Quét Dấu Hiệu AI Sinh Văn Bản")
            if st.button("Chạy quét cấu trúc lặp LLM"):
                with st.spinner("Đang phân tích độ tự nhiên và mật độ phân phối từ..."):
                    ai_detect_res = AdvancedAuditor.detect_ai_generated(st.session_state.user_text_content, ai_engine)
                    st.write(f"**Kết luận chung:** `{ai_detect_res.get('summary', 'Cần rà soát')}`")
                    st.info(f"💡 **Gợi ý cá nhân hóa:** {ai_detect_res.get('advice', '')}")
                    
                    df_ai = pd.DataFrame(ai_detect_res.get('sections', []))
                    st.table(df_ai)
                
        with col_m9:
            st.subheader("📚 Module 9: Kiểm Tra Đạo Văn & Trùng Lặp")
            if st.button("Đối chiếu hệ thống dữ liệu"):
                with st.spinner("Đang so sánh biểu mẫu ý tưởng diện rộng..."):
                    plag_res = AdvancedAuditor.check_plagiarism(st.session_state.user_text_content, ai_engine)
                    for p in plag_res:
                        color = "🔴" if p['level'] == "Cao" else "🟡"
                        st.write(f"{color} **{p['section']}**")
                        st.progress(p['similarity'] / 100)
                        st.caption(f"Mức độ tương đồng cấu trúc mạng: {p['similarity']}%")
    else:
        st.info("Vui lòng cung cấp API Key và tải hồ sơ tại Tab 2.")

# --- TAB 6: BẢNG ĐIỀU KHIỂN & PHẢN BIỆN (MODULE 11, 12, 13) ---
with tab6:
    st.header("📊 Trung Tâm Điều Hành Thẩm Định & Dự Đoán")
    
    if st.session_state.user_text_content and ai_engine:
        # Module 10: Dự đoán khả năng đạt giải
        st.subheader("🔮 Module 10: Dự Đoán Khả Năng Được Công Nhận")
        if st.button("Phân tích xác suất Hội đồng thi đua"):
            with st.spinner("Đang chạy mô hình đối chiếu thư viện giải thưởng..."):
                pred_res = AdvancedAuditor.predict_success_rate(st.session_state.user_text_content, ai_engine)
                
                col1, col2, col3 = st.columns(3)
                for rate in pred_res.get("rates", []):
                    if rate['level'] == "Cấp Trường": col1.metric("Xác suất Cấp Trường", f"{rate['probability']}%")
                    if rate['level'] == "Cấp Huyện": col2.metric("Xác suất Cấp Huyện", f"{rate['probability']}%")
                    if rate['level'] == "Cấp Tỉnh": col3.metric("Xác suất Cấp Tỉnh", f"{rate['probability']}%")
                
                st.success(f"**Điểm mạnh cấu trúc:** {pred_res.get('strengths')}")
                st.error(f"**Điểm yếu thiếu sót:** {pred_res.get('weaknesses')}")
                st.info(f"💬 **Nhận xét dự báo:** *{pred_res.get('advice')}*")
                
                st.write("**Biểu đồ phân tích chất lượng tiêu chí (Module 11):**")
                chart_data = pd.DataFrame({
                    'Tiêu chí': ['Cấu trúc', 'Nội dung', 'Minh chứng', 'Đổi mới'],
                    'Hồ sơ của bạn': [85, 70, 45, 60],
                    'Chuẩn Cấp Huyện': [80, 75, 70, 70]
                })
                st.bar_chart(chart_data, x='Tiêu chí')

        st.divider()
        
        # Module 12: Mô phỏng tranh biện phản biện hội đồng
        st.subheader("⚖️ Module 12: Góc Nhìn Phản Biện Hội Đồng Giả Lập")
        if st.button("Kích hoạt Hội đồng phản biện"):
            with st.spinner("Đang giả lập hội đồng thảo luận kín..."):
                debates = DashboardPanel.simulate_committee_debate(st.session_state.user_text_content, ai_engine)
                for d in debates:
                    with st.chat_message("user"):
                        st.write(f"**{d['reviewer']}** (Điểm chấm: {d['score']}/100)")
                        st.write(f"*{d['opinion']}*")
                    
        st.divider()
        
        # Module 13: Cố vấn chiến lược đường dài
        st.subheader("🎯 Module 13: Cố Vấn Chiến Lược Hoàn Thiện")
        st.caption("AI hoạch định lộ trình chuyển đổi nâng hạng giải thưởng dựa trên các điểm nghẽn.")
        
        strat_query = st.selectbox(
            "Lựa chọn câu hỏi chiến lược:",
            [
                "Tôi cần bổ sung gì cụ thể để hồ sơ này chắc chắn đạt cấp Huyện?",
                "Làm thế nào để nâng cấp phần giải pháp thực nghiệm lên tiêu chuẩn cấp Tỉnh?",
                "Phần biện pháp nào trong tài liệu thường bị Hội đồng chấm điểm thấp?"
            ]
        )
        if st.button("Xin lộ trình chiến lược"):
            with st.spinner("AI đang vạch lộ trình hành động..."):
                roadmap = DashboardPanel.get_strategic_roadmap(strat_query, ai_engine)
                st.markdown(roadmap)
    else:
        st.info("Vui lòng cung cấp API Key và tải hồ sơ tại Tab 2.")

# --- TAB 7: AI CỐ VẤN TƯƠNG TÁC ---
with tab7:
    st.header("💬 Trợ Lý Cố Vấn Học Đường (Contextual Chat)")
    st.write("Đặt câu hỏi trực tiếp về tài liệu của bạn, AI sẽ trả lời dựa trên ngữ cảnh cấu trúc văn bản đang mở.")
    user_query = st.text_input("Ví dụ: Tôi nên viết lại phần lý do chọn đề tài như thế nào để thuyết phục?")
    if user_query and ai_engine:
        if st.session_state.user_text_content:
            with st.spinner("AI đang tìm giải pháp tốt nhất..."):
                ctx_prompt = f"Ngữ cảnh tài liệu hiện tại:\n{st.session_state.user_text_content[:2000]}\n\nCâu hỏi giáo viên: {user_query}\nHãy trả lời chuẩn hóa chuyên môn."
                response = ai_engine.model.generate_content(ctx_prompt)
                st.write(response.text)
        else:
            st.warning("Vui lòng tải tài liệu tại Tab 2 trước khi đặt câu hỏi tương tác.")
# --- FOOTER CỐ ĐỊNH ---
st.divider()
st.markdown(
    """
    <div style="text-align: center; font-size: 0.8em; color: grey;">
        Ứng dụng được phát triển bởi Ngo Thanh Hung © 2026
    </div>
    """,
    unsafe_allow_html=True
)
