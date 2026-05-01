import pandas as pd
import sqlite3

# Leer Excel
df = pd.read_excel("trabajadores.xlsx")

# Conectar base de datos
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

for index, row in df.iterrows():
    try:
        cursor.execute("""
        INSERT INTO trabajadores (ci, nombre, cargo, area)
        VALUES (?, ?, ?, ?)
        """, (
            str(row['CI']),
            row['NOMBRE'],
            row['CARGO'],
            row['ÁREA']
        ))
    except:
        print(f"CI duplicado: {row['CI']}")

conn.commit()
conn.close()

print("Trabajadores importados correctamente")