import sqlite3
conn = sqlite3.connect('db_data/db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cur.fetchall())
