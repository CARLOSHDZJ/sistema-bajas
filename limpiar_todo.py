import os
import sqlite3
import shutil

print("Iniciando protocolo de limpieza profunda... 🧹")

# 1. Vaciar la tabla de solicitudes en la base de datos
try:
    conn = sqlite3.connect("bajas.db")
    # Borramos todas las solicitudes
    conn.execute("DELETE FROM solicitudes")
    # Reseteamos el contador de IDs para que vuelva a empezar en 1
    conn.execute("DELETE FROM sqlite_sequence WHERE name='solicitudes'")
    conn.commit()
    conn.close()
    print("✅ Base de datos 'solicitudes' vaciada y reseteada.")
except Exception as e:
    print(f"❌ Error al limpiar la base de datos: {e}")

# 2. Vaciar la carpeta de PDFs y Fotos
carpeta_uploads = "static/uploads"
try:
    if os.path.exists(carpeta_uploads):
        # Recorremos todo lo que hay en la carpeta y lo borramos
        for archivo in os.listdir(carpeta_uploads):
            ruta_archivo = os.path.join(carpeta_uploads, archivo)
            if os.path.isfile(ruta_archivo):
                os.unlink(ruta_archivo)
        print("✅ Carpeta de expedientes y fotos vaciada por completo.")
    else:
        print("⚠️ La carpeta 'static/uploads' no existe aún.")
except Exception as e:
    print(f"❌ Error al vaciar la carpeta: {e}")

print("\n🚀 ¡LIMPIEZA TOTAL COMPLETADA CON ÉXITO!")
