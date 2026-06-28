import json
import random
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp
from io import BytesIO

# 1. Cấu hình cấu trúc đặc thù theo Ma trận định hướng GDPT 2018 (Form 2025)
SUBJECT_CONFIGS = {
    "Toán": {
        "parts": {
            "Phần I: Trắc nghiệm 4 lựa chọn": {"types": ["TN_4_lua_chon"], "weight": 3.0, "desc": "Mỗi câu trả lời đúng được 0.25 điểm"},
            "Phần II: Trắc nghiệm Đúng/Sai": {"types": ["TN_dung_sai"], "weight": 4.0, "desc": "Điểm tối đa một câu là 1.0 điểm (Đúng 1 ý: 0.1, 2 ý: 0.25, 3 ý: 0.5, 4 ý: 1.0)"},
            "Phần III: Trắc nghiệm Trả lời ngắn": {"types": ["TL_ngan"], "weight": 3.0, "desc": "Mỗi câu trả lời đúng được 0.5 điểm"}
        }
    },
    "Tiếng Anh": {
        "parts": {
            "Part 1: Pronunciation & Stress": {"types": ["TN_4_lua_chon"], "weight": 2.0},
            "Part 2: Vocabulary & Grammar": {"types": ["TN_4_lua_chon"], "weight": 3.0},
            "Part 3: Reading Comprehension": {"types": ["Reading_Cloze", "Reading_Text"], "weight": 3.0},
            "Part 4: Writing": {"types": ["Rewrite_Sentence", "Essay"], "weight": 2.0}
        }
    },
    "Ngữ văn": {
        "parts": {
            "Phần I: Đọc hiểu (Ngữ liệu ngoài SGK)": {"types": ["TN_4_lua_chon", "Tu_luan_ngan"], "weight": 4.0},
            "Phần II: Viết (Nghị luận xã hội & Văn học)": {"types": ["Tu_luan"], "weight": 6.0}
        }
    },
    "Lịch sử": {
        "parts": {
            "Phần I: Câu hỏi trắc nghiệm khách quan": {"types": ["TN_4_lua_chon"], "weight": 6.0},
            "Phần II: Tự luận giải thích ý nghĩa/nguyên nhân": {"types": ["Tu_luan"], "weight": 4.0}
        }
    }
}

# 2. Thuật toán đảo đề thông minh (Đảo câu, đảo đáp án tùy thuộc dạng câu hỏi)
def shuffle_exam(selected_questions, code_number):
    random.seed(int(code_number))
    shuffled_list = []
    
    for _, row in selected_questions.iterrows():
        q_item = row.to_dict()
        # Nếu là trắc nghiệm 4 lựa chọn thông thường -> đảo đáp án mẫu ký tự
        if q_item['q_type'] == 'TN_4_lua_chon' and q_item['options']:
            opts = json.loads(q_item['options'])
            random.shuffle(opts)
            q_item['shuffled_options'] = opts
        else:
            q_item['shuffled_options'] = json.loads(q_item['options']) if q_item['options'] else []
            
        shuffled_list.append(q_item)
        
    random.shuffle(shuffled_list) # Đảo thứ tự xuất hiện các câu trong cùng phân khúc
    return shuffled_list

# 3. Động cơ Math tự động sinh Đồ thị hàm số / Hình học trực quan bằng Matplotlib
def generate_math_graph(graph_type="bậc 3"):
    fig, ax = plt.subplots(figsize=(4, 3))
    x = np.linspace(-2.5, 2.5, 400)
    
    if graph_type == "bậc 3":
        y = x**3 - 3*x
        ax.set_title("Đồ thị hàm số $y = x^3 - 3x$")
    elif graph_type == "trùng phương":
        y = x**4 - 2*x**2
        ax.set_title("Đồ thị hàm số $y = x^4 - 2x^2$")
    else:
        y = 1 / (x + 0.001)
        ax.set_title("Đồ thị hàm số phân thức")

    ax.plot(x, y, color='blue', linewidth=2)
    ax.axhline(0, color='black',linewidth=0.8)
    ax.axvline(0, color='black',linewidth=0.8)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_ylim(-4, 4)
    
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf
