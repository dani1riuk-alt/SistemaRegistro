from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import datetime
import os
import time

from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment

# 📧 CORREO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# 🖼️ IMAGEN
from PIL import Image as PILImage, ImageDraw

app = Flask(__name__)

# =========================
# 🔥 CREAR BASE DE DATOS
# =========================
def crear_db():
    db = sqlite3.connect('database.db')
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trabajadores (
        ci TEXT PRIMARY KEY,
        nombre TEXT,
        cargo TEXT,
        area TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registros (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        hora TEXT,
        ci TEXT,
        descripcion TEXT,
        imagen_url TEXT
    )
    """)

    db.commit()
    db.close()

crear_db()

# =========================
# 📁 Carpeta de imágenes
# =========================
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# =========================
# 🔌 DB
# =========================
def get_db():
    return sqlite3.connect('database.db')

# =========================
# 🖼️ CREAR IMAGEN REPORTE
# =========================
def crear_reporte_imagen(ci, nombre, descripcion, ruta_imagen):

    img = PILImage.new('RGB', (700, 450), color='white')
    draw = ImageDraw.Draw(img)

    texto = f"""REPORTE DE ANOMALIA

CI: {ci}
Nombre: {nombre}

Descripcion:
{descripcion}
"""

    draw.text((20, 20), texto, fill='black')

    try:
        if os.path.exists(ruta_imagen):
            foto = PILImage.open(ruta_imagen)
            foto = foto.resize((250, 180))
            img.paste(foto, (400, 220))
    except Exception as e:
        print("ERROR IMAGEN:", e)

    ruta_final = f"reporte_{int(time.time())}.png"
    img.save(ruta_final)

    return ruta_final

# =========================
# 📧 ENVIAR CORREO
# =========================
def enviar_correo_imagen(ruta_imagen):

    remitente = "dani1riuk@gmail.com"
    clave = "TU_CLAVE_APP"  # 🔥 REEMPLAZA ESTO

    destinatario = "dani1riuk@gmail.com"

    msg = MIMEMultipart()
    msg['Subject'] = "🚨 Nuevo reporte registrado"
    msg['From'] = remitente
    msg['To'] = destinatario

    with open(ruta_imagen, 'rb') as f:
        img = MIMEImage(f.read())
        msg.attach(img)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(remitente, clave)
    server.send_message(msg)
    server.quit()

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
# 💾 GUARDAR
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

    # Guardar imagen
    nombre_archivo = str(int(time.time())) + ".png"
    ruta = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
    imagen.save(ruta)

    ahora = datetime.datetime.now()

    cursor.execute("""
        INSERT INTO registros (fecha, hora, ci, descripcion, imagen_url)
        VALUES (?, ?, ?, ?, ?)
    """, (str(ahora.date()), str(ahora.time()), ci, descripcion, ruta))

    db.commit()

    # Obtener nombre
    cursor.execute("SELECT nombre FROM trabajadores WHERE ci=?", (ci,))
    nombre = cursor.fetchone()[0]

    # 🔥 PROTEGIDO (NO ROMPE)
    try:
        ruta_reporte = crear_reporte_imagen(ci, nombre, descripcion, ruta)
        enviar_correo_imagen(ruta_reporte)
    except Exception as e:
        print("ERROR CORREO:", e)

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

    ws.append(["Fecha", "Hora", "CI", "Nombre", "Descripción", "Imagen"])

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT r.fecha, r.hora, r.ci, t.nombre, r.descripcion, r.imagen_url
        FROM registros r
        LEFT JOIN trabajadores t ON r.ci = t.ci
    """)

    fila = 2

    for row in cursor.fetchall():

        ws.cell(row=fila, column=1, value=row[0])
        ws.cell(row=fila, column=2, value=row[1])
        ws.cell(row=fila, column=3, value=row[2])
        ws.cell(row=fila, column=4, value=row[3])
        ws.cell(row=fila, column=5, value=row[4])

        try:
            if row[5] and os.path.exists(row[5]):
                img = Image(row[5])
                img.width = 100
                img.height = 80
                ws.add_image(img, f'F{fila}')
        except Exception as e:
            print("ERROR EXCEL IMG:", e)

        fila += 1

    # Formato
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 25
    ws.column_dimensions['E'].width = 40
    ws.column_dimensions['F'].width = 20

    for i in range(2, fila):
        ws.row_dimensions[i].height = 80

    for row in ws.iter_rows(min_row=2, max_row=fila, min_col=1, max_col=5):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True)

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
# ▶️ RUN
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)