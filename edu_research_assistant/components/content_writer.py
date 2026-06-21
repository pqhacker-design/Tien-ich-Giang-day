import streamlit as st
# Sửa lại đường dẫn import tùy thuộc vào cấu trúc thư mục thực tế của thầy
try:
    from ai_engine import call_ai_stream
except ModuleNotFoundError:
    from edu_research_assistant.ai_engine import call_ai_stream

# Thêm tham số api_key=None vào định nghĩa hàm để nhận Key truyền sang
def show_content_writer_module(api_key=None):
    st.subheader("📝 Trợ Lý AI Biên Soạn Nội Dung Chuyên Sâu")
    
    title = st.text_input("Nhập tên đề tài chính thức cần viết bài:", value="Ứng dụng sơ đồ tư duy kết hợp công nghệ AI nhằm nâng cao năng lực tự học hình học của học sinh lớp 8")
    mode = st.selectbox("Chế độ viết:", ["Viết ngắn", "Viết tiêu chuẩn", "Viết chi tiết", "Viết chuyên sâu"])
    action = st.selectbox("Hành động:", ["Viết mới từ đầu", "Viết mở rộng ý", "Tóm tắt/Rút gọn", "Chuyển đổi văn phong sư phạm"])
    
    section = st.selectbox("Chọn chương/phần mục:", [
        "Lý do chọn đề tài / Đặt vấn đề",
        "Cơ sở lý luận khoa học",
        "Thực trạng và nguyên nhân khó khăn",
        "Các biện pháp thực hiện (Nội dung cốt lõi)",
        "Kết quả đạt được và bài học kinh nghiệm"
    ])
    
    context_note = st.text_area("Ý tưởng cốt lõi hoặc tài liệu tham khảo bổ sung (nếu có):")

    if st.button("✍️ Bắt đầu sinh nội dung học thuật"):
        if not title.strip():
            st.error("Vui lòng nhập tên đề tài trước khi viết.")
            return
            
        with st.spinner("AI đang tra cứu thuật ngữ chuyên ngành và biên soạn văn bản..."):
            prompt = f"""
            Tên đề tài: {title}
            Yêu cầu: {action} phần '{section}' theo chế độ '{mode}'.
            Ý tưởng bổ sung từ tác giả: {context_note}
            
            Bạn là chuyên gia viết sáng kiến kinh nghiệm và nghiên cứu khoa học sư phạm ứng dụng với hơn 20 năm kinh nghiệm trong ngành giáo dục Việt Nam, từng tham gia chấm sáng kiến cấp tỉnh và hướng dẫn đề tài nghiên cứu khoa học giáo dục.

            Hãy viết nội dung có chiều sâu học thuật, có tính thực tiễn, tính mới, tính sáng tạo và khả năng áp dụng cao. Không viết theo kiểu liệt kê hoặc văn mẫu AI. Mỗi luận điểm phải có căn cứ lý luận, minh chứng thực tiễn hoặc số liệu phù hợp.

            Ưu tiên các xu hướng giáo dục hiện đại như chuyển đổi số, AI trong giáo dục, năng lực số, giáo dục STEM, phát triển phẩm chất và năng lực học sinh theo Chương trình GDPT 2018.
            ### TIÊU CHUẨN NÂNG CAO DÀNH CHO SÁNG KIẾN KINH NGHIỆM VÀ NGHIÊN CỨU KHOA HỌC

            * Viết theo đúng cấu trúc của một sáng kiến kinh nghiệm hoặc đề tài nghiên cứu khoa học sư phạm ứng dụng trong ngành giáo dục Việt Nam.
            
            * Phân tích rõ vấn đề thực tiễn tại đơn vị công tác, nêu được nguyên nhân, hạn chế và nhu cầu đổi mới.
            
            * Các biện pháp phải có tính mới, tính sáng tạo, tính khả thi và khả năng nhân rộng.
            
            * Mỗi giải pháp cần trình bày:
            
              * Mục tiêu giải pháp.
              * Nội dung thực hiện.
              * Quy trình thực hiện.
              * Điều kiện áp dụng.
              * Ví dụ minh họa thực tế.
              * Hiệu quả dự kiến.
            
            * Tự xây dựng số liệu khảo sát trước và sau tác động theo hướng hợp lý, khoa học và có tính thuyết phục.
            
            * Bổ sung các bảng thống kê, biểu đồ, tỷ lệ phần trăm, mức độ tiến bộ của học sinh hoặc đối tượng nghiên cứu.
            
            * Vận dụng các lý thuyết giáo dục hiện đại như:
            
              * Dạy học phát triển phẩm chất và năng lực.
              * Giáo dục STEM/STEAM.
              * Chuyển đổi số trong giáo dục.
              * Dạy học tích cực.
              * Giáo dục số và năng lực số.
              * AI trong giáo dục.
              * Kiểm tra đánh giá theo định hướng phát triển năng lực.
            
            * Dẫn chiếu phù hợp các văn bản chỉ đạo hiện hành của Bộ GD&ĐT như:
            
              * Chương trình GDPT 2018.
              * Thông tư đánh giá học sinh.
              * Các văn bản về chuyển đổi số, giáo dục STEM, năng lực số.
            
            * Văn phong phải mang tính học thuật, khách quan, tránh sử dụng các cụm từ sáo rỗng như:
              "hết sức cần thiết", "rất quan trọng", "mang lại hiệu quả cao" nếu không có minh chứng.
            
            * Mỗi nhận định đều cần có dẫn chứng, ví dụ thực tế hoặc số liệu minh họa.
            
            * Kết quả nghiên cứu phải phân tích theo các tiêu chí:
            
              * Hiệu quả đối với học sinh.
              * Hiệu quả đối với giáo viên.
              * Hiệu quả đối với nhà trường.
              * Hiệu quả về chuyển đổi số.
              * Khả năng áp dụng rộng rãi.
            
            * Tự động đề xuất:
            
              * Phiếu khảo sát.
              * Bảng câu hỏi điều tra.
              * Kế hoạch thực hiện.
              * Biên bản họp chuyên môn.
              * Bảng thống kê thực nghiệm.
              * Hình ảnh minh họa cần thiết.
              * Phụ lục và minh chứng kèm theo.
            
            * Nếu thiếu dữ liệu thực tế, AI được phép xây dựng số liệu giả định nhưng phải:
            
              * Hợp lý.
              * Có tính logic.
              * Phù hợp với quy mô lớp học và thực tế giáo dục Việt Nam.
            
            * Nội dung phải đạt mức chất lượng tương đương hồ sơ dự thi cấp trường, cấp huyện hoặc cấp tỉnh.

            """
            
            # TRUYỀN api_key VÀO ĐÂY ĐỂ GỌI SỬ DỤNG
            result = call_ai_stream(prompt, "Bạn là Giáo sư, chuyên gia viết các bài báo khoa học Giáo dục Việt Nam.", api_key=api_key)
            st.markdown(result)
