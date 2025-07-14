import sqlite3

DB_PATH = 'clientes.db'

def recrear_tabla():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Eliminar tabla antigua
    cursor.execute('DROP TABLE IF EXISTS interacciones')

    # Crear nueva tabla con todas las columnas necesarias
    cursor.execute('''
        CREATE TABLE interacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codcliente TEXT NOT NULL,
            empresa TEXT NOT NULL,
            accion TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            entidad TEXT,
            nom_cliente TEXT,
            total_soles REAL,
            monto_cancelacion REAL,
            monto_ofertado REAL,
            estado_pago TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Tabla 'interacciones' recreada correctamente.")

if __name__ == '__main__':
    recrear_tabla()
