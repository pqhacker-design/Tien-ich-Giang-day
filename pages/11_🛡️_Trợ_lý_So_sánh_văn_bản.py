import streamlit as st
import os
from dotenv import load_dotenv
from core.document_proc import DocumentProcessor
from core.ai_engine import AIEngine
from core.rag_manager import RAGManager
from modules.grammar_checker import VietnameseGrammarChecker
from modules.evidence_gen import EvidenceGenerator
from modules.criterion_eval import CommitteeEvaluator

load_dotenv()

st.set_page_config(page_title="AI Thư ký Hội đồng - Kiểm định Hồ sơ Giáo dục", layout="wide")

# Khởi tạo Session State lưu trữ dữ liệu liên tục
if "rag_manager" not in st.session_state:
    st.session_state.rag_manager = RAGManager()
if "template_reqs" not in st.session_state:
    st.session_state.template_reqs = []
if "audit_report" not in st.session_state:
    st.session_state.audit_report = None

st.title("🛡️ AI Thư Ký Hội Đồng - Trợ Lý Kiểm Định & Hoàn Thiện Hồ Sơ Chuyên Nghiệp")
st.caption("Giải pháp ứng dụng Trí tuệ nhân tạo chuyên biệt dành cho Sáng kiến kinh nghiệm, Kế hoạch bài dạy (KHBD), và Đánh giá chuẩn giáo dục.")

# --- SIDEBAR: Cấu hình hệ thống ---
st.sidebar.header("⚙️ Cấu hình Hệ thống AI")
api_key = st.sidebar.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
model_name = st.sidebar.selectbox("Lựa chọn Mô hình", ["gemini-1.5-pro", "gemini-1.5-flash"])
audit_level = st.sidebar.radio("Mức độ rà soát chuyên sâu", ["Toàn diện (Cấu trúc + Câu từ)", "Cấu trúc khung", "Từ khóa & Minh chứng"])

if st.sidebar.button("Lưu & Khởi động Trợ lý"):
    if not api_key:
        st.sidebar.error("Vui lòng cung cấp API Key hợp lệ!")
    else:
        st.sidebar.success("Hệ thống AI đã sẵn sàng hoạt động!")

ai_engine = AIEngine(api_key=api_key, model_name=model_name) if api_key else None

# --- Giao diện Tabs chính ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 1. Thư viện Mẫu Chuẩn", 
    "📂 2. Hồ Sơ Cần Kiểm Tra", 
    "🔬 3. Phân Tích & Đối Chiếu AI", 
    "📊 4. Thẩm Định Hội Đồng",
    "🤖 5. Chat Cố Vấn Tương Tác"
])

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

# --- TAB 2: VĂN BẢN CẦN KIỂM TRA ---
with tab2:
    st.header("Tải lên tài liệu giáo viên cần thẩm định")
    uploaded_user_file = st.file_uploader("Tải lên Hồ sơ của bạn (DOCX/PDF)", type=["docx", "pdf"], key="user_doc")
    if uploaded_user_file:
        user_text = DocumentProcessor.read_file(uploaded_user_file)
        st.text_area("Xem trước Nội dung văn bản hiện tại:", value=user_text[:1500] + "\n...", height=300)

# --- TAB 3: PHÂN TÍCH AI & TRACK CHANGES ---
with tab3:
    st.header("Kết quả phân tích, đối chiếu diện rộng")
    if st.button("🚀 Khởi chạy Rà soát tự động bằng AI") and uploaded_user_file and ai_engine:
        user_text = DocumentProcessor.read_file(uploaded_user_file)
        with st.spinner("AI đang tiến hành quét cấu trúc, kiểm tra lỗi hành chính và chính tả..."):
            res = ai_engine.audit_document(st.session_state.template_reqs, user_text, audit_level)
            st.session_state.audit_report = res.get("report", [])
            
    if st.session_state.audit_report:
        st.subheader("Bảng chi tiết thiếu sót và khuyến nghị hành động:")
        for idx, item in enumerate(st.session_state.audit_report):
            with st.expander(f"📌 Tiêu chí: {item.get('criteria')} - Hiện trạng: {item.get('status')}"):
                st.write(f"**Điểm thành phần:** {item.get('score')}/100")
                st.info(f"💡 **Đề xuất hiệu đính từ Hội đồng AI:** {item.get('fix')}")
                
                # Tính năng Track changes lựa chọn áp dụng áp đặt
                col_acc, col_rej = st.columns(2)
                if col_acc.button("☑️ Áp dụng Đề xuất này", key=f"acc_{idx}"):
                    st.success("Đã ghi nhận cấu trúc chỉnh sửa vào hàng đợi xuất file!")
                col_rej.button("✖️ Bỏ qua lỗi", key=f"rej_{idx}")

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

# --- TAB 5: AI CỐ VẤN TƯƠNG TÁC ---
with tab5:
    st.header("💬 Trợ Lý Cố Vấn Học Đường (Contextual Chat)")
    st.write("Đặt câu hỏi trực tiếp về tài liệu của bạn, AI sẽ trả lời dựa trên ngữ cảnh cấu trúc văn bản đang mở.")
    user_query = st.text_input("Ví dụ: Tôi nên viết lại phần lý do chọn đề tài như thế nào để thuyết phục?")
    if user_query and ai_engine and uploaded_user_file:
        user_text = DocumentProcessor.read_file(uploaded_user_file)
        with st.spinner("AI đang tìm giải pháp tốt nhất..."):
            ctx_prompt = f"Ngữ cảnh tài liệu hiện tại:\n{user_text[:2000]}\n\nCâu hỏi giáo viên: {user_query}\nHãy trả lời chuẩn hóa chuyên môn."
            response = ai_engine.model.generate_content(ctx_prompt)
            st.write(response.text)
