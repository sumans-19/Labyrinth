import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(__file__), "labyrinth.db")

def get_connection():
    # check_same_thread=False allows using the same connection across different FastAPI async threads
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Initializes the SQLite database with the attack_logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attack_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip TEXT,
            endpoint TEXT,
            token_type TEXT,
            threat_score INTEGER,
            threat_level TEXT,
            user_agent TEXT,
            reasons TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_attack(ip: str, endpoint: str, token_type: str, threat_score: int, threat_level: str, user_agent: str, reasons: List[str]):
    """Logs an attack event into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    reasons_str = ",".join(reasons)
    cursor.execute('''
        INSERT INTO attack_logs (timestamp, ip, endpoint, token_type, threat_score, threat_level, user_agent, reasons)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, ip, endpoint, token_type, threat_score, threat_level, user_agent, reasons_str))
    conn.commit()
    conn.close()

def get_all_logs() -> List[Dict[str, Any]]:
    """Retrieves all attack logs from the database."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM attack_logs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize database on module import
init_db()
