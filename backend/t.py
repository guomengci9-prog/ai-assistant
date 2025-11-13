import sqlite3
conn = sqlite3.connect("users.db")
conn.execute("ALTER TABLE assistants ADD COLUMN opening_message TEXT DEFAULT ''")
conn.commit()
conn.close()