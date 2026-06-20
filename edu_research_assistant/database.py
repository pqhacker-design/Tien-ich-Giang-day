import sqlite3
import json
from datetime import datetime

DB_NAME = "edu_research.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Bảng lưu trữ dự án nghiên cứu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subject TEXT,
            grade TEXT,
            level TEXT,
            problem TEXT,
            target TEXT,
            keywords TEXT,
            outline TEXT,
            content TEXT,
            stats_data TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_project(title, subject, grade, level, problem, target, keywords, outline="", content="", stats_data=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    stats_str = json.dumps(stats_data) if stats_data else ""
    cursor.execute('''
        INSERT INTO projects (title, subject, grade, level, problem, target, keywords, outline, content, stats_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, subject, grade, level, problem, target, keywords, outline, content, stats_str, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return project_id

def get_all_projects():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, subject, created_at FROM projects ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows
