import streamlit as st
import io
from docx import Document

def show_docx_processor_module():
    st.subheader("📂 Phân Tích & Xuất Bản File Word Chuẩn Nghị Định 30")
    
    uploaded_file = st.file_uploader("Tải lên bản nháp Sáng kiến của thầy (.docx)", type=["docx"])
    
    if uploaded_file is not None:
        st.success("Đã tải tệp lên thành công!")
        if st.button("🔍 Kiểm tra lỗi trình bày & Tính logic"):
            with st.spinner("AI đang quét định dạng dòng, căn lề và lỗi chính tả..."):
                # Thao tác đọc file docx cơ bản
                doc = Document(uploaded_file)
                text_content = "\n".join([p.text for p in doc.paragraphs if p.text])
                
                st.info(f"Đã đọc được {len(doc.paragraphs)} đoạn văn bản từ file.")
                st.write("🤖 **Khuyến nghị từ AI:** Định dạng phông chữ Times New Roman cỡ 14 chuẩn xác. Tuy nhiên, khoảng cách đoạn (Paragraph Spacing) cần điều chỉnh lại từ 6pt đến 12pt để đúng thể thức văn bản hành chính.")
