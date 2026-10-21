import sqlite3
from werkzeug.security import generate_password_hash


def preparar_seguridad():
    print("🔄 Conectando a la base de datos...")
    conn = sqlite3.connect("bajas.db")
    cursor = conn.cursor()

    # 1. Crear tabla de Usuarios
    print("🛠️ Creando tabla de usuarios...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nombre_completo TEXT NOT NULL,
            password TEXT NOT NULL,
            rol TEXT NOT NULL -- Puede ser: 'admin', 'editor', 'visor'
        )
    """
    )

    # 2. Crear tabla de Bitácora (Log de movimientos)
    print("🛠️ Creando tabla de bitácora (Log)...")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bitacora (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL,
            accion TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            detalles TEXT
        )
    """
    )

    # 3. Crear el primer Super Administrador (Tú)
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        # Encriptamos la contraseña por seguridad
        hash_pass = generate_password_hash("admin123")
        cursor.execute(
            """
            INSERT INTO usuarios (username, nombre_completo, password, rol) 
            VALUES (?, ?, ?, ?)
        """,
            ("admin", "Super Administrador", hash_pass, "admin"),
        )
        print("✅ ¡Cuenta Maestra creada!")
        print("   -> Usuario: admin")
        print("   -> Clave: admin123")
    else:
        print("ℹ️ La cuenta maestra ya existía.")

    conn.commit()
    conn.close()
    print("-" * 50)
    print("🚀 ¡FASE 1 COMPLETADA! Base de datos lista para la seguridad.")


if __name__ == "__main__":
    preparar_seguridad()
