import sqlite3
import pandas as pd

# Leer el Excel
df = pd.read_excel('clientes.xlsx', dtype=str)

# Renombrar columnas para que coincidan con la base (opcional, si quieres usar minúsculas sin espacios)
df.columns = [
    'empresa', 'nom_cliente', 'codcliente', 'estado_civil', 'edad', 'sueldo',
    'reporte_centrales', 'rango_mora', 'situacion', 'fecha_trabajo',
    'capital_soles', 'total_soles', 'porcentaje_descuento', 'monto_cancelacion',
    'mejor_gestion', 'fecha_mejor_gestion', 'tarea', 'asignacion', 'num1', 'num2',
    'rango_deuda', 'grupo', 'rango_edad', 'sexo', 'grupos', 'socio', 'datos',
    'contacto', 'segmento_contacto', 'total_contacto', 'perfilamiento',
    'telefono_search', 'fecha_data_search', 'domicilio_departamento',
    'domicilio_provincia', 'domicilio_ciudad', 'domicilio_comercial'
]

conn = sqlite3.connect('clientes.db')
cur = conn.cursor()

for index, row in df.iterrows():
    # Convertir la fila a tupla
    data = tuple(row[col] for col in df.columns)

    # Preparar valores para UPDATE:
    # Quitamos 'empresa' (pos 0) y 'codcliente' (pos 2) para el SET
    valores_update = list(data)
    codcliente = valores_update.pop(2)  # codcliente
    empresa = valores_update.pop(0)     # empresa

    # 35 valores para SET + 2 para WHERE = 37 en total

    # Verificar si el cliente ya existe
    cur.execute("SELECT 1 FROM clientes WHERE codcliente=? AND empresa=?", (codcliente, empresa))
    existe = cur.fetchone()

    if existe:
        # Actualizar fila existente
        cur.execute(f"""
            UPDATE clientes SET
                nom_cliente=?, estado_civil=?, edad=?, sueldo=?, reporte_centrales=?,
                rango_mora=?, situacion=?, fecha_trabajo=?, capital_soles=?, total_soles=?,
                porcentaje_descuento=?, monto_cancelacion=?, mejor_gestion=?, fecha_mejor_gestion=?,
                tarea=?, asignacion=?, num1=?, num2=?, rango_deuda=?, grupo=?, rango_edad=?,
                sexo=?, grupos=?, socio=?, datos=?, contacto=?, segmento_contacto=?,
                total_contacto=?, perfilamiento=?, telefono_search=?, fecha_data_search=?,
                domicilio_departamento=?, domicilio_provincia=?, domicilio_ciudad=?, domicilio_comercial=?
            WHERE codcliente=? AND empresa=?
        """, valores_update + [codcliente, empresa])
    else:
        # Insertar nuevo registro completo
        cur.execute(f"""
            INSERT INTO clientes (
                empresa, nom_cliente, codcliente, estado_civil, edad, sueldo, reporte_centrales,
                rango_mora, situacion, fecha_trabajo, capital_soles, total_soles,
                porcentaje_descuento, monto_cancelacion, mejor_gestion, fecha_mejor_gestion,
                tarea, asignacion, num1, num2, rango_deuda, grupo, rango_edad, sexo,
                grupos, socio, datos, contacto, segmento_contacto, total_contacto,
                perfilamiento, telefono_search, fecha_data_search,
                domicilio_departamento, domicilio_provincia, domicilio_ciudad, domicilio_comercial
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

conn.commit()
conn.close()

print("✅ Datos importados o actualizados correctamente.")
