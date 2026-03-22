import sqlite3
import json
from datetime import datetime

def init_db():
    conn = sqlite3.connect('parliament.db')
    c = conn.cursor()
    # Upgraded table with new columns for topics and fact_checks
    c.execute('''
        CREATE TABLE IF NOT EXISTS speeches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            transcript TEXT,
            sentiment TEXT,
            keywords TEXT,
            promises TEXT,
            topics TEXT,
            fact_checks TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_speech(transcript, sentiment, keywords, promises, topics, fact_checks):
    conn = sqlite3.connect('parliament.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    c.execute('''
        INSERT INTO speeches (timestamp, transcript, sentiment, keywords, promises, topics, fact_checks)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, transcript, sentiment, json.dumps(keywords), json.dumps(promises), json.dumps(topics), json.dumps(fact_checks)))
    
    conn.commit()
    conn.close()

def get_all_speeches():
    conn = sqlite3.connect('parliament.db')
    c = conn.cursor()
    c.execute('SELECT * FROM speeches ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()
    return rows