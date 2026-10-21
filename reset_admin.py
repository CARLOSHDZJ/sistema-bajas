import sqlite3
from werkzeug.security import generate_password_hash

# 1. Cambia esto por el nombre exacto de tu archivo de base de datos (ej. 'sistema.db')
nombre_bd = 'bajas.db'

# 2. Escribe la nueva contraseña que usarás para entrar al panel web
nueva_contrasena = "AdminWeb2026!" 
hash_nuevo = generate_password_hash(nueva_contrasena)

try:
    conexion = sqlite3.connect(nombre_bd)
    cursor = conexion.cursor()

    # 3. La consulta ya está lista apuntando a la columna 'username'
    consulta = '''
        UPDATE usuarios 
        SET password = ? 
        WHERE username = 'admin'
    '''
    
    cursor.execute(consulta, (hash_nuevo,))
    conexion.commit()
    
    if cursor.rowcount > 0:
        print("¡Listo! La contraseña web del administrador ha sido restablecida.")
    else:
        print("No se encontró el usuario 'admin'. Verifica el nombre de la tabla de usuarios.")

except sqlite3.Error as error:
    print("Ocurrió un error al conectar con SQLite:", error)

finally:
    if conexion:
        conexion.close()