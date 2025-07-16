from flask import Flask, request, jsonify, send_from_directory, redirect
import sqlite3
import os
import shutil
from datetime import datetime

# Detectar si estamos en Render y preparar la base de datos
def es_entorno_render():
    return os.environ.get('RENDER', '').lower() == 'true'

# Ruta a la base de datos
if es_entorno_render():
    DATA_PATH = '/data/clientes.db'
    LOCAL_PATH = 'clientes.db'

    # Copiar la base si aún no está en /data
    if not os.path.exists(DATA_PATH) and os.path.exists(LOCAL_PATH):
        shutil.copy(LOCAL_PATH, DATA_PATH)
        print("Base de datos copiada a /data")

    DB_PATH = DATA_PATH
else:
    DB_PATH = 'clientes.db'

print(f"Usando base de datos: {DB_PATH}")

app = Flask(__name__)


def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalizar_empresa(nombre_url):
    mapa_empresas = {
        'caja_cusco': 'Caja Cusco',
        'empresa1': 'Empresa 1',
        'empresa2': 'Empresa 2',
    }
    return mapa_empresas.get(nombre_url, nombre_url)


@app.route('/api/consulta', methods=['POST'])
def api_consulta():
    try:
        data = request.get_json()
        dni = data.get('dni')
        empresa = data.get('empresa')

        if not dni or not empresa:
            return jsonify({'error': 'Faltan parámetros'}), 400

        empresa_normalizada = normalizar_empresa(empresa)
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT empresa, nom_cliente, total_soles, monto_cancelacion, num1
            FROM clientes
            WHERE codcliente = ? AND empresa = ?
        """, (dni, empresa_normalizada))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'error': 'Cliente no encontrado'})

        cliente = dict(row)
        cliente['monto_cancelacion'] = float(cliente.get('monto_cancelacion') or 0)
        cliente['total_soles'] = float(cliente.get('total_soles') or 0)

        cursor.execute("""
            INSERT INTO interacciones (codcliente, nom_cliente, empresa, accion, fecha_hora)
            VALUES (?, ?, ?, ?, ?)
        """, (dni, cliente['nom_cliente'], empresa_normalizada, 'CONSULTA',
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        conn.commit()
        conn.close()

        return jsonify({'cliente': cliente})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/actualizar_accion', methods=['POST'])
def actualizar_accion():
    try:
        data = request.get_json()
        dni = data.get('dni')
        empresa = data.get('empresa')
        accion = data.get('accion')
        estado_pago = data.get('estado_pago')
        monto_ofertado = data.get('monto_ofertado', '')

        if not dni or not empresa or not accion:
            return jsonify({'error': 'Faltan parámetros'}), 400

        empresa_normalizada = normalizar_empresa(empresa)
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nom_cliente, empresa, total_soles, monto_cancelacion
            FROM clientes
            WHERE codcliente = ? AND empresa = ?
        """, (dni, empresa_normalizada))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'error': 'Cliente no encontrado'}), 404

        cliente = dict(row)

        cursor.execute("""
            UPDATE clientes
            SET mejor_gestion = ?, tarea = ?, accion = ?, estado_pago = ?, monto_ofertado = ?
            WHERE codcliente = ? AND empresa = ?
        """, (
            accion,
            estado_pago or '',
            accion,
            estado_pago or '',
            monto_ofertado,
            dni,
            empresa_normalizada
        ))

        cursor.execute("""
            INSERT INTO interacciones (
                codcliente, nom_cliente, empresa, accion, entidad, total_soles,
                monto_cancelacion, monto_ofertado, estado_pago, fecha_hora
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dni,
            cliente['nom_cliente'],
            empresa_normalizada,
            accion,
            cliente['empresa'],
            cliente['total_soles'],
            cliente['monto_cancelacion'],
            monto_ofertado,
            estado_pago or '',
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/interacciones', methods=['GET'])
def obtener_interacciones():
    try:
        empresa_url = request.args.get('empresa', '')
        empresa_normalizada = normalizar_empresa(empresa_url)

        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            WITH ultima_accion AS (
                SELECT i.*
                FROM interacciones i
                INNER JOIN (
                    SELECT codcliente, MAX(fecha_hora) AS max_fecha
                    FROM interacciones
                    WHERE empresa = ?
                    GROUP BY codcliente
                ) ult
                ON i.codcliente = ult.codcliente AND i.fecha_hora = ult.max_fecha
                WHERE i.empresa = ?
            )
            SELECT 
                u.codcliente, u.nom_cliente, u.empresa, u.accion, u.entidad,
                u.total_soles AS deuda,
                c.monto_cancelacion AS monto_base,
                CASE 
                    WHEN u.accion = 'Aceptó' THEN c.monto_cancelacion
                    WHEN u.accion = 'Oferta Enviada' THEN u.monto_ofertado
                    ELSE NULL
                END AS cancelacion,
                u.monto_ofertado AS ofertado,
                u.estado_pago, u.fecha_hora
            FROM ultima_accion u
            LEFT JOIN clientes c ON u.codcliente = c.codcliente AND u.empresa = c.empresa
            ORDER BY u.fecha_hora DESC
        """, (empresa_normalizada, empresa_normalizada))

        data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'interacciones': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# (... continúa con todas las demás rutas exactamente como las tenías ...)
# No las repito para que no se vuelva extremadamente largo el mensaje,
# pero no necesitas modificar nada más de tu código actual.

@app.route('/')
def redireccion_raiz():
    return redirect('/caja_cusco/')


if __name__ == '__main__':
    app.run(debug=True)
