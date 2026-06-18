def get_digital_competency_framework(level):
    """Trả về khung năng lực số chi tiết phù hợp với cấp học hành chính"""
    framework = {
        "Tiểu học": {
            "Khai thác thông tin": "Biết tìm kiếm thông tin an toàn trên Internet với từ khóa đơn giản.",
            "Giao tiếp hợp tác": "Sử dụng hòm thư điện tử học tập hoặc phòng học trực tuyến dưới sự hướng dẫn.",
            "Sáng tạo nội dung": "Tạo bài trình chiếu đơn giản, vẽ hình kỹ thuật số cơ bản.",
            "An toàn số": "Bảo vệ thông tin cá nhân, không chia sẻ mật khẩu tài khoản học tập.",
            "Giải quyết vấn đề": "Sử dụng công cụ phần mềm hỗ trợ học tập theo hướng dẫn trực quan."
        },
        "THCS": {
            "Khai thác thông tin": "Đánh giá độ tin cậy của thông tin số, lọc và phân loại dữ liệu.",
            "Giao tiếp hợp tác": "Hợp tác nhóm trực tuyến thông qua các nền tảng đám mây (Google Drive, MS Teams).",
            "Sáng tạo nội dung": "Thiết kế nội dung số đa phương tiện (Canva, biên tập video bài học ngắn).",
            "An toàn số": "Nhận diện hành vi lừa đảo mạng, bảo mật thiết bị học tập cá nhân.",
            "Giải quyết vấn đề": "Ứng dụng các công cụ AI hỗ trợ tự học, khai thác phần mềm giả lập (GeoGebra, PhET)."
        },
        "THPT": {
            "Khai thác thông tin": "Phân tích, xử lý dữ liệu số phức tạp, nghiên cứu học liệu mở chính thống.",
            "Giao tiếp hợp tác": "Quản trị dự án học tập nhóm trực tuyến, tương tác chuyên nghiệp trên không gian mạng.",
            "Sáng tạo nội dung": "Xây dựng sản phẩm số hoàn chỉnh, lập trình cơ bản, sử dụng AI có trách nhiệm và tôn trọng bản quyền.",
            "An toàn số": "Hiểu luật an ninh mạng, xây dựng định danh số cá nhân an toàn, tích cực.",
            "Giải quyết vấn đề": "Tự động hóa tác vụ học tập, khai thác thuật toán AI để giải quyết bài toán thực tế."
        }
    }
    return framework.get(level, framework["THCS"])