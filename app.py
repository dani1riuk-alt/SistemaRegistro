from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import datetime
import os
import time

from openpyxl import Workbook
from openpyxl.drawing.image import Image

app = Flask(__name__)

# Carpeta de imágenes
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear carpeta si no existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Conexión DB
def get_db():
    return sqlite3.connect('database.db')

# =========================
# 🏠 HOME
# =========================
@app.route('/')
def index():
    return render_template('index.html')

# =========================
# 🔍 VALIDAR CI
# =========================
@app.route('/validar_ci', methods=['POST'])
def validar_ci():
    ci = request.json['ci']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT nombre, cargo, area FROM trabajadores WHERE ci=?", (ci,))
    data = cursor.fetchone()

    if data:
        return jsonify({
            "existe": True,
            "nombre": data[0],
            "cargo": data[1],
            "area": data[2]
        })
    else:
        return jsonify({"existe": False})

# =========================
# 💾 GUARDAR REGISTRO
# =========================
@app.route('/guardar', methods=['POST'])
def guardar():

    ci = request.form['ci']
    descripcion = request.form['descripcion']
    imagen = request.files['imagen']

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM trabajadores WHERE ci=?", (ci,))
    if not cursor.fetchone():
        return "CI NO VALIDO"

    # Nombre único de imagen
    nombre_archivo = str(int(time.time())) + ".png"
    ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)

    imagen.save(ruta)

    ahora = datetime.datetime.now()

    cursor.execute("""
        INSERT INTO registros (fecha, hora, ci, nombre, descripcion, imagen_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (str(ahora.date()), str(ahora.time()), ci, descripcion, ruta))

    db.commit()

    return "OK"

# =========================
# 📊 VER REGISTROS
# =========================
@app.route('/registros')
def ver_registros():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM registros")
    data = cursor.fetchall()

    return render_template('registros.html', registros=data)

# =========================
# 📥 EXPORTAR EXCEL
# =========================
@app.route('/exportar_excel')
def exportar_excel():

    wb = Workbook()
    ws = wb.active
    ws.title = "Registros"

    headers = ["Fecha", "Hora", "CI", "Descripción", "Imagen"]
    ws.append(headers)

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM registros")

    fila = 2

    for row in cursor.fetchall():
        ws.cell(row=fila, column=1, value=row[1])
        ws.cell(row=fila, column=2, value=row[2])
        ws.cell(row=fila, column=3, value=row[3])
        ws.cell(row=fila, column=4, value=row[4])

        try:
            img = Image(row[5])
            img.width = 100
            img.height = 80
            ws.add_image(img, f'E{fila}')
        except:
            pass

        fila += 1

    archivo = "reporte.xlsx"
    wb.save(archivo)

    return send_file(archivo, as_attachment=True)

# =========================
# 👨‍🔧 AGREGAR TRABAJADOR
# =========================
@app.route('/agregar_trabajador', methods=['POST'])
def agregar_trabajador():

    ci = request.form['ci']
    nombre = request.form['nombre']
    cargo = request.form['cargo']
    area = request.form['area']

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
        INSERT INTO trabajadores (ci, nombre, cargo, area)
        VALUES (?, ?, ?, ?)
        """, (ci, nombre, cargo, area))

        db.commit()
        return "OK"

    except:
        return "CI YA EXISTE"

# =========================
# 🧑‍💼 VISTA TRABAJADORES
# =========================
@app.route('/trabajadores')
def trabajadores():
    return render_template('trabajadores.html')

# =========================
# ▶️ RUN
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)