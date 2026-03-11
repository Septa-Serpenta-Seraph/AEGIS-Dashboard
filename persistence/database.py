"""
SQLite persistence layer for AEGIS Dashboard.
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.environ.get('AEGIS_DB_PATH', 'data/dashboard.db')

def get_db_connection():
    """Return a new SQLite connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Container stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS container_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            container_id TEXT NOT NULL,
            cpu_percent REAL,
            memory_mb REAL,
            network_rx INTEGER,
            network_tx INTEGER
        )
    ''')
    
    # Container snapshots (lightweight container list snapshots)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS container_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            container_id TEXT NOT NULL,
            name TEXT,
            status TEXT,
            image TEXT
        )
    ''')
    
    # Screenshot metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            container_id TEXT,
            filepath TEXT NOT NULL
        )
    ''')
    
    # Chat logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            tokens_used INTEGER,
            cost_usd REAL
        )
    ''')
    
    # Token usage history (Summary level)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model_name TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            cost_usd REAL
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[*] Database initialized at {DB_PATH}")

def insert_container_stats(container_id: str, cpu_percent: float, memory_mb: float,
                           network_rx: int, network_tx: int):
    """Record a container stat snapshot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO container_stats (container_id, cpu_percent, memory_mb, network_rx, network_tx)
        VALUES (?, ?, ?, ?, ?)
    ''', (container_id, cpu_percent, memory_mb, network_rx, network_tx))
    conn.commit()
    conn.close()

def insert_screenshot(filename: str, url: str, container_id: Optional[str], filepath: str):
    """Record screenshot metadata."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO screenshots (filename, url, container_id, filepath)
        VALUES (?, ?, ?, ?)
    ''', (filename, url, container_id, filepath))
    conn.commit()
    conn.close()

def insert_chat_log(session_id: str, message: str, response: str, tokens: int = 0, cost: float = 0.0):
    """Record a chat interaction with token usage."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_logs (session_id, message, response, tokens_used, cost_usd)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, message, response, tokens, cost))
    conn.commit()
    conn.close()

def insert_token_usage(model_name: str, input_tokens: int, output_tokens: int, cost: float):
    """Record a model usage event for cost tracking."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO token_usage (model_name, input_tokens, output_tokens, total_tokens, cost_usd)
        VALUES (?, ?, ?, ?, ?)
    ''', (model_name, input_tokens, output_tokens, input_tokens + output_tokens, cost))
    conn.commit()
    conn.close()

def get_total_cost() -> Dict[str, Any]:
    """Calculate aggregate token usage and cost."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            SUM(total_tokens) as total_tokens, 
            SUM(cost_usd) as total_cost 
        FROM token_usage
    ''')
    row = cursor.fetchone()
    conn.close()
    return {
        "total_tokens": row['total_tokens'] or 0,
        "total_cost": row['total_cost'] or 0.0
    }

def get_container_stats(container_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve historical stats for a container."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM container_stats
        WHERE container_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (container_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_recent_screenshots(limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent screenshot metadata."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM screenshots
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_chat_logs(session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve chat logs, optionally filtered by session."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if session_id:
        cursor.execute('''
            SELECT * FROM chat_logs
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (session_id, limit))
    else:
        cursor.execute('''
            SELECT * FROM chat_logs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def insert_container_snapshot(container_id: str, name: str, status: str, image: str):
    """Record a lightweight container snapshot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO container_snapshots (container_id, name, status, image)
        VALUES (?, ?, ?, ?)
    ''', (container_id, name, status, image))
    conn.commit()
    conn.close()

def get_recent_snapshots(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve recent container snapshots."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM container_snapshots
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Context Persistence (for critical info across wipes) ---
def init_context_table():
    """Create context_notes table if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS context_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("[*] Context persistence table ready")

def insert_context_note(category: str, key: str, value: str, metadata: Optional[str] = None):
    """Store a critical piece of information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO context_notes (category, key, value, metadata)
        VALUES (?, ?, ?, ?)
    ''', (category, key, value, metadata))
    conn.commit()
    conn.close()

def get_context_notes(category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve context notes, optionally filtered by category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute('''
            SELECT * FROM context_notes
            WHERE category = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (category, limit))
    else:
        cursor.execute('''
            SELECT * FROM context_notes
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Initialize on import
init_db()
init_context_table()
