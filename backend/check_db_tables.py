import sqlite3
from pathlib import Path

# Check both database files
db_paths = [
    Path("D:/back/chromatography_system/backend/data/database/chromatography.db"),
    Path("D:/back/chromatography_system/data/database/chromatography.db")
]

for db_path in db_paths:
    print(f"\nChecking: {db_path}")
    print("-" * 60)
    if db_path.exists():
        print(f"  File exists, size: {db_path.stat().st_size / 1024:.2f} KB")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"  Tables: {[t[0] for t in tables]}")
        conn.close()
    else:
        print(f"  File does not exist")