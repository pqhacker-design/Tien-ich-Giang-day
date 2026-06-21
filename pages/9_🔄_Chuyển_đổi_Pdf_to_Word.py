import streamlit as st
import io
from google import genai
from google.genai import types
import pdfplumber
from docx import Document

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Chuyển đổi Tài liệu sang Word", page_icon="📝", layout="boxed")

st.title("📝 Chuyển đổi Ảnh/PDF sang Word (Giữ định dạng)")
st.caption("Ứng dụng trích xuất văn bản từ tài liệu và xuất bản thành file `.docx` gọn gàng.")

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.stop() 

# Khởi tạo hoặc tái sử dụng client tập trung
if "gemini_client" not in st.session_state:
    try:
        st.session_state.gemini_client = genai.Client(api_key=api_key_input)
    except Exception as e:
        st.error(f"Khởi tạo Gemini Client thất bại: {e}")
        st.stop()

client = st.session_state.gemini_client

# --- HÀM TẠO FILE WORD TỪ VĂN BẢN ---
def create_word_document(text_content):
    doc = Document()
    # Tách văn bản theo các dòng để xử lý giữ định dạng xuống dòng và đoạn văn
    lines = text_content.split('\n')
    for line in lines:
        if line.strip().startswith('# '):  # Định dạng tiêu đề lớn nếu có markdown
            doc.add_heading(line.replace('# ', '').strip(), level=1)
        elif line.strip().startswith('## '):
            doc.add_heading(line.replace('## ', '').strip(), level=2)
        else:
            doc.add_paragraph(line)
            
    # Lưu vào bộ nhớ tạm buffer để Streamlit có thể tải về trực tiếp
    bio = io.BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- GIAO DIỆN TẢI FILE ---
uploaded_file = st.file_uploader(
    "Tải lên File ảnh (PNG, JPG, JPEG) hoặc File PDF cần chuyển đổi:",
    type=["png", "jpg", "jpeg", "pdf"]
)

if uploaded_file is not None:
    file_type = uploaded_file.type
    extracted_text = ""
    
    st.info(f"📁 Đã nhận file: **{uploaded_file.name}**")
    
    # Nút bấm kích hoạt tiến trình xử lý
    if st.button("🚀 Bắt đầu trích xuất và chuyển đổi"):
        with st.spinner("Đang xử lý dữ liệu và giữ cấu trúc định dạng..."):
            
            # TRƯỜNG HỢP 1: FILE PDF
            if file_type == "application/pdf":
                try:
                    with pdfplumber.open(uploaded_file) as pdf:
                        text_pages = []
                        for page in pdf.pages:
                            # extract_text của pdfplumber giữ khoảng cách và dòng cực tốt
                            page_text = page.extract_text(layout=True)
                            if page_text:
                                text_pages.append(page_text)
                        extracted_text = "\n\n--- PAGE BREAK ---\n\n".join(text_pages)
                except Exception as e:
                    st.error(f"Lỗi đọc file PDF bằng pdfplumber: {e}. Hệ thống sẽ thử chuyển đổi qua AI...")
                    # Dự phòng nếu PDF quét dạng ảnh (scanned), gửi qua Gemini xử lý
                    uploaded_file.seek(0)
                    file_bytes = uploaded_file.read()
                    file_part = types.Part.from_bytes(data=file_bytes, mime_type=file_type)
                    prompt = "Hãy trích xuất toàn bộ văn bản trong file PDF này, giữ nguyên cấu trúc dòng, đoạn văn, bảng biểu (nếu có) và định dạng thụt lề."
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[file_part, prompt]
                    )
                    extracted_text = response.text

            # TRƯỜNG HỢP 2: FILE ẢNH (Sử dụng AI OCR tối tân)
            else:
                file_bytes = uploaded_file.read()
                file_part = types.Part.from_bytes(data=file_bytes, mime_type=file_type)
                
                # Prompt tối ưu cấu trúc định dạng văn bản cho AI
                prompt = (
                    "Bạn là một chuyên gia OCR cao cấp. Hãy trích xuất chính xác 100% văn bản từ hình ảnh này. "
                    "Yêu cầu quan trọng: Giữ nguyên định dạng xuống dòng, khoảng cách đoạn, cấu trúc các mục (1., a., -) "
                    "và hiển thị lại dạng bảng nếu trong ảnh có bảng biểu. Không thêm lời bình luận của bạn."
                )
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[file_part, prompt]
                    )
                    extracted_text = response.text
                except Exception as e:
                    st.error(f"Lỗi khi xử lý ảnh qua Gemini API: {e}")

        # --- HIỂN THỊ KẾT QUẢ VÀ NÚT TẢI FILE ---
        if extracted_text.strip():
            st.success("✅ Đã trích xuất văn bản thành công!")
            
            # Hiển thị bản xem trước (Preview)
            with st.expander("👀 Xem trước văn bản trích xuất"):
                st.text_area("Nội dung:", extracted_text, height=300)
            
            # Tiến hành tạo file Word (.docx)
            word_file = create_word_document(extracted_text)
            
            # Nút Tải file Word về máy
            st.download_button(
                label="📥 Tải file WORD (.docx) về máy",
                data=word_file,
                file_name=uploaded_file.name.rsplit('.', 1)[0] + "_converted.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.warning("Không thể trích xuất được văn bản từ tài liệu này. Anh vui lòng kiểm tra lại chất lượng file nhé.")

# --- FOOTER CỐ ĐỊNH ---
st.divider()
st.markdown(
    """
    <div style="text-align: center; font-size: 0.8em; color: grey;">
        Ứng dụng được phát triển bởi Ngô Thanh Hùng
    </div>
    """,
    unsafe_allow_html=True
)
