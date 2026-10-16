import sqlite3

# Nos conectamos a la base de datos
conn = sqlite3.connect("bajas.db")
cursor = conn.cursor()

try:
    # 1. Borramos absolutamente todas las solicitudes
    cursor.execute("DELETE FROM solicitudes")

    # 2. Reiniciamos el contador de IDs para que vuelva a empezar en 1
    cursor.execute('DELETE FROM sqlite_sequence WHERE name="solicitudes"')

    conn.commit()
    print("✅ Tabla de solicitudes vaciada correctamente.")
    print("🚀 ¡Ya puedes correr tu archivo importar_excel.py!")

except Exception as e:
    print(f"❌ Hubo un error: {e}")
finally:
    conn.close()
