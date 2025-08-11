import sqlite3
import json
import os

# Check backend database
backend_db = "backend/wellness.db"
if os.path.exists(backend_db):
    conn = sqlite3.connect(backend_db)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"Backend DB tables: {tables}")
    
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} records")
        if count > 0 and table == 'blink_events':
            rows = conn.execute(f"SELECT * FROM {table} LIMIT 3").fetchall()
            print(f"Sample {table} data: {rows}")
    conn.close()

# Check desktop app database
desktop_db = "src/desktop_app/data/local.db"
if os.path.exists(desktop_db):
    conn = sqlite3.connect(desktop_db)
    tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(f"\nDesktop DB tables: {tables}")
    
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} records")
    conn.close()

# Check for JSON files
data_dir = "data"
if os.path.exists(data_dir):
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    print(f"\nJSON files in data/: {json_files}")
    
# Check desktop app data dir
desktop_data_dir = "src/desktop_app/data"
if os.path.exists(desktop_data_dir):
    files = os.listdir(desktop_data_dir)
    print(f"\nDesktop app data files: {files}")
