import sqlite3
import os
from datetime import datetime

DB_FILE = "lattice_agents.db"

def init_db():
    """Database initialize karna with auto-migration"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Agents Table (Base creation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            public_key TEXT PRIMARY KEY,
            capabilities TEXT,
            stake REAL DEFAULT 0.0,
            trust_score REAL DEFAULT 50.0,
            tasks_completed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # 2. Task Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            task_name TEXT,
            status TEXT,
            timestamp TEXT
        )
    ''')
    
    # 3. Payments Table (For future use)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            amount REAL,
            payer TEXT,
            timestamp TEXT
        )
    ''')

    # AUTO-MIGRATION: Agar koi column missing hai toh khud add kar do (No need to delete DB!)
    def add_column_if_missing(table, column, type_def):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
            print(f"[DB] Auto-added column: {column} in {table}")

    add_column_if_missing("agents", "capabilities", "TEXT")
    add_column_if_missing("agents", "stake", "REAL DEFAULT 0.0")
    add_column_if_missing("agents", "trust_score", "REAL DEFAULT 50.0")
    add_column_if_missing("agents", "tasks_completed", "INTEGER DEFAULT 0")
    add_column_if_missing("agents", "status", "TEXT DEFAULT 'active'")
    
    conn.commit()
    conn.close()

def save_agent(public_key, capabilities, stake):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO agents (public_key, capabilities, stake, trust_score)
            VALUES (?, ?, ?, ?)
        ''', (public_key, str(capabilities), stake, 50.0))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_agent(public_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM agents WHERE public_key=?', (public_key,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_trust(public_key, new_trust):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE agents SET trust_score=? WHERE public_key=?', (new_trust, public_key))
    conn.commit()
    conn.close()

def log_task(agent_id, task_name, status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO task_logs (agent_id, task_name, status, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (agent_id, task_name, status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_logs(limit=5):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT agent_id, task_name, status, timestamp FROM task_logs ORDER BY id DESC LIMIT ?', (limit,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def add_agent(public_key, capabilities, stake, trust=50.0, tasks=0, status="active"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO agents (public_key, capabilities, stake, trust_score, tasks_completed, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (public_key, str(capabilities), stake, trust, tasks, status))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_status(public_key, new_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE agents SET status=? WHERE public_key=?", (new_status, public_key))
    conn.commit()
    conn.close()

def burn_stake(public_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE agents SET trust_score=0.0, stake=0.0, tasks_completed=0, status='slashed' WHERE public_key=?", (public_key,))
    conn.commit()
    conn.close()

def record_payment(agent_id, amount, payer):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO payments (agent_id, amount, payer, timestamp) VALUES (?, ?, ?, ?)''', 
                   (agent_id, amount, payer, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()