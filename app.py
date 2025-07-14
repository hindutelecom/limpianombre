Podrias actualizar mi app.py
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = 'clientes.db'

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

@app.route('/api/enviar_sms', methods=['POST'])
def enviar_sms():
    try:
        data = request.get_json()
        dni = data.get('dni')
        empresa = data.get('empresa')
        mensaje = data.get('mensaje')

        print("📨 Datos recibidos en /api/enviar_sms:", data)

        if not dni or not empresa or not mensaje:
            return jsonify({'error': 'Faltan parámetros'}), 400

        empresa_normalizada = normalizar_empresa(empresa)
        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT num1 FROM clientes
            WHERE codcliente = ? AND empresa = ?
        """, (dni, empresa_normalizada))
        row = cursor.fetchone()

        if not row or not row['num1']:
            conn.close()
            return jsonify({'error': 'Número de teléfono no encontrado'}), 404

        numero = row['num1']

        cursor.execute("""
            INSERT INTO sms_enviados (dni, empresa, mensaje, telefono, accion, fecha_hora)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            dni,
            empresa_normalizada,
            mensaje,
            numero,
            'Simulado',
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'mensaje': 'SMS simulado enviado correctamente.'})

    except Exception as e:
        print("🔥 Error en /api/enviar_sms:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/api/sms')
def obtener_sms():
    try:
        empresa = request.args.get('empresa')
        if not empresa:
            return jsonify({'error': 'Falta parámetro empresa'}), 400

        empresa_normalizada = normalizar_empresa(empresa)

        conn = conectar_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT dni, telefono, mensaje, empresa, accion, fecha_hora
            FROM sms_enviados
            WHERE empresa = ?
            ORDER BY fecha_hora DESC
        """, (empresa_normalizada,))

        filas = cursor.fetchall()
        conn.close()

        sms = [dict(fila) for fila in filas]
        return jsonify({'sms': sms})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/<empresa>/')
def servir_index_empresa(empresa):
    ruta = os.path.join('frontend', 'empresas', empresa)
    archivo = os.path.join(ruta, 'index.html')
    if os.path.exists(archivo):
        return send_from_directory(ruta, 'index.html')
    return "Empresa no encontrada", 404

@app.route('/<empresa>/<path:filename>')
def archivos_estaticos_empresa(empresa, filename):
    ruta = os.path.join('frontend', 'empresas', empresa)
    return send_from_directory(ruta, filename)

@app.route('/api/dashboard')
def dashboard():
    try:
        empresa = request.args.get('empresa')
        if not empresa:
            return jsonify({'error': 'Falta parámetro empresa'}), 400

        empresa_normalizada = normalizar_empresa(empresa)
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
                COUNT(*) AS total,
                SUM(CASE WHEN accion = 'CONSULTA' THEN 1 ELSE 0 END) AS consultas,
                SUM(CASE WHEN accion = 'Aceptó' THEN 1 ELSE 0 END) AS aceptados,
                SUM(CASE WHEN accion = 'Oferta Enviada' THEN 1 ELSE 0 END) AS ofertaron,
                SUM(CASE WHEN accion = 'No Aceptó' THEN 1 ELSE 0 END) AS no_aceptaron,
                SUM(CASE WHEN estado_pago = 'Pagado' THEN 1 ELSE 0 END) AS pagados,
                SUM(CASE WHEN estado_pago = 'Pendiente' THEN 1 ELSE 0 END) AS pendientes,
                SUM(CASE WHEN estado_pago = 'Pagado' THEN
                    CASE WHEN accion = 'Aceptó' THEN c.monto_cancelacion
                         WHEN accion = 'Oferta Enviada' THEN i.monto_ofertado
                         ELSE 0 END
                    ELSE 0 END
                ) AS monto_pagado,
                SUM(CASE WHEN estado_pago = 'Pendiente' THEN
                    CASE WHEN accion = 'Aceptó' THEN c.monto_cancelacion
                         WHEN accion = 'Oferta Enviada' THEN i.monto_ofertado
                         ELSE 0 END
                    ELSE 0 END
                ) AS monto_pendiente
            FROM ultima_accion i
            LEFT JOIN clientes c ON i.codcliente = c.codcliente AND i.empresa = c.empresa
        """, (empresa_normalizada, empresa_normalizada))

        row = cursor.fetchone()
        conn.close()
        return jsonify(dict(row))

    except Exception as e:
        return jsonify({'error': str(e)}), 500

from flask import redirect

@app.route('/')
def redireccion_raiz():
    return redirect('/caja_cusco/')


if __name__ == '__main__':
    app.run(debug=True)