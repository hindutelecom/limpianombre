from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template_string
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_super_secreta'
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')
        if usuario == 'admin' and clave == 'zangano1234':
            session['usuario'] = usuario
            return redirect(url_for('panel_admin', empresa='caja_cusco'))
        else:
            return 'Credenciales incorrectas', 401

    return render_template_string("""
        <form method="post">
            <input type="text" name="usuario" placeholder="Usuario"><br>
            <input type="password" name="clave" placeholder="Contraseña"><br>
            <button type="submit">Ingresar</button>
        </form>
    """)


@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))


@app.route('/<empresa>/administrador.html')
def panel_admin(empresa):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    ruta = os.path.join('frontend', 'empresas', empresa)
    return send_from_directory(ruta, 'administrador.html')


@app.route('/<empresa>/dashboard.html')
def panel_dashboard(empresa):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    ruta = os.path.join('frontend', 'empresas', empresa)
    return send_from_directory(ruta, 'dashboard.html')


@app.route('/<empresa>/historial_sms.html')
def panel_sms(empresa):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    ruta = os.path.join('frontend', 'empresas', empresa)
    return send_from_directory(ruta, 'historial_sms.html')


@app.route('/api/consulta', methods=['POST'])
# (rest of the code unchanged)
# ...

@app.route('/')
def redireccion_raiz():
    return redirect('/caja_cusco/')


if __name__ == '__main__':
    app.run(debug=True)
