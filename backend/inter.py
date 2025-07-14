import sqlite3

conn = sqlite3.connect('clientes.db')
cursor = conn.cursor()

cursor.execute("SELECT * FROM interacciones ORDER BY fecha_hora DESC")
rows = cursor.fetchall()

print(f"Total de interacciones encontradas: {len(rows)}")
for r in rows:
    print(r)

