     1|"""
     2|SQLite persistence layer for AEGIS Dashboard.
     3|"""
     4|import sqlite3
     5|import os
     6|from datetime import datetime
     7|from typing import Optional, List, Dict, Any
     8|
     9|DB_PATH = os.environ.get('AEGIS_DB_PATH', 'data/dashboard.db')
    10|
    11|def get_db_connection():
    12|    """Return a new SQLite connection."""
    13|    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn
    17|
    18|def init_db():
    19|    """Create tables if they don't exist."""
    20|    conn = get_db_connection()
    21|    cursor = conn.cursor()
    22|    
    23|    # Container stats
    24|    cursor.execute('''
    25|        CREATE TABLE IF NOT EXISTS container_stats (
    26|            id INTEGER PRIMARY KEY AUTOINCREMENT,
    27|            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    28|            container_id TEXT NOT NULL,
    29|            cpu_percent REAL,
    30|            memory_mb REAL,
    31|            network_rx INTEGER,
    32|            network_tx INTEGER
    33|        )
    34|    ''')
    35|    
    36|    # Container snapshots (lightweight container list snapshots)
    37|    cursor.execute('''
    38|        CREATE TABLE IF NOT EXISTS container_snapshots (
    39|            id INTEGER PRIMARY KEY AUTOINCREMENT,
    40|            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    41|            container_id TEXT NOT NULL,
    42|            name TEXT,
    43|            status TEXT,
    44|            image TEXT
    45|        )
    46|    ''')
    47|    
    48|    # Screenshot metadata
    49|    cursor.execute('''
    50|        CREATE TABLE IF NOT EXISTS screenshots (
    51|            id INTEGER PRIMARY KEY AUTOINCREMENT,
    52|            filename TEXT NOT NULL,
    53|            url TEXT,
    54|            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    55|            container_id TEXT,
    56|            filepath TEXT NOT NULL
    57|        )
    58|    ''')
    59|    
    60|    # Chat logs
    61|    cursor.execute('''
    62|        CREATE TABLE IF NOT EXISTS chat_logs (
    63|            id INTEGER PRIMARY KEY AUTOINCREMENT,
    64|            session_id TEXT,
    65|            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    66|            message TEXT NOT NULL,
    67|            response TEXT NOT NULL,
    68|            tokens_used INTEGER,
    69|            cost_usd REAL
    70|        )
    71|    ''')
    72|    
    73|    # Token usage history (Summary level)
    74|    cursor.execute('''
    75|        CREATE TABLE IF NOT EXISTS token_usage (
    76|            id INTEGER PRIMARY KEY AUTOINCREMENT,
    77|            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    78|            model_name TEXT,
    79|            input_tokens INTEGER,
    80|            output_tokens INTEGER,
    81|            total_tokens INTEGER,
    82|            cost_usd REAL
    83|        )
    84|    ''')
    85|    
    86|    conn.commit()
    87|    conn.close()
    88|    print(f"[*] Database initialized at {DB_PATH}")
    89|
    90|def insert_container_stats(container_id: str, cpu_percent: float, memory_mb: float,
    91|                           network_rx: int, network_tx: int):
    92|    """Record a container stat snapshot."""
    93|    conn = get_db_connection()
    94|    cursor = conn.cursor()
    95|    cursor.execute('''
    96|        INSERT INTO container_stats (container_id, cpu_percent, memory_mb, network_rx, network_tx)
    97|        VALUES (?, ?, ?, ?, ?)
    98|    ''', (container_id, cpu_percent, memory_mb, network_rx, network_tx))
    99|    conn.commit()
   100|    conn.close()
   101|
   102|def insert_screenshot(filename: str, url: str, container_id: Optional[str], filepath: str):
   103|    """Record screenshot metadata."""
   104|    conn = get_db_connection()
   105|    cursor = conn.cursor()
   106|    cursor.execute('''
   107|        INSERT INTO screenshots (filename, url, container_id, filepath)
   108|        VALUES (?, ?, ?, ?)
   109|    ''', (filename, url, container_id, filepath))
   110|    conn.commit()
   111|    conn.close()
   112|
   113|def insert_chat_log(session_id: str, message: str, response: str, tokens: int = 0, cost: float = 0.0):
   114|    """Record a chat interaction with token usage."""
   115|    conn = get_db_connection()
   116|    cursor = conn.cursor()
   117|    cursor.execute('''
   118|        INSERT INTO chat_logs (session_id, message, response, tokens_used, cost_usd)
   119|        VALUES (?, ?, ?, ?, ?)
   120|    ''', (session_id, message, response, tokens, cost))
   121|    conn.commit()
   122|    conn.close()
   123|
   124|def insert_token_usage(model_name: str, input_tokens: int, output_tokens: int, cost: float):
   125|    """Record a model usage event for cost tracking."""
   126|    conn = get_db_connection()
   127|    cursor = conn.cursor()
   128|    cursor.execute('''
   129|        INSERT INTO token_usage (model_name, input_tokens, output_tokens, total_tokens, cost_usd)
   130|        VALUES (?, ?, ?, ?, ?)
   131|    ''', (model_name, input_tokens, output_tokens, input_tokens + output_tokens, cost))
   132|    conn.commit()
   133|    conn.close()
   134|
   135|def get_total_cost() -> Dict[str, Any]:
   136|    """Calculate aggregate token usage and cost."""
   137|    conn = get_db_connection()
   138|    cursor = conn.cursor()
   139|    cursor.execute('''
   140|        SELECT 
   141|            SUM(total_tokens) as total_tokens, 
   142|            SUM(cost_usd) as total_cost 
   143|        FROM token_usage
   144|    ''')
   145|    row = cursor.fetchone()
   146|    conn.close()
   147|    return {
   148|        "total_tokens": row['total_tokens'] or 0,
   149|        "total_cost": row['total_cost'] or 0.0
   150|    }
   151|
   152|def get_container_stats(container_id: str, limit: int = 100) -> List[Dict[str, Any]]:
   153|    """Retrieve historical stats for a container."""
   154|    conn = get_db_connection()
   155|    cursor = conn.cursor()
   156|    cursor.execute('''
   157|        SELECT * FROM container_stats
   158|        WHERE container_id = ?
   159|        ORDER BY timestamp DESC
   160|        LIMIT ?
   161|    ''', (container_id, limit))
   162|    rows = cursor.fetchall()
   163|    conn.close()
   164|    return [dict(row) for row in rows]
   165|
   166|def get_recent_screenshots(limit: int = 20) -> List[Dict[str, Any]]:
   167|    """Retrieve recent screenshot metadata."""
   168|    conn = get_db_connection()
   169|    cursor = conn.cursor()
   170|    cursor.execute('''
   171|        SELECT * FROM screenshots
   172|        ORDER BY timestamp DESC
   173|        LIMIT ?
   174|    ''', (limit,))
   175|    rows = cursor.fetchall()
   176|    conn.close()
   177|    return [dict(row) for row in rows]
   178|
   179|def get_chat_logs(session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
   180|    """Retrieve chat logs, optionally filtered by session."""
   181|    conn = get_db_connection()
   182|    cursor = conn.cursor()
   183|    if session_id:
   184|        cursor.execute('''
   185|            SELECT * FROM chat_logs
   186|            WHERE session_id = ?
   187|            ORDER BY timestamp DESC
   188|            LIMIT ?
   189|        ''', (session_id, limit))
   190|    else:
   191|        cursor.execute('''
   192|            SELECT * FROM chat_logs
   193|            ORDER BY timestamp DESC
   194|            LIMIT ?
   195|        ''', (limit,))
   196|    rows = cursor.fetchall()
   197|    conn.close()
   198|    return [dict(row) for row in rows]
   199|
   200|def insert_container_snapshot(container_id: str, name: str, status: str, image: str):
   201|    """Record a lightweight container snapshot."""
   202|    conn = get_db_connection()
   203|    cursor = conn.cursor()
   204|    cursor.execute('''
   205|        INSERT INTO container_snapshots (container_id, name, status, image)
   206|        VALUES (?, ?, ?, ?)
   207|    ''', (container_id, name, status, image))
   208|    conn.commit()
   209|    conn.close()
   210|
   211|def get_recent_snapshots(limit: int = 100) -> List[Dict[str, Any]]:
   212|    """Retrieve recent container snapshots."""
   213|    conn = get_db_connection()
   214|    cursor = conn.cursor()
   215|    cursor.execute('''
   216|        SELECT * FROM container_snapshots
   217|        ORDER BY timestamp DESC
   218|        LIMIT ?
   219|    ''', (limit,))
   220|    rows = cursor.fetchall()
   221|    conn.close()
   222|    return [dict(row) for row in rows]
   223|
   224|# --- Context Persistence (for critical info across wipes) ---
   225|def init_context_table():
   226|    """Create context_notes table if not exists."""
   227|    conn = get_db_connection()
   228|    cursor = conn.cursor()
   229|    cursor.execute('''
   230|        CREATE TABLE IF NOT EXISTS context_notes (
   231|            id INTEGER PRIMARY KEY AUTOINCREMENT,
   232|            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
   233|            category TEXT NOT NULL,
   234|            key TEXT NOT NULL,
   235|            value TEXT,
   236|            metadata TEXT
   237|        )
   238|    ''')
   239|    conn.commit()
   240|    conn.close()
   241|    print("[*] Context persistence table ready")
   242|
   243|def insert_context_note(category: str, key: str, value: str, metadata: Optional[str] = None):
   244|    """Store a critical piece of information."""
   245|    conn = get_db_connection()
   246|    cursor = conn.cursor()
   247|    cursor.execute('''
   248|        INSERT INTO context_notes (category, key, value, metadata)
   249|        VALUES (?, ?, ?, ?)
   250|    ''', (category, key, value, metadata))
   251|    conn.commit()
   252|    conn.close()
   253|
   254|def get_context_notes(category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
   255|    """Retrieve context notes, optionally filtered by category."""
   256|    conn = get_db_connection()
   257|    cursor = conn.cursor()
   258|    if category:
   259|        cursor.execute('''
   260|            SELECT * FROM context_notes
   261|            WHERE category = ?
   262|            ORDER BY timestamp DESC
   263|            LIMIT ?
   264|        ''', (category, limit))
   265|    else:
   266|        cursor.execute('''
   267|            SELECT * FROM context_notes
   268|            ORDER BY timestamp DESC
   269|            LIMIT ?
   270|        ''', (limit,))
   271|    rows = cursor.fetchall()
   272|    conn.close()
   273|    return [dict(row) for row in rows]
   274|
   275|def delete_context_note(note_id: int) -> bool:
   276|    """Delete a context note by ID. Returns True if deleted."""
   277|    conn = get_db_connection()
   278|    cursor = conn.cursor()
   279|    cursor.execute('DELETE FROM context_notes WHERE id = ?', (note_id,))
   280|    conn.commit()
   281|    deleted = cursor.rowcount > 0
   282|    conn.close()
   283|    return deleted
   284|
   285|# Initialize on import
   286|init_db()
   287|init_context_table()
   288|

def get_context_note_by_id(note_id):
    """Fetch a single context note by its ID using direct DB query."""
    conn = None
    try:
        conn = _get_connection()
        row = conn.execute(
            "SELECT id, content, timestamp, tags FROM memories WHERE id = ? AND type = 'context_note'",
            (note_id,)
        ).fetchone()
        if row:
            return {
                'id': row[0],
                'content': row[1],
                'timestamp': row[2],
                'tags': json.loads(row[3]) if row[3] else []
            }
        return None
    finally:
        if conn:
            conn.close()

