import sqlite3
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel

class ProgressState(BaseModel):
    book_id: str
    current_chapter: int
    current_page: int
    max_chapter_reached: int
    updated_at: float

class ProgressTracker:
    def __init__(self, db_path: str = "./data/db/user_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                book_id TEXT PRIMARY KEY,
                current_chapter INTEGER,
                current_page INTEGER,
                max_chapter_reached INTEGER,
                updated_at REAL
            )
        ''')
        conn.commit()
        conn.close()

    def get_progress(self, book_id: str) -> ProgressState:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM progress WHERE book_id = ?', (book_id,))
        row = c.fetchone()
        conn.close()

        if row:
            return ProgressState(
                book_id=row[0],
                current_chapter=row[1],
                current_page=row[2],
                max_chapter_reached=row[3],
                updated_at=row[4]
            )
        else:
            # Default state
            return ProgressState(
                book_id=book_id,
                current_chapter=1,
                current_page=1,
                max_chapter_reached=1,
                updated_at=time.time()
            )

    def update_progress(self, book_id: str, chapter: int, page: int):
        current = self.get_progress(book_id)
        max_chap = max(current.max_chapter_reached, chapter)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO progress 
            (book_id, current_chapter, current_page, max_chapter_reached, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (book_id, chapter, page, max_chap, time.time()))
        conn.commit()
        conn.close()
        
        return self.get_progress(book_id)

tracker = ProgressTracker()
