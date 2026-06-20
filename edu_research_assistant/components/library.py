import streamlit as st

def show_library_module():
    st.subheader("📚 Thư Viện Tra Cứu & Tải Văn Bản Sáng Kiến Mẫu Quy Chuẩn")
    st.info("Hệ thống cung cấp sẵn khung nội dung chi tiết bám sát cấu trúc Sáng kiến kinh nghiệm chuẩn giáo dục.")
    
    # Thanh tìm kiếm
    search_query = st.text_input("🔍 Tìm kiếm nhanh tài liệu, sáng kiến (Ví dụ: Toán, STEM, AI...):", "")
    
    # Cơ sở dữ liệu mẫu nội dung chi tiết của các sáng kiến
    library_data = {
        "Toán học": [
            {
                "title": "Biện pháp ứng dụng công nghệ số trong dạy học Hình học lớp 8",
                "author": "Mẫu chuẩn Bộ GD&ĐT",
                "summary": "Giải pháp tập trung vào việc sử dụng các phần mềm hình học động (Geogebra) kết hợp mô hình lớp học đảo ngược nhằm nâng cao tư duy trừu tượng không gian cho học sinh khối 8.",
                "content": """ĐẶT VẤN ĐỀ
1. Lý do chọn đề tài: Hình học lớp 8 (Bộ sách Kết nối tri thức/Chân trời sáng tạo) mang tính trừu tượng cao, học sinh thường gặp khó khăn trong việc hình dung các khối đa diện, định lý Pitago hay tính chất tam giác đồng dạng...
2. Mục đích nghiên cứu: Số hóa quy trình dạy học trực quan.

NỘI DUNG CỐT LÕI
- Biện pháp 1: Thiết kế ngân hàng hình ảnh 3D chuyển động trực quan bằng Geogebra.
- Biện pháp 2: Giao nhiệm vụ tự học qua video ngắn trước khi lên lớp.
- Biện pháp 3: Tổ chức trò chơi khảo sát định lượng trực tuyến toán học."""
            },
            {
                "title": "Phát triển tư duy phản biện qua giải toán có lời văn lớp 8",
                "author": "Mẫu chuẩn tập huấn",
                "summary": "Ứng dụng ma trận câu hỏi gợi mở để học sinh tự phản biện cách giải toán, từ đó tối ưu hóa thuật toán và nâng cao năng lực giải quyết vấn đề.",
                "content": """ĐẶT VẤN ĐỀ
Dạy học giải toán có lời văn không chỉ là tìm ra đáp số mà là quá trình học sinh phân tích giả thuyết, lập luận toán học chuyên sâu.

NỘI DUNG CỐT LÕI
- Sử dụng sơ đồ KWL (Biết - Muốn biết - Đã học được) trong phân tích đề bài.
- Tổ chức kỹ thuật dạy học 'Mảnh ghép' để học sinh tranh biện về các phương án lập phương trình/hệ phương trình."""
            }
        ],
        "Khoa học tự nhiên": [
            {
                "title": "Thiết kế chủ đề STEM nội dung dòng điện lớp 9",
                "author": "Tài liệu mạng lưới giáo viên",
                "summary": "Hướng dẫn chi tiết quy trình 5 bước thiết kế bài học STEM: Chế tạo mô hình đèn ngủ thông minh tiết kiệm điện từ vật liệu tái chế.",
                "content": "Nội dung chi tiết cấu trúc bài học STEM bao gồm: Tiêu chí sản phẩm, Ma trận kiến thức nền (Lý thuyết dòng điện, định luật Ôm) và Biên bản chấm sản phẩm của các nhóm học sinh."
            }
        ],
        "Tin học & Công nghệ": [
            {
                "title": "Xây dựng hệ thống học liệu số và quản lý bài tập với Google Drive",
                "author": "Mẫu sáng kiến Chuyển đổi số",
                "summary": "Giải pháp đồng bộ hóa kho lưu trữ, phân quyền thư mục bài tập cho từng lớp, giúp chấm bài và phản hồi nhanh chóng cho học sinh bằng công nghệ.",
                "content": "Chi tiết cách thiết lập Google Forms chấm tự động, sơ đồ phân quyền thư mục lớp học trên Google Drive và cách tối ưu hóa dung lượng lưu trữ miễn phí cho giáo viên."
            }
        ]
    }
    
    # Hiển thị cấu trúc thư mục
    for cat, topics in library_data.items():
        # Bộ lọc tìm kiếm sơ bộ
        filtered_topics = [t for t in topics if search_query.lower() in t["title"].lower() or search_query.lower() in cat.lower()]
        
        if filtered_topics:
            with st.expander(f"📁 Danh mục Sáng kiến: Môn {cat} ({len(filtered_topics)} tài liệu)"):
                for t in filtered_topics:
                    st.markdown(f"### 📄 {t['title']}")
                    st.caption(f"✍️ Tác giả: {t['author']}")
                    st.write(f"ℹ️ **Tóm tắt giải pháp:** {t['summary']}")
                    
                    # Nút bấm mở rộng xem nội dung chi tiết trực tiếp
                    show_detail = st.checkbox(f"👁️ Xem nội dung chi tiết Sáng kiến", key=t['title'])
                    if show_detail:
                        st.text_area("Nội dung văn bản mẫu:", value=t['content'], height=250)
                        
                        # Tạo tính năng cho phép tải file đính kèm dạng Text/Markdown (hoặc Word nháp)
                        st.download_button(
                            label="📥 Tải file bản nháp (.txt) về máy",
                            data=f"TÊN ĐỀ TÀI: {t['title']}\n\n{t['content']}",
                            file_name=f"{t['title'].replace(' ', '_')}.txt",
                            mime="text/plain"
                        )
                    st.markdown("---")
