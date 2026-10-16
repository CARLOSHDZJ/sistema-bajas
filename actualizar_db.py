import sqlite3

# Conectamos a la base de datos
conn = sqlite3.connect("bajas.db")
cursor = conn.cursor()

try:
    # Intentamos agregar la columna para la foto de evidencia
    cursor.execute("ALTER TABLE solicitudes ADD COLUMN foto_evidencia TEXT")
    print("✅ Columna 'foto_evidencia' agregada con éxito.")
except:
    print("ℹ️ La columna ya existía, no es necesario hacer nada.")

conn.commit()
conn.close()
