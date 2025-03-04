import sqlite3
import json
from datetime import datetime, timedelta
import threading

class SQLiteCache:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.db_name = "cache.db"
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at TIMESTAMP
                )
            """)
    
    def set(self, key: str, value: any, expires_in: int = 3600):
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), expires_at.isoformat())
            )
    
    def get(self, key: str) -> any:
        with sqlite3.connect(self.db_name) as conn:
            result = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,)
            ).fetchone()
            
            if result is None:
                return None
                
            value, expires_at = result
            if datetime.fromisoformat(expires_at) < datetime.utcnow():
                self.delete(key)
                return None
                
            return json.loads(value)
    
    def delete(self, key: str):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))

cache = SQLiteCache()