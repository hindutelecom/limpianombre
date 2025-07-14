import sqlite3

conn = sqlite3.connect('../clientes.db')
cursor = conn.cursor()

# Añadir columna 'accion'
try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN accion TEXT")
    print("Columna 'accion' agregada.")
except sqlite3.OperationalError:
    print("La columna 'accion' ya existe.")

# Añadir columna 'estado_pago'
try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN estado_pago TEXT")
    print("Columna 'estado_pago' agregada.")
except sqlite3.OperationalError:
    print("La columna 'estado_pago' ya existe.")

# Añadir columna 'fecha'
try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN fecha TEXT")
    print("Columna 'fecha' agregada.")
except sqlite3.OperationalError:
    print("La columna 'fecha' ya existe.")

conn.commit()
conn.close()
print("Actualización completada.")
