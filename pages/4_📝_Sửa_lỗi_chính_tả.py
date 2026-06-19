import streamlit as st
import os
import pandas as pd
import altair as alt

# Import các module nội bộ
from utils import load_criteria, save_criteria, get_docx_info
from formatter import normalize_to_nd30
from spelling_checker import check_vietnamese_spelling
from grammar_checker import check_vietnamese_grammar
from ai_checker import analyze_document_with_ai, get_ai_response
from track_changes import render_track_changes_view
from report_generator import generate_excel_report

st.set_page_config(page_title="AI Document & School Record Processor", layout="wide")

# --- LẤY API KEY TẬP TRUNG TỪ TRANG CHỦ ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    # Nếu chưa nhập key ở trang chủ, hiển thị thông báo nhắc nhở và dừng app con lại
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.stop() # Dừng không chạy các đoạn code phía dưới để tránh lỗi crash

st.sidebar.subheader("🎯 Tiêu chí kiểm tra Sổ Sách")
current_criteria = load_criteria()

# Cho phép thêm tiêu chí động qua UI
profile_type = st.sidebar.selectbox("Loại hồ sơ cấu hình:", list(current_criteria.keys()))
new_criterion = st.sidebar.text_input("Thêm mục kiểm tra bắt buộc:")
if st.sidebar.button("Cập nhật tiêu chí"):
    if new_criterion:
        current_criteria[profile_type].append(new_criterion)
        save_criteria(current_criteria)
        st.sidebar.success("Đã cập nhật tiêu chí động!")

# Giao diện chính chính thức
st.title("📑 AI CHUẨN HÓA VĂN BẢN HÀNH CHÍNH VÀ HỒ SƠ GIÁO DỤC")
st.caption("Giải pháp tự động hóa rà soát Nghị định 30/2020/NĐ-CP và Chương trình GDPT 2018")

uploaded_file = st.file_uploader("Kéo thả file văn bản hành chính hoặc Hồ sơ trường học của bạn (.DOCX)", type=["docx"])

if uploaded_file is not None:
    # Lưu file tạm để xử lý bằng thư viện docx
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    doc_info = get_docx_info(temp_path)
    
    # Hiển thị Metadata văn bản sơ bộ
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tên văn bản", doc_info["filename"])
    col2.metric("Số lượng từ", doc_info["word_count"])
    col3.metric("Số trang dự tính", doc_info["page_count"])
    col4.metric("Dung lượng", f"{uploaded_file.size / 1024:.2f} KB")

    # Bảng điều khiển chế độ phân tích
    st.write("---")
    st.subheader("🛠️ Chế độ phân tích & Chuẩn hóa")
    c_thethuc = st.checkbox("Kiểm tra thể thức (NĐ 30/2020/NĐ-CP)", value=True)
    c_chinhta = st.checkbox("Kiểm tra chính tả nâng cao", value=True)
    c_nguphap = st.checkbox("Kiểm tra ngữ pháp & Hành văn", value=True)
    c_hoso = st.checkbox("Phân tích chiều sâu Hồ sơ Giáo dục (GDPT 2018)", value=True)

    if st.button("🚀 BẮT ĐẦU PHÂN TÍCH VÀ SỬA LỖI TỰ ĐỘNG", type="primary"):
        with st.spinner("Hệ thống AI đang đọc hiểu và quét sâu cấu trúc văn bản..."):
            
            # Khởi tạo danh sách lỗi tổng hợp
            all_errors = []
            
            if c_chinhta:
                all_errors.extend(check_vietnamese_spelling(doc_info["full_text"]))
            if c_nguphap:
                all_errors.extend(check_vietnamese_grammar(doc_info["full_text"]))
                
            # Gọi Core AI xử lý sâu
            ai_result = None
            if c_hoso or c_thethuc:
                ai_result = analyze_document_with_ai(doc_info["full_text"], doc_info["filename"])
                if ai_result and "loi_the_thuc" in ai_result:
                    all_errors.extend(ai_result["loi_the_thuc"])

            # Lưu vào session state phục vụ tương tác trực tiếp
            st.session_state["all_errors"] = all_errors
            st.session_state["ai_result"] = ai_result
            
            # Tiến hành chuẩn hóa định dạng vật lý theo NĐ30 luôn
            out_standard_path = f"standardized_{doc_info['filename']}"
            normalize_to_nd30(temp_path, out_standard_path)
            st.session_state["out_standard_path"] = out_standard_path

    # Hiển thị kết quả xử lý nếu có trong Session State
    if "ai_result" in st.session_state and st.session_state["ai_result"]:
        res = st.session_state["ai_result"]
        
        st.write("---")
        st.header("📊 KẾT QUẢ ĐÁNH GIÁ TỪ CHUYÊN GIA AI")
        
        col_res1, col_res2 = st.columns([1, 1])
        with col_res1:
            st.info(f"📋 **Loại hồ sơ nhận diện:** {res.get('loai_ho_so', 'Không xác định')} ({res.get('do_tin_cay', 0)}% độ tin cậy)")
            st.metric(value=f"{res['diem'].get('tong', 0)} / 100", label="TỔNG ĐIỂM CHẤT LƯỢNG HỒ SƠ")
            st.subheader(f"Xếp loại chung: {res.get('xep_loai', 'Chưa xếp loại')}")
            
        with col_res2:
            st.write("**Biểu đồ phân rã điểm số năng lực văn bản:**")
            chart_data = pd.DataFrame({
                'Tiêu chí': ['Thể thức', 'Nội dung', 'GDPT 2018', 'Năng lực số', 'Khoa học'],
                'Điểm': [res['diem'].get('the_thuc',0), res['diem'].get('noi_dung',0), res['diem'].get('gdpt_2018',0), res['diem'].get('nang_luc_so',0), res['diem'].get('khoa_hoc',0)]
            })
            chart = alt.Chart(chart_data).mark_bar(color='#4CAF50').encode(x='Tiêu chí', y='Điểm')
            st.altair_chart(chart, use_container_width=True)

        # Kiểm tra chi tiết cấu trúc hồ sơ học đường
        st.write("---")
        tab1, tab2, tab3 = st.tabs(["⚠️ Cảnh báo Cấu trúc & GDPT 2018", "📝 Phê duyệt Track Changes", "🤖 Trợ lý AI Hỏi Đáp"])
        
        with tab1:
            st.subheader("Kiểm tra sự tích hợp Chương trình GDPT 2018")
            st.json(res.get("gdpt_2018_check", {}))
            
            st.subheader("Cảnh báo thiếu sót danh mục bắt buộc:")
            for thieu in res.get("thieu_sot_cau_truc", []):
                st.warning(thieu)
                
            st.subheader("Đề xuất cải tiến từ Hội đồng chuyên môn AI:")
            for dexuat in res.get("de_xuat_cai_tien", []):
                st.success(f"💡 {dexuat}")

        with tab2:
            # Module 5 & Module 6 hiển thị tại đây
            remaining_errors = render_track_changes_view(st.session_state["all_errors"])
            
            # Xuất file báo cáo tổng hợp
            st.write("---")
            st.subheader("💾 Xuất dữ liệu & Báo cáo hoàn chỉnh")
            
            # Đọc file Word đã định dạng sẵn lề lối từ formatter để người dùng tải
            if "out_standard_path" in st.session_state:
                with open(st.session_state["out_standard_path"], "rb") as f_word:
                    st.download_button("📥 Tải về Văn bản đã chuẩn hóa lề lối (.DOCX)", data=f_word.read(), file_name=f"ChuanHoa_{doc_info['filename']}")
            
            # Tạo file excel báo cáo lỗi động dựa trên dữ liệu hiện tại
            excel_data = generate_excel_report(remaining_errors, res['diem'])
            st.download_button("📥 Xuất Báo cáo Thống kê lỗi chi tiết (.XLSX)", data=excel_data, file_name=f"BaoCaoLoi_{doc_info['filename']}.xlsx")

        with tab3:
            st.subheader("💬 Hỏi đáp tương tác sâu về các quy định pháp lý pháp lý")
            user_q = st.text_input("Ví dụ: Tại sao lỗi thể thức quốc hiệu của tôi lại bị chấm điểm thấp?")
            if user_q:
                with st.spinner("AI đang tra cứu Nghị định 30/2020/NĐ-CP..."):
                    context_prompt = f"Dựa trên văn bản có chất lượng điểm số tổng {res['diem'].get('tong', 0)}, người dùng hỏi: {user_q}. Hãy giải thích rõ căn cứ theo điều khoản pháp lý quy định hành chính hoặc hướng dẫn của Bộ GD&ĐT."
                    answer = get_api_response(context_prompt)
                    st.write(answer)
                    
    # Dọn dẹp tệp tạm thời sau phiên làm việc
    if os.path.exists(temp_path):
        os.remove(temp_path)
