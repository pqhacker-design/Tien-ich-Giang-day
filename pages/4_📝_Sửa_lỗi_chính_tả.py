import streamlit as st
import os
import pandas as pd
import altair as alt

# Import trực tiếp các file trong cùng dự án (bỏ tiền tố vietnamese_word_corrector. nếu không dùng cấu trúc package)
from utils import load_criteria, save_criteria, get_docx_info
from formatter import normalize_to_nd30
from spelling_checker import check_vietnamese_spelling
from grammar_checker import check_vietnamese_grammar
from ai_checker import analyze_document_with_ai, get_ai_response
from track_changes import render_track_changes_view
from report_generator import generate_excel_report

st.set_page_config(page_title="AI Document & School Record Processor", layout="wide")

st.markdown("## 📑 Sửa lỗi chính tả và chuẩn hóa văn bản")
st.info("Giúp GV sửa lỗi chính tả và chuẩn hóa văn bản Hành chính - Giáo dục theo Nghị định 30/2020/NĐ-CP.")

# --- 1. CHECK API KEY ---
if "gemini_api_key" in st.session_state and st.session_state["gemini_api_key"].strip() != "":
    api_key_input = st.session_state["gemini_api_key"]
else:
    st.warning("⚠️ Vui lòng quay lại **Trang chủ** để nhập Google Gemini API Key trước khi sử dụng tính năng này.")
    st.info("💡 Mẹo: Nhập một lần tại trang chủ, tất cả các công cụ khác sẽ tự động kích hoạt.")
    st.page_link("🏠_Trang_Chủ.py", label="Nhấn vào đây để Quay lại Trang chủ", icon="🔄")
    st.stop() 

# --- 2. CẤU HÌNH TIÊU CHÍ ---
with st.expander("⚙️ **Cấu hình Tiêu chí kiểm tra Sổ Sách & Hồ sơ**", expanded=False):
    current_criteria = load_criteria()
    
    col_cfg1, col_cfg2, col_cfg3 = st.columns([1, 1, 1])
    with col_cfg1:
        profile_type = st.selectbox("**Loại hồ sơ cấu hình:**", list(current_criteria.keys()))
    with col_cfg2:
        new_criterion = st.text_input("**Thêm mục kiểm tra bắt buộc:**")
    with col_cfg3:
        st.write("&#160;")
        if st.button("Cập nhật tiêu chí", use_container_width=True, type="primary"):
            if new_criterion:
                current_criteria[profile_type].append(new_criterion)
                save_criteria(current_criteria)
                st.success("Đã cập nhật tiêu chí động!")

# --- 3. UPLOAD FILE ---
uploaded_file = st.file_uploader("**Kéo thả file văn bản hành chính hoặc Hồ sơ trường học của bạn (.DOCX):**", type=["docx"])

if uploaded_file is not None:
    temp_path = f"temp_{uploaded_file.name}"
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    doc_info = get_docx_info(temp_path)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tên văn bản", doc_info["filename"])
    col2.metric("Số lượng từ", doc_info["word_count"])
    col3.metric("Số trang dự tính", doc_info["page_count"])
    col4.metric("Dung lượng", f"{uploaded_file.size / 1024:.2f} KB")

    st.write("---")
    st.subheader("🛠️ Chế độ phân tích & Chuẩn hóa")
    
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        c_thethuc = st.checkbox("Kiểm tra thể thức (NĐ 30/2020/NĐ-CP)", value=True)
        c_chinhta = st.checkbox("Kiểm tra chính tả nâng cao", value=True)
    with col_chk2:
        c_nguphap = st.checkbox("Kiểm tra ngữ pháp & Hành văn", value=True)
        c_hoso = st.checkbox("Phân tích chiều sâu Hồ sơ Giáo dục (GDPT 2018)", value=True)

    # --- 4. NÚT XỬ LÝ PHÂN TÍCH & CHUẨN HÓA ---
    if st.button("🚀 BẮT ĐẦU PHÂN TÍCH VÀ SỬA LỖI TỰ ĐỘNG", type="primary", use_container_width=True):
        with st.spinner("Hệ thống AI đang đọc hiểu, quét lỗi và tự động căn chỉnh thể thức..."):
            all_errors = []
            
            if c_chinhta:
                all_errors.extend(check_vietnamese_spelling(doc_info["full_text"]))
            if c_nguphap:
                all_errors.extend(check_vietnamese_grammar(doc_info["full_text"]))
                
            ai_result = None
            if c_hoso or c_thethuc:
                ai_result = analyze_document_with_ai(doc_info["full_text"], doc_info["filename"])
                if isinstance(ai_result, dict) and "loi_the_thuc" in ai_result:
                    all_errors.extend(ai_result["loi_the_thuc"])

            out_standard_path = f"standardized_{doc_info['filename']}"
            normalize_to_nd30(temp_path, out_standard_path)
            
            st.session_state["all_errors"] = all_errors
            st.session_state["ai_result"] = ai_result
            st.session_state["out_standard_path"] = out_standard_path
            st.session_state["analyzed_file_name"] = uploaded_file.name
            
            st.success("✨ Đã hoàn thành phân tích và chuẩn hóa thể thức!")

    # --- 5. HIỂN THỊ KẾT QUẢ ---
    if "all_errors" in st.session_state and st.session_state.get("analyzed_file_name") == uploaded_file.name:
        res = st.session_state.get("ai_result")
        errors = st.session_state.get("all_errors", [])
        
        st.write("---")
        st.header("📊 KẾT QUẢ PHÂN TÍCH & CHUẨN HÓA VĂN BẢN")
        
        if isinstance(res, dict):
            col_res1, col_res2 = st.columns([1, 1])
            with col_res1:
                st.info(f"📋 **Loại hồ sơ nhận diện:** {res.get('loai_ho_so', 'Không xác định')} ({res.get('do_tin_cay', 0)}% độ tin cậy)")
                st.metric(value=f"{res.get('diem', {}).get('tong', 0)} / 100", label="TỔNG ĐIỂM CHẤT LƯỢNG HỒ SƠ")
                st.subheader(f"Xếp loại chung: {res.get('xep_loai', 'Chưa xếp loại')}")
                
            with col_res2:
                st.write("**Biểu đồ phân rã điểm số năng lực văn bản:**")
                chart_data = pd.DataFrame({
                    'Tiêu chí': ['Thể thức', 'Nội dung', 'GDPT 2018', 'Năng lực số', 'Khoa học'],
                    'Điểm': [
                        res.get('diem', {}).get('the_thuc', 0), 
                        res.get('diem', {}).get('noi_dung', 0), 
                        res.get('diem', {}).get('gdpt_2018', 0), 
                        res.get('diem', {}).get('nang_luc_so', 0), 
                        res.get('diem', {}).get('khoa_hoc', 0)
                    ]
                })
                chart = alt.Chart(chart_data).mark_bar(color='#4CAF50').encode(x='Tiêu chí', y='Điểm')
                st.altair_chart(chart, use_container_width=True)

        st.write("---")
        tab1, tab2, tab3 = st.tabs(["⚠️ Cảnh báo Cấu trúc & GDPT 2018", "📝 Phê duyệt Track Changes", "🤖 Trợ lý AI Hỏi Đáp"])
        
        with tab1:
            if isinstance(res, dict):
                st.subheader("Kiểm tra sự tích hợp Chương trình GDPT 2018")
                st.json(res.get("gdpt_2018_check", {}))
                
                st.subheader("Cảnh báo thiếu sót danh mục bắt buộc:")
                for thieu in res.get("thieu_sot_cau_truc", []):
                    st.warning(thieu)
                    
                st.subheader("Đề xuất cải tiến từ Hội đồng chuyên môn AI:")
                for dexuat in res.get("de_xuat_cai_tien", []):
                    st.success(f"💡 {dexuat}")
            else:
                st.info("💡 Bạn cần tích chọn tính năng 'Phân tích chiều sâu Hồ sơ' hoặc 'Kiểm tra thể thức' để xem đánh giá chuyên sâu từ AI.")

        with tab2:
            remaining_errors = render_track_changes_view(errors)
            st.write("---")
            st.subheader("💾 Xuất dữ liệu & Báo cáo hoàn chỉnh")
            
            if "out_standard_path" in st.session_state and os.path.exists(st.session_state["out_standard_path"]):
                with open(st.session_state["out_standard_path"], "rb") as f_word:
                    st.download_button(
                        label="📥 Tải về Văn bản đã chuẩn hóa lề lối (.DOCX)", 
                        data=f_word.read(), 
                        file_name=f"ChuanHoa_{doc_info['filename']}",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            
            scores = res.get('diem', {}) if isinstance(res, dict) else {"the_thuc": 0, "noi_dung": 0, "gdpt_2018": 0, "nang_luc_so": 0, "khoa_hoc": 0, "tong": 0}
            excel_data = generate_excel_report(remaining_errors, scores)
            st.download_button(
                label="📥 Xuất Báo cáo Thống kê lỗi chi tiết (.XLSX)", 
                data=excel_data, 
                file_name=f"BaoCaoLoi_{doc_info['filename']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with tab3:
            st.subheader("💬 Hỏi đáp tương tác sâu về các quy định pháp lý")
            user_q = st.text_input("Ví dụ: Tại sao lỗi thể thức quốc hiệu của tôi lại bị chấm điểm thấp?")
            if user_q:
                with st.spinner("AI đang tra cứu..."):
                    score_info = res.get('diem', {}).get('tong', 0) if isinstance(res, dict) else "Chưa chấm điểm"
                    context_prompt = f"Dựa trên văn bản có chất lượng điểm số tổng {score_info}, người dùng hỏi: {user_q}."
                    answer = get_ai_response(context_prompt)
                    st.write(answer)

# --- FOOTER ---
st.divider()
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
