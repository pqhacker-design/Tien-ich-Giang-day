import sqlite3
import pandas as pd
import json

DB_NAME = "quiz_bank.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            grade TEXT,
            topic TEXT,
            level TEXT, -- Nhận biết, Thông hiểu, Vận dụng, Vận dụng cao
            q_type TEXT, -- TN_4_lua_chon, TN_dung_sai, TL_ngan, Tu_luan...
            content TEXT,
            options TEXT, -- Chuỗi JSON lưu danh sách đáp án nếu là Trắc nghiệm
            correct_answer TEXT,
            explanation TEXT,
            media_path TEXT
        )
    ''')
    
    # Chèn dữ liệu mẫu nếu database trống
    cursor.execute("SELECT COUNT(*) FROM questions")
    if cursor.fetchone()[0] == 0:
        sample_questions = [
            ("Toán", "Lớp 12", "Hàm số", "Nhận biết", "TN_4_lua_chon", "Hàm số $y = ax^4 + bx^2 + c$ có đồ thị như hình vẽ bên là hàm số nào?", json.dumps(["A. Hàm bậc 4", "B. Hàm bậc 3", "C. Hàm bậc 2", "D. Hàm phân thức"]), "A", "Dựa vào dạng đồ thị hình chữ W.", ""),
            ("Toán", "Lớp 12", "Hình học không gian", "Thông hiểu", "TN_dung_sai", "Cho hình chóp $S.ABC$ có đáy là tam giác đều.", json.dumps(["a) $SA \perp (ABC)$", "b) Tam giác $SBC$ cân tại $S$"]), "a: Đúng, b: Đúng", "Giải thích chi tiết hình học...", ""),
            ("Tiếng Anh", "Lớp 11", "Pronunciation", "Nhận biết", "TN_4_lua_chon", "Choose the word whose underlined part differs from the other three in pronunciation:", json.dumps(["A. achieve", "B. chemistry", "C. cheerful", "D. chief"]), "B", "chemistry phát âm là /k/, các từ còn lại là /tʃ/", ""),
            ("Ngữ văn", "Lớp 10", "Đọc hiểu văn bản", "Thông hiểu", "Tu_luan", "Đọc đoạn trích sau và trả lời câu hỏi: 'Thuyền về có nhớ bến chăng...' Anh/chị hãy chỉ ra biện pháp tu từ được sử dụng.", "", "Biện pháp ẩn dụ (Thuyền, Bến)", "Thuyền chỉ người đi, bến chỉ người ở lại.", "")
        ]
        cursor.executemany('''
            INSERT INTO questions (subject, grade, topic, level, q_type, content, options, correct_answer, explanation, media_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_questions)
        conn.commit()
    conn.close()

def get_questions(subject, grade):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM questions WHERE subject=? AND grade=?", conn, params=(subject, grade))
    conn.close()
    return df

def insert_question(data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions (subject, grade, topic, level, q_type, content, options, correct_answer, explanation, media_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()
