import streamlit as st

# Import hàm gọi AI từ lõi hệ thống
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

def show_library_module(api_key=None):
    st.subheader("📚 Thư Viện Tra Cứu & Tự Động Sinh Sáng Kiến Mẫu")
    st.info("Thầy/Cô có thể tra cứu các mẫu có sẵn hoặc gõ một tên đề tài bất kỳ để AI tự động xây dựng một bản sáng kiến mẫu hoàn chỉnh.")

    # --- TÍNH NĂNG CAO CẤP: AI TỰ SINH SÁNG KIẾN MẪU THEO TÊN NGƯỜI DÙNG GÕ ---
    st.markdown("### 🤖 Tính năng: Tự động biên soạn Sáng kiến mẫu theo yêu cầu")
    
    # Cho phép người dùng gõ hoặc dán tên đề tài tùy ý
    user_topic = st.text_input(
        "✍️ Nhập tên Đề tài/Sáng kiến thầy cô muốn tạo mẫu:",
        placeholder="Ví dụ: Ứng dụng AI và chuyển đổi số nâng cao hiệu quả dạy học môn Toán lớp 8"
    )
    
    if st.button("🔥 Kích hoạt AI biên soạn Bản mẫu Sư phạm"):
        if not user_topic.strip():
            st.warning("⚠️ Vui lòng nhập tên đề tài trước khi bấm tạo mẫu.")
        else:
            with st.spinner("🧠 AI đang phân tích bối cảnh, tra cứu thuật ngữ và biên soạn bản mẫu..."):
                # Thiết lập prompt ra lệnh chi tiết cho AI sinh đúng cấu trúc chuẩn
                prompt = f"""
                Hãy đóng vai là Chuyên gia Khoa học Sư phạm cấp cao của Bộ Giáo dục và Đào tạo Việt Nam.
                Xây dựng một BẢN SÁNG KIẾN KINH NGHIỆM MẪU chi tiết cho đề tài: "{user_topic}".
                
                Yêu cầu cấu trúc nội dung sinh ra phải bao gồm đầy đủ các phần sau:
                1. TÊN ĐỀ TÀI (Chuẩn hóa lại nếu cần)
                2. ĐẶT VẤN ĐỀ
                   - Lý do chọn đề tài (Nêu bật tính cấp thiết và thực trạng khó khăn tại trường học).
                   - Mục đích nghiên cứu.
                3. GIẢI PHÁP THỰC HIỆN (Biên soạn chi tiết ít nhất 3 biện pháp cốt lõi, đột phá, có ứng dụng công nghệ hoặc đổi mới phương pháp).
                4. KẾT QUẢ ĐẠT ĐƯỢC (Đưa ra các số liệu định lượng, tỷ lệ % tăng trưởng giả định một cách khoa học).
                5. KẾT LUẬN & KIẾN NGHỊ (Bài học kinh nghiệm và đề xuất với nhà trường/Sở GD&ĐT).
                
                Văn phong yêu cầu: Nghiêm túc, mang tính học thuật ngành giáo dục Việt Nam, lập luận chặt chẽ, không sáo rỗng.
                """
                
                # Gọi AI xử lý và truyền API Key từ Trang chủ sang
                generated_sample = call_ai_stream(
                    prompt=prompt, 
                    system_instruction="Bạn là Giáo sư Viện Khoa học Giáo dục Việt Nam.", 
                    api_key=api_key
                )
                
                # Hiển thị kết quả ra màn hình
                st.success("🎉 Đã biên soạn thành công bản mẫu sư phạm!")
                st.markdown("---")
                st.markdown(generated_sample)
                st.markdown("---")
                
                # Tích hợp luôn nút tải file bản mẫu vừa sinh về máy
                st.download_button(
                    label="📥 Tải Bản mẫu này về máy (.txt)",
                    data=generated_sample,
                    file_name=f"Mau_SKKN_{user_topic.replace(' ', '_')[:30]}.txt",
                    mime="text/plain"
                )
                
    st.markdown("<br><hr><br>", unsafe_allow_index=True)

    # --- ĐOẠN CODE DƯỚI ĐÂY LÀ THƯ VIỆN CÁC MẪU CỐ ĐỊNH CŨ (GIỮ NGUYÊN) ---
    st.markdown("### 📁 Danh mục các mẫu quy chuẩn có sẵn trong thư viện")
    search_query = st.text_input("🔍 Tìm kiếm nhanh trong kho mẫu sẵn có:", "")
    
    library_data = {
        "Toán học": [
            {
                "title": "Biện pháp ứng dụng công nghệ số trong dạy học Hình học lớp 8",
                "author": "Mẫu chuẩn Bộ GD&ĐT",
                "summary": "Giải pháp tập trung vào việc sử dụng các phần mềm hình học động (Geogebra) kết hợp mô hình lớp học đảo ngược...",
                "content": "ĐẶT VẤN ĐỀ\n1. Lý do chọn đề tài...\n\nNỘI DUNG CỐT LÕI..."
            }
        ]
    }
    
    for cat, topics in library_data.items():
        filtered_topics = [t for t in topics if search_query.lower() in t["title"].lower() or search_query.lower() in cat.lower()]
        if filtered_topics:
            with st.expander(f"📁 Danh mục: Môn {cat} ({len(filtered_topics)} tài liệu)"):
                for t in filtered_topics:
                    st.markdown(f"### 📄 {t['title']}")
                    st.write(f"ℹ️ **Tóm tắt:** {t['summary']}")
                    if st.checkbox(f"👁️ Xem nội dung mẫu", key=t['title']):
                        st.text_area("Nội dung:", value=t['content'], height=150)
