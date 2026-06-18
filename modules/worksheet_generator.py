def generate_digital_worksheet(lesson_json):
    """Sinh nội dung chi tiết cho Phiếu học tập 4.0 đính kèm ứng dụng công nghệ"""
    info = lesson_json.get("thong_tin_chung", {})
    topic = info.get("ten_bai_hoc", "Chủ đề bài học")
    grade = info.get("lop", "Tất cả các khối")
    
    worksheet = {
        "title": f"PHIẾU HỌC TẬP SỐ: {topic.upper()} - {grade.upper()}",
        "phieu_ca_nhan": [
            "Nhiệm vụ 1: Đọc thông tin sách giáo khoa và hoàn thành sơ đồ tư duy số sau.",
            "Nhiệm vụ 2: Truy cập đường link phần mềm mô phỏng bài học, ghi lại 3 hiện tượng quan sát được."
        ],
        "phieu_nhom": [
            "Nhiệm vụ nhóm: Thảo luận trên không gian Padlet chung, đưa ra giải pháp giải quyết tình huống thực tế của bài dạy.",
            "Sản phẩm yêu cầu: Thiết kế 1 trang Canva thuyết trình đại diện nhóm."
        ],
        "interactive_quiz": [
            {"cau_hoi": "Câu hỏi 1 (Mức Nhận biết): Khái niệm cốt lõi nào đúng?", "dap_an": "Đáp án đúng theo SGK"},
            {"cau_hoi": "Câu hỏi 2 (Mức Thông hiểu): Tại sao cần ứng dụng công cụ số trong tình huống này?", "dap_an": "Giải thích bản chất hành vi"}
        ]
    }
    return worksheet