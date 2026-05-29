import sqlite3
conn = sqlite3.connect('db_data/db.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name='local_pdv_configlocal';")
print(cur.fetchone())

cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name='local_pdv_pagamentopix';")
print(cur.fetchone())
