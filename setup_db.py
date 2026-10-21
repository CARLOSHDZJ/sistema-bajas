import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect("bajas.db")
cursor = conn.cursor()

# Crear la tabla con TODAS las columnas (incluyendo estatus y fotos)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS solicitudes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ct TEXT NOT NULL,
        fecha_recibido TEXT NOT NULL,
        region TEXT NOT NULL,
        cantidad_bienes INTEGER NOT NULL,
        municipio TEXT NOT NULL,
        localidad TEXT NOT NULL,
        contacto TEXT NOT NULL,
        correo TEXT,
        recibio TEXT NOT NULL,
        en_bodega TEXT,
        faltantes TEXT,
        nombre_expediente TEXT,
        tipo_documento TEXT,
        observaciones TEXT,
        fecha_programada TEXT,
        observaciones_extra TEXT,
        foto_evidencia TEXT,
        estatus TEXT DEFAULT 'Pendiente'  -- ¡ESTA FALTABA!
    )
"""
)

conn.commit()
conn.close()
print("✅ Base de datos REPARADA (Incluye columna ESTATUS y FOTOS).")
