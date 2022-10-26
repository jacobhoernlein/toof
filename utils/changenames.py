import json
import sqlite3

conn = sqlite3.connect("toof.sqlite")
with open("names.json") as fp:
    names = json.load(fp)

for id, name in names.items():
    conn.execute(f"UPDATE pics SET name = '{name}' WHERE pic_id = '{id}'")

conn.commit()
conn.close()
