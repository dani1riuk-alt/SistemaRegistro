import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Crear tabla trabajadores
cursor.execute("""
CREATE TABLE IF NOT EXISTS trabajadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ci TEXT UNIQUE,
    nombre TEXT,
    cargo TEXT,
    area TEXT
)
""")

# Crear tabla registros
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

# Insertar trabajador de prueba
cursor.execute("""
INSERT OR IGNORE INTO trabajadores (ci, nombre, cargo, area)
VALUES ('12345678', 'Juan Perez', 'Tecnico', 'Mantenimiento')
""")

conn.commit()
conn.close()

print("Base de datos creada correctamente")