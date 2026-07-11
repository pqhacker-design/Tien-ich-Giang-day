import sqlite3
import pandas as pd
import os

class DBManager:
    def __init__(self, db_path="database/school.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Bảng thông tin lớp học (Module 1)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_name TEXT, school_year TEXT, class_name TEXT, 
                    teacher_name TEXT, semester TEXT, subject_name TEXT, level TEXT
                )
            """)
            # Bảng học sinh (Module 2 & 3)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    tx_scores TEXT, -- Lưu dạng chuỗi phân cách dấu phẩy, ví dụ: "8,9,7"
                    gk_score REAL,
                    ck_score REAL,
                    ai_comment TEXT,
                    evaluation_level TEXT
                )
            """)
            conn.commit()

    def import_dataframe(self, df):
        with self.get_connection() as conn:
            df.to_sql("students", conn, if_exists="append", index=False)
