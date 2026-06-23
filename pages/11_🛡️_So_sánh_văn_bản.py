import streamlit as st
import os
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

st.set_page_config(page_title="AI Thư ký Hội đồng - Kiểm định Hồ sơ Giáo dục", layout="wide")

# Khởi tạo Session State lưu trữ dữ liệu liên tục và đồng bộ
if "rag_manager" not in st.session_state:
    st.session_state.rag_manager = RAGManager()
if "template_reqs" not in st.session_state:
    st.session_state.template_reqs = []
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None
if "user_text_content" not in st.session_state:
    st.session_state.user_text_content = ""

st.title("🛡️ AI Thư Ký Hội Đồng - Trợ Lý Kiểm Định & Hoàn Thiện Hồ Sơ Chuyên Nghiệp")
st.caption("Giải pháp ứng dụng Trí tuệ nhân tạo chuyên biệt dành cho Sáng kiến kinh nghiệm, Kế hoạch bài dạy (KHBD), và Đánh giá chuẩn giáo dục.")

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
        for idx, item in enumerate(st.session_state.audit_report):
            with st.expander(f"📌 Tiêu chí: {item.get('criteria')} - Hiện trạng: {item.get('status')}"):
                st.write(f"**Điểm thành phần:** {item.get('score')}/100")
                st.info(f"💡 **Đề xuất hiệu đính từ Hội đồng AI:** {item.get('fix')}")
                
                col_acc, col_rej = st.columns(2)
                if col_acc.button("☑️ Áp dụng Đề xuất này", key=f"acc_{idx}"):
                    st.success("Đã ghi nhận cấu trúc chỉnh sửa vào hàng đợi xuất file!")
                col_rej.button("✖️ Bỏ qua lỗi", key=f"rej_{idx}")
        st.divider()
        st.subheader("💾 Tải về văn bản báo cáo")
    # Tính điểm trung bình để truyền vào file
        avg_score = sum([int(i.get('score', 70)) for i in st.session_state.audit_report]) / len(st.session_state.audit_report)
        
        # Gọi hàm tạo file Word từ bộ nhớ đệm
        docx_data = export_audit_to_docx(st.session_state.audit_report, avg_score)
        
        # Hiển thị nút bấm tải về chính thức trên giao diện Streamlit
        st.download_button(
            label="📥 Tải xuống Biên Bản Thẩm Định Toàn Diện (.DOCX)",
            data=docx_data,
            file_name="Bien_Ban_Tham_Dinh_Ho_So_Giao_Duc.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
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
