import sqlite3
import json
import os

DB_NAME = "lattice_agents.db"

def init_db():
    """Database initialize karein aur tables banayein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Agar table galat ban gaya ho toh usko drop karke naya banayenge
    cursor.execute('DROP TABLE IF EXISTS agents')
    cursor.execute('DROP TABLE IF EXISTS payments')
    
    # Naya Agents Table
    cursor.execute('''
        CREATE TABLE agents (
            agent_id TEXT PRIMARY KEY,
            public_key TEXT,
            capabilities TEXT,
            trust_score REAL,
            status TEXT,
            stake REAL
        )
    ''')
    
    # Naya Payments Table
    cursor.execute('''
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT,
            amount REAL,
            payer TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized & Refreshed (lattice_agents.db).")

def add_agent(agent_id: str, public_key: str, capabilities: list, trust_score: float, stake: float, status: str):
    """Naya agent database mein add karein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    caps_str = json.dumps(capabilities)
    
    try:
        cursor.execute('''
            INSERT INTO agents (agent_id, public_key, capabilities, trust_score, status, stake)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (agent_id, public_key, caps_str, trust_score, status, stake))
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute('''
            UPDATE agents SET public_key=?, capabilities=?, trust_score=?, status=?, stake=? 
            WHERE agent_id=?
        ''', (public_key, caps_str, trust_score, status, stake, agent_id))
        conn.commit()
    finally:
        conn.close()

def get_agent(agent_id: str):
    """Agent ki details uthayein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT agent_id, public_key, capabilities, trust_score, status, stake FROM agents WHERE agent_id=?', (agent_id,))
    row = cursor.fetchone()
    conn.close()
    
    return row

def update_trust(agent_id: str, new_trust: float):
    """Agent ka trust score update karein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE agents SET trust_score=? WHERE agent_id=?', (new_trust, agent_id))
    conn.commit()
    conn.close()

def update_status(agent_id: str, new_status: str):
    """Agent ka status update karein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE agents SET status=? WHERE agent_id=?', (new_status, agent_id))
    conn.commit()
    conn.close()

def record_payment(agent_id: str, amount: float, payer: str):
    """Payment record karein aur stake update karein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO payments (agent_id, amount, payer) VALUES (?, ?, ?)', (agent_id, amount, payer))
    cursor.execute('UPDATE agents SET stake = stake + ? WHERE agent_id=?', (amount, agent_id))
    
    conn.commit()
    conn.close()

def list_agents(capability: str = "", min_trust: float = 0.0):
    """Agents ko filter karke list karein."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT agent_id, public_key, capabilities, trust_score, status, stake FROM agents WHERE trust_score >= ?', (min_trust,))
    rows = cursor.fetchall()
    conn.close()
    
    filtered_agents = []
    for row in rows:
        caps_list = json.loads(row[2]) if row[2] else []
        if capability == "" or capability in caps_list:
            filtered_agents.append(row)
            
    return filtered_agents