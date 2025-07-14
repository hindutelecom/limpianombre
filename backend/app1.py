from flask import Flask, request, jsonify, send_from_directory, abort
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

DB_PATH = 'clientes.db'  # ajusta si está en otra ruta

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Ruta para servir archivos estáticos y página principal por empresa
@app.route('/<empresa>/')
def serve_index(empresa):
    base_path = os.path.join('..', 'frontend', 'empresas', empresa)
    if not os.path.exists(base_path):
        abort(404)
    return send_from_directory(base_path, 'index.html')

@app.route('/<empresa>/<path:filename>')
def serve_static(empresa, filename):
    base_path = os.path.join('..', 'frontend', 'empresas', empresa)
    if not os.path.exists(os.path.join(base_path, filename)):
        abort(404)
    return send_from_directory(base_path, filename)

# API consulta deuda
@app.route('/<empresa>/api/consulta', methods=['POST'])
def consulta(empresa):
    data = request.json
    dni = data.get('dni', '').strip()
    if not dni or not empresa:
        return jsonify({'error': 'Datos incompletos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM clientes
        WHERE codcliente = ? AND TRIM(LOWER(empresa)) = TRIM(LOWER(?))
    ''', (dni, empresa))
    cliente = cursor.fetchone()

    if cliente is None:
        conn.close()
        return jsonify({'error': 'Cliente no encontrado'}), 404

    # Registrar interacción: Consulta
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO interacciones 
        (dni, nombre, accion, entidad, deuda_total, monto_cancelacion, oferta_mostrada, monto_ofertado, fecha_hora, estado_pago)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        cliente['codcliente'],
        cliente['nom_cliente'],
        'Consulta',
        cliente['empresa'],
        cliente['total_soles'],
        cliente['monto_cancelacion'],
        None,
        None,
        now,
        ''
    ))
    conn.commit()
    conn.close()

    return jsonify({'cliente': dict(cliente)})

# API actualizar acción (Aceptar / No aceptar / Oferta enviada, etc)
@app.route('/<empresa>/api/actualizar_accion', methods=['POST'])
def actualizar_accion(empresa):
    data = request.json
    dni = data.get('dni')
    accion = data.get('accion')
    estado_pago = data.get('estado_pago', '')
    monto_ofertado = data.get('monto_ofertado')

    if not dni or not empresa or not accion:
        return jsonify({'error': 'Datos incompletos'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM clientes WHERE codcliente = ? AND TRIM(LOWER(empresa)) = TRIM(LOWER(?))
    ''', (dni, empresa))
    cliente = cursor.fetchone()

    if cliente is None:
        conn.close()
        return jsonify({'error': 'Cliente no encontrado'}), 404

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO interacciones
        (dni, nombre, accion, entidad, deuda_total, monto_cancelacion, oferta_mostrada, monto_ofertado, fecha_hora, estado_pago)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        cliente['codcliente'],
        cliente['nom_cliente'],
        accion,
        cliente['empresa'],
        cliente['total_soles'],
        cliente['monto_cancelacion'],
        float(cliente['monto_cancelacion']) * 1.15,  # ejemplo oferta mostrada 15% más
        monto_ofertado,
        now,
        estado_pago
    ))
    conn.commit()
    conn.close()
    return jsonify({'mensaje': 'Acción registrada'})

if __name__ == '__main__':
    app.run(debug=True)
