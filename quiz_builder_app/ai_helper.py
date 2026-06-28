import time

def generate_ai_question(subject, topic, level, q_type):
    """
    Hệ thống Mock AI Engine. Bạn chỉ cần thay thế phần return bằng 
    gọi API thực tế (như OpenAI, Gemini API hoặc các mô hình mã nguồn mở).
    """
    # Mô phỏng thời gian xử lý của mạng neural
    time.sleep(1) 
    
    if subject == "Toán":
        content = f"Một vật chuyển động theo quy luật $s(t) = -t^3 + 9t^2$. Tính vận tốc lớn nhất của vật trong khoảng thời gian 5 giây đầu tiên?"
        options = ["A. $27 m/s$", "B. $36 m/s$", "C. $45 m/s$", "D. $54 m/s$"]
        answer = "A"
        explanation = "Vận tốc là đạo hàm bậc nhất của quãng đường: $v(t) = s'(t) = -3t^2 + 18t$. Tìm GTLN của hàm bậc 2 trên $[0, 5]$ tại đỉnh $t=3 \\Rightarrow v(3) = 27$."
    elif subject == "Ngữ văn":
        content = f"Đọc đoạn thơ sau: 'Cha lại dắt con đi trên cát mịn / Ánh nắng chảy đầy vai...' (Hoàng Trung Thông). Hãy viết đoạn văn ngắn (150 chữ) nêu cảm nhận về tình cha con."
        options = []
        answer = "Xem hướng dẫn chấm chi tiết."
        explanation = "Yêu cầu học sinh làm rõ: Tình cảm gắn kết thiêng liêng, hình ảnh thơ giàu tính gợi hình, biểu cảm."
    else:
        content = f"AI Generated Question for {subject} - Topic: {topic} ({level})"
        options = ["Option A", "Option B", "Option C", "Option D"]
        answer = "A"
        explanation = "Giải thích tự động từ AI."

    return {
        "content": content,
        "options": options,
        "answer": answer,
        "explanation": explanation
    }
