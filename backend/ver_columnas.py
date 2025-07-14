import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect('clientes.db')
cursor = conn.cursor()

# Obtener y mostrar las columnas de la tabla 'clientes'
cursor.execute("PRAGMA table_info(clientes)")
columnas = cursor.fetchall()

print("Columnas en la tabla 'clientes':")
for col in columnas:
    print(f"- {col[1]}")  # col[1] es el nombre de la columna

conn.close()

