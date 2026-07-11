import streamlit as st
import os
from edu_ai_assistant.config import config
from edu_ai_assistant.modules.ui import UIManager
from edu_ai_assistant.modules.parser import DocumentParser
from edu_ai_assistant.modules.api_manager import APIManager
from edu_ai_assistant.modules.rag import KnowledgeHubRAG
from edu_ai_assistant.modules.multi_agent import MultiAgentWorkflow
from edu_ai_assistant.modules.word_export import WordExportEngine

# 1. Khởi tạo Giao diện
UIManager.setup_theme()
UIManager.render_header()
# 2. Khởi tạo & Kiểm tra Session State
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    # Đồng bộ hóa key để dùng thống nhất trong app
    st.session_state["api_key"] = st.session_state["gemini_api_key"]
elif "api_key" not in st.session_state or not st.session_state["api_key"].strip():
    # Nếu chưa nhập key ở trang chủ, hiển thị thông báo nhắc nhở và dừng app con lại
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop() # Dừng không chạy các đoạn code phía dưới để tránh lỗi crash

# Khởi tạo các biến lưu trữ trạng thái nếu chưa có
if "processed_doc" not in st.session_state:
    st.session_state["processed_doc"] = None
if "parsed_text" not in st.session_state:
    st.session_state["parsed_text"] = ""

# Khởi tạo RAG System
api_key = st.session_state.get("api_key")
rag_system = KnowledgeHubRAG(config.CHROMA_PERSIST_DIR, api_key) if api_key else None
# 3. Giao diện Chính (Main Interface)
# Tabs Chức năng
tab_config, tab_process, tab_copilot, tab_templates = st.tabs([
    "**| ⚙️ Cấu hình Hệ thống**",
    "**| ⚡ Xử lý Văn bản thông minh**", 
    "**| 💬 Document Copilot**", 
    "**| 📁 Thư viện Mẫu**"
])

# --- TAB CẤU HÌNH HỆ THỐNG ---
with tab_config:
    st.subheader("⚙️ Cấu hình Hệ thống & Tri thức ngành")
    
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.markdown("#### 👤 Người dùng")
        user_role = st.selectbox("**Vai trò người dùng**", [config.ROLE_TEACHER, config.ROLE_ADMIN, config.ROLE_GUEST])
        st.info(f"Quyền hiện tại: **{user_role}**")
        
    with col_c2:
        st.markdown("#### 📚 Knowledge Hub (RAG)")
        rag_upload = st.file_uploader("**Nạp Thông tư/Nghị định mẫu vào cơ sở dữ liệu:**", type=["docx", "pdf", "txt"], key="rag_file")
        if rag_upload:
            if st.button("📥 Lưu vào Vector DB", type="secondary"):
                with st.spinner("Đang phân tích & sinh Vector Embedding..."):
                    content, meta = DocumentParser.parse_file(rag_upload)
                    rag_sys = KnowledgeHubRAG(config.CHROMA_PERSIST_DIR, st.session_state["api_key"])
                    rag_sys.add_document(content, {"source": rag_upload.name})
                    st.toast(f"Đã nạp thành công {rag_upload.name} vào Tri thức ngành!", icon="✅")

with tab_process:
    st.subheader("📄 Tải lên & Điều khiển quy trình làm việc")
    
    uploaded_file = st.file_uploader(
        "**Kéo thả hoặc chọn file văn bản giáo dục (DOCX, PDF, TXT):**", 
        type=["docx", "pdf", "txt"]
    )

    if uploaded_file:
        content, meta = DocumentParser.parse_file(uploaded_file)
        st.session_state["parsed_text"] = content
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.info(f"📄 File: **{meta['file_name']}**")
        col_m2.info(f"📏 Dung lượng: **{meta['file_size_kb']} KB**")
        col_m3.info(f"📑 Số trang ước tính: **{meta['page_count']}**")
        col_m4.info(f"📝 Số từ: **{meta['word_count']}**")

        with st.expander("👀 Xem trước văn bản gốc", expanded=False):
            st.text_area("Nội dung gốc", content, height=200)

        st.divider()
        st.markdown("### 🤖 Yêu cầu AI Xử lý / Chỉnh sửa")
        
        prompt_option = st.selectbox("Chọn nhanh yêu cầu phổ biến:", [
            "Tự động rà soát toàn bộ (Lỗi thể thức + Pháp lý + Sư phạm)",
            "Chuyển đổi nội dung môn bóng chuyền sang kéo co (giữ nguyên cấu trúc)",
            "Tối ưu lại Kế hoạch Bài dạy (KHBD) theo đúng Công văn 5112 / Thông tư mới",
            "Rút gọn văn bản còn 2 trang giữ nguyên các mục chính",
            "Tùy chỉnh riêng..."
        ])
        
        user_prompt = prompt_option
        if prompt_option == "Tùy chỉnh riêng...":
            user_prompt = st.text_area("Nhập yêu cầu chi tiết cho AI Agent:", placeholder="Ví dụ: Bổ sung mục kinh phí và căn cứ Nghị định mới nhất...")

        if st.button("🚀 KÍCH HOẠT MULTI-AGENT WORKFLOW", type="primary", use_container_width=True):
            if not st.session_state.get("api_key"):
                st.error("🔑 Hệ thống chưa cấu hình Gemini API Key. Vui lòng kiểm tra lại trang chủ.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                workflow = MultiAgentWorkflow(st.session_state["api_key"], rag_system)
                final_output = workflow.execute_full_workflow(content, user_prompt, progress_bar, status_text)
                
                st.session_state["processed_doc"] = final_output
                st.success("🎉 Multi-Agent Workflow hoàn tất thành công!")

        if st.session_state["processed_doc"]:
            st.divider()
            st.markdown("### 🎯 KẾT QUẢ XỬ LÝ TỪ TRƯỞNG NHÓM AGENT")
            
            st.markdown(st.session_state["processed_doc"])
            
            # Xuất file
            docx_bytes = WordExportEngine.create_docx(st.session_state["processed_doc"])
            st.download_button(
                label="📥 Tải xuống File Word (.docx) Chuẩn Định Dạng",
                data=docx_bytes,
                file_name=f"AI_Processed_{uploaded_file.name}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )

# --- TAB DOCUMENT COPILOT ---
with tab_copilot:
    st.subheader("💬 Trò chuyện trực tiếp với Văn bản (Document Copilot)")
    if not st.session_state["parsed_text"]:
        st.warning("⚠️ Vui lòng tải lên một văn bản ở tab 'Xử lý Văn bản' trước khi bắt đầu Copilot.")
    else:
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        user_chat = st.chat_input("Hỏi AI bất kỳ điều gì về văn bản này...")
        if user_chat:
            st.session_state["chat_history"].append({"role": "user", "content": user_chat})
            with st.chat_message("user"):
                st.write(user_chat)

            with st.chat_message("assistant"):
                api_mgr = APIManager(st.session_state["api_key"])
                context_prompt = f"""Dưới đây là nội dung văn bản đang làm việc:
{st.session_state['parsed_text'][:4000]}

Trả lời câu hỏi của người dùng dựa trên văn bản này:
{user_chat}"""
                response = api_mgr.generate_response(context_prompt)
                st.write(response)
                st.session_state["chat_history"].append({"role": "assistant", "content": response})

# --- TAB THƯ VIỆN MẪU ---
with tab_templates:
    st.subheader("📁 Kho Mẫu Văn bản Giáo dục Chuẩn")
    st.info("💡 Bạn có thể chọn mẫu chuẩn bên dưới để xuất trực tiếp hoặc làm khung mẫu cho AI.")
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("""
        #### 1. Kế hoạch Giáo dục (KHBD/Giáo án)
        - Cấu trúc 4 bước theo Công văn 5112/BGDĐT.
        - Khung thiết kế ma trận & bảng đặc tả đề kiểm tra.
        
        #### 2. Báo cáo, thống kê
        - Đầy đủ mục Căn cứ, số liệu, biểu đồ.
        """)
    with col_t2:
        st.markdown("""
        #### 3. Báo cáo Sáng kiến Kinh nghiệm (SKKN)
        - Chuẩn bố cục Trình bày Lý do chọn đề tài, Biện pháp, Hiệu quả.
        
        #### 4. Biên bản & Công văn Hành chính
        - Chuẩn Nghị định 30/2020/NĐ-CP về Thể thức văn bản.
        """)
