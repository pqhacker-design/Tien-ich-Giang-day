import sqlite3
import json
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="classroom_ai.db"):
        # Lấy đường dẫn tuyệt đối của thư mục chứa file db_manager.py hiện tại
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Đảm bảo file DB sẽ luôn nằm chung thư mục với file db_manager.py
        self.db_path = os.path.join(current_dir, db_name)
        
        # Khởi tạo DB
        self.init_db()

    def get_connection(self):
        # Đảm bảo thư mục chứa file DB thực sự tồn tại trước khi kết nối
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Bảng lưu lịch sử sinh nội dung từ AI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject TEXT,
                    grade TEXT,
                    topic TEXT,
                    activity_type TEXT,
                    generated_content TEXT,
                    created_at TIMESTAMP
                )
            ''')
            # Bảng lưu cấu hình trò chơi tương tác trực tiếp
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT,
                    title TEXT,
                    config_json TEXT,
                    is_favorite INTEGER DEFAULT 0,
                    created_at TIMESTAMP
                )
            ''')
            conn.commit()

    def save_history(self, subject, grade, topic, activity_type, content):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO generation_history (subject, grade, topic, activity_type, generated_content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (subject, grade, topic, activity_type, json.dumps(content, ensure_ascii=False), datetime.now())
            )
            conn.commit()

    def save_game(self, game_type, title, config_dict, is_favorite=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO custom_games (game_type, title, config_json, is_favorite, created_at) VALUES (?, ?, ?, ?, ?)",
                (game_type, title, json.dumps(config_dict, ensure_ascii=False), is_favorite, datetime.now())
            )
            conn.commit()
