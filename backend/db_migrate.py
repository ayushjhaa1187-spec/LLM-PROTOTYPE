import sqlite3
import json

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE documents ADD COLUMN sha256 VARCHAR(64)")
except Exception as e:
    print(e)
    
try:
    cursor.execute("ALTER TABLE documents ADD COLUMN metadata_json JSON")
except Exception as e:
    print(e)

conn.commit()
conn.close()
