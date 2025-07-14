import sqlite3

DB_PATH = 'clientes.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(sms_enviados);")
columnas = cursor.fetchall()

print("📋 Columnas en la tabla sms_enviados:")
for col in columnas:
    print(f"- {col[1]}")

conn.close()

