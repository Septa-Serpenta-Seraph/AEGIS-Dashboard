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
            response TEXT NOT NULL
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

def insert_chat_log(session_id: str, message: str, response: str):
    """Record a chat interaction."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_logs (session_id, message, response)
        VALUES (?, ?, ?)
    ''', (session_id, message, response))
    conn.commit()
    conn.close()

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

# Initialize on import
init_db()
