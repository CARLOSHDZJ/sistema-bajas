import os
import io
import zipfile
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from importar_excel import importar_de_excel
import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "demo_secret_key_sistema_bajas")
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS Y FUNCIONES EXTRA
# ==============================================================================

def get_db_connection():
    conn = sqlite3.connect("bajas.db", timeout=20.0)
    conn.execute("PRAGMA journal_mode=wal")
    conn.row_factory = sqlite3.Row
    return conn

def calcular_dias(fecha_str):
    if not fecha_str:
        return 0
    try:
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        return (datetime.now() - fecha_dt).days
    except:
        return 0

def registrar_bitacora(usuario, accion, detalles):
    conn = get_db_connection()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO bitacora (usuario, accion, detalles, fecha) VALUES (?, ?, ?, ?)",
        (usuario, accion, detalles, ahora),
    )
    conn.commit()
    conn.close()

# ==============================================================================
# RUTA 1: SISTEMA DE LOGIN Y LOGOUT
# ==============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if usuario and check_password_hash(usuario["password"], password):
            session["usuario_id"] = usuario["id"]
            session["username"] = usuario["username"]
            session["rol"] = usuario["rol"]
            session["nombre_completo"] = usuario["nombre_completo"]
            registrar_bitacora(usuario["username"], "INICIO SESIÓN", "Acceso exitoso")
            return redirect(url_for("index"))
        error = "Usuario o contraseña incorrectos."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    if "username" in session:
        registrar_bitacora(session["username"], "CERRÓ SESIÓN", "Salida del sistema")
    session.clear()
    return redirect(url_for("login"))

# ==============================================================================
# RUTA 2: DASHBOARD PRINCIPAL (Solicitudes Pendientes)
# ==============================================================================

@app.route("/")
def index():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    solicitudes_db = conn.execute(
        "SELECT * FROM solicitudes WHERE estatus != 'Finalizado' ORDER BY fecha_recibido ASC"
    ).fetchall()
    conn.close()
    solicitudes = []
    for sol in solicitudes_db:
        item = dict(sol)
        item["dias_transcurridos"] = calcular_dias(sol["fecha_recibido"])
        solicitudes.append(item)
    return render_template("index.html", solicitudes=solicitudes)

# ==============================================================================
# RUTA 3: HISTORIAL (Solicitudes Finalizadas)
# ==============================================================================

@app.route("/historial")
def historial():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    solicitudes = conn.execute(
        "SELECT * FROM solicitudes WHERE estatus = 'Finalizado' ORDER BY fecha_recibido DESC"
    ).fetchall()
    conn.close()
    return render_template("historial.html", solicitudes=solicitudes)

@app.route("/eliminar_historial/<int:id>")
def eliminar_historial(id):
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("historial"))

    conn = get_db_connection()
    solicitud = conn.execute(
        "SELECT ct FROM solicitudes WHERE id = ?", (id,)
    ).fetchone()

    if solicitud:
        conn.execute("DELETE FROM solicitudes WHERE id = ?", (id,))
        conn.commit()
        registrar_bitacora(
            session["username"],
            "ELIMINAR HISTORIAL",
            f"Borrado definitivo de solicitud CT: {solicitud['ct']}",
        )
    conn.close()
    return redirect(url_for("historial"))

# ==============================================================================
# RUTA 4: REPORTES Y ESTADÍSTICAS
# ==============================================================================

@app.route("/reportes")
def reportes():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    por_mes = conn.execute(
        """
        SELECT 
            UPPER(region) as region, 
            COUNT(*) as recibidas,
            SUM(CASE WHEN estatus = 'Finalizado' THEN 1 ELSE 0 END) as finalizadas, 
            SUM(cantidad_bienes) as total_bienes
        FROM solicitudes 
        GROUP BY UPPER(region) 
        ORDER BY region ASC
    """
    ).fetchall()
    por_estatus = conn.execute(
        "SELECT estatus, COUNT(*) as total FROM solicitudes GROUP BY estatus"
    ).fetchall()
    conn.close()
    return render_template("reportes.html", por_mes=por_mes, por_estatus=por_estatus)

# ==============================================================================
# RUTA 5: OPERACIONES (Nueva, Editar, Finalizar)
# ==============================================================================

@app.route("/nueva", methods=("GET", "POST"))
def nueva_solicitud():
    if "usuario_id" not in session or session.get("rol") == "visor":
        return redirect(url_for("index"))
    if request.method == "POST":
        ct = request.form["ct"].upper()
        fecha_recibido = request.form["fecha_recibido"]
        en_bodega = request.form.get("en_bodega", "no")
        faltantes = request.form.get("faltantes", "no")
        cantidad = request.form["cantidad_bienes"]
        region = request.form["region"].upper()
        localidad = request.form["localidad"].upper()
        municipio = request.form["municipio"].upper()
        contacto = request.form["contacto"].upper()
        correo = request.form["correo"].upper()
        observaciones = request.form["observaciones"].upper()
        recibio = request.form["recibio"].upper()
        tipo_doc = request.form["tipo_documento"]

        archivo = request.files["expediente"]
        nombre_archivo = None
        if archivo and archivo.filename != "":
            nombre_seguro = secure_filename(archivo.filename)
            nombre_final = f"{ct}_{fecha_recibido}_{nombre_seguro}"
            archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_final))
            nombre_archivo = nombre_final

        conn = get_db_connection()
        conn.execute(
            """INSERT INTO solicitudes (ct, fecha_recibido, en_bodega, faltantes, cantidad_bienes, region, 
            localidad, municipio, contacto, correo, observaciones, recibio, tipo_documento, nombre_expediente) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ct, fecha_recibido, en_bodega, faltantes, cantidad, region, localidad, municipio, contacto, correo, observaciones, recibio, tipo_doc, nombre_archivo),
        )
        conn.commit()
        conn.close()
        registrar_bitacora(session["username"], "NUEVA SOLICITUD", f"Creó nueva solicitud para CT: {ct}")
        return redirect("/")
    return render_template("form.html")

@app.route("/api/check_ct/<ct>")
def check_ct(ct):
    if "usuario_id" not in session:
        return {"existe": False}
    conn = get_db_connection()
    # Verifica si existe alguna solicitud con ese CT
    cuenta = conn.execute("SELECT COUNT(*) FROM solicitudes WHERE ct = ?", (ct.upper(),)).fetchone()[0]
    conn.close()
    return {"existe": cuenta > 0}


@app.route("/editar/<int:id>", methods=("GET", "POST"))
def editar(id):
    if "usuario_id" not in session or session.get("rol") == "visor":
        return redirect(url_for("index"))

    conn = get_db_connection()
    solicitud = conn.execute("SELECT * FROM solicitudes WHERE id = ?", (id,)).fetchone()

    if request.method == "POST":
        ct_nuevo = request.form["ct"].upper()
        fecha_nueva = request.form["fecha_recibido"]
        cantidad_nueva = request.form["cantidad_bienes"]
        municipio_nuevo = request.form["municipio"].upper()
        region_nueva = request.form["region"].upper() # <--- ¡Aquí está la magia de la región!
        contacto_nuevo = request.form["contacto"].upper()
        observaciones_nuevas = request.form["observaciones"].upper()

        archivo_pdf = request.files.get("pdf")
        nombre_final = None

        if archivo_pdf and archivo_pdf.filename != "":
            nombre_seguro = secure_filename(archivo_pdf.filename)
            nombre_final = f"{ct_nuevo}_{fecha_nueva}_CORREGIDO_{nombre_seguro}"
            archivo_pdf.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_final))
            
            # ¡Se incluye 'region' en el UPDATE!
            conn.execute(
                """UPDATE solicitudes 
                   SET ct = ?, fecha_recibido = ?, cantidad_bienes = ?, municipio = ?, region = ?, 
                       contacto = ?, observaciones = ?, nombre_expediente = ? 
                   WHERE id = ?""",
                (ct_nuevo, fecha_nueva, cantidad_nueva, municipio_nuevo, region_nueva, 
                 contacto_nuevo, observaciones_nuevas, nombre_final, id),
            )
            detalles_bitacora = f"Editó datos, región ({region_nueva}) y actualizó PDF del ID: {id}"
        else:
            # ¡Se incluye 'region' en el UPDATE!
            conn.execute(
                """UPDATE solicitudes 
                   SET ct = ?, fecha_recibido = ?, cantidad_bienes = ?, municipio = ?, region = ?, 
                       contacto = ?, observaciones = ? 
                   WHERE id = ?""",
                (ct_nuevo, fecha_nueva, cantidad_nueva, municipio_nuevo, region_nueva, 
                 contacto_nuevo, observaciones_nuevas, id),
            )
            detalles_bitacora = f"Editó datos base y región ({region_nueva}) del ID: {id}"

        conn.commit()
        conn.close()

        registrar_bitacora(session["username"], "EDITAR DATOS", detalles_bitacora)
        return redirect("/")

    conn.close()
    return render_template("editar.html", solicitud=solicitud)

@app.route("/actualizar/<int:id>", methods=["POST"])
def actualizar(id):
    if "usuario_id" not in session:
        return redirect(url_for("index"))
    fecha_p = request.form["fecha_programada"]
    obs = request.form["observaciones_extra"].upper()
    archivo = request.files.get("foto_evidencia")
    nombre_foto = None
    conn = get_db_connection()
    
    # Obtener el CT para el log de la bitacora
    solicitud = conn.execute("SELECT ct FROM solicitudes WHERE id = ?", (id,)).fetchone()
    ct_str = solicitud["ct"] if solicitud else f"ID {id}"
    
    if archivo and archivo.filename != "":
        nombre_foto = f"EVIDENCIA_{id}_{secure_filename(archivo.filename)}"
        archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_foto))
        conn.execute(
            "UPDATE solicitudes SET fecha_programada=?, observaciones_extra=?, foto_evidencia=? WHERE id=?",
            (fecha_p, obs, nombre_foto, id),
        )
        foto_log = "[FOTO SUBIDA]"
    else:
        conn.execute(
            "UPDATE solicitudes SET fecha_programada=?, observaciones_extra=? WHERE id=?",
            (fecha_p, obs, id),
        )
        foto_log = ""
    conn.commit()
    conn.close()
    
    # Construir un mensaje detallado
    detalles = f"CT: {ct_str}"
    if fecha_p:
        detalles += f" | Fecha: {fecha_p}"
    if obs:
        detalles += f" | Obs: {obs}"
    if foto_log:
        detalles += f" {foto_log}"
        
    registrar_bitacora(session["username"], "ACTUALIZAR NOTA/FOTO", detalles)
    return redirect("/")

@app.route("/finalizar/<int:id>")
def finalizar(id):
    if "usuario_id" not in session or session.get("rol") == "visor":
        return redirect(url_for("index"))
    conn = get_db_connection()
    conn.execute("UPDATE solicitudes SET estatus = 'Finalizado' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    registrar_bitacora(session["username"], "FINALIZAR", f"ID: {id}")
    return redirect("/")

# ==============================================================================
# RUTA 6: PANEL DE ADMINISTRADOR (Usuarios y Bitácora)
# ==============================================================================

@app.route("/admin", methods=["GET", "POST"])
def panel_admin():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    conn = get_db_connection()
    if request.method == "POST":
        username = request.form["username"]
        nombre = request.form["nombre_completo"]
        password = request.form["password"]
        rol = request.form["rol"]
        hash_pass = generate_password_hash(password)
        try:
            conn.execute(
                "INSERT INTO usuarios (username, nombre_completo, password, rol) VALUES (?, ?, ?, ?)",
                (username, nombre, hash_pass, rol),
            )
            conn.commit()
            registrar_bitacora(session["username"], "CREAR USUARIO", f"Creó a: {username}")
        except:
            pass
    usuarios = conn.execute("SELECT id, username, nombre_completo, rol FROM usuarios").fetchall()
    bitacora = conn.execute("SELECT * FROM bitacora ORDER BY fecha DESC LIMIT 100").fetchall()
    conn.close()
    return render_template("admin.html", usuarios=usuarios, bitacora=bitacora)

@app.route("/editar_usuario/<int:id>", methods=["POST"])
def editar_usuario(id):
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    nuevo_rol = request.form.get("rol")
    nueva_pass = request.form.get("password")
    conn = get_db_connection()
    if nueva_pass and nueva_pass.strip() != "":
        hash_p = generate_password_hash(nueva_pass)
        conn.execute(
            "UPDATE usuarios SET password = ?, rol = ? WHERE id = ?",
            (hash_p, nuevo_rol, id),
        )
        detalles = f"Cambió clave y rol a {nuevo_rol}"
    else:
        conn.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (nuevo_rol, id))
        detalles = f"Cambió rol a {nuevo_rol}"
    conn.commit()
    u = conn.execute("SELECT username FROM usuarios WHERE id = ?", (id,)).fetchone()
    registrar_bitacora(session["username"], "EDITAR USUARIO", f"{detalles} para {u['username']}")
    conn.close()
    return redirect(url_for("panel_admin"))

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    conn = get_db_connection()
    u = conn.execute("SELECT username FROM usuarios WHERE id = ?", (id,)).fetchone()
    if u and u["username"] != "admin":
        conn.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        conn.commit()
        registrar_bitacora(session["username"], "ELIMINAR USUARIO", f"Eliminó a {u['username']}")
    conn.close()
    return redirect(url_for("panel_admin"))

@app.route("/admin/imprimir_bitacora")
def imprimir_bitacora():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    conn = get_db_connection()
    bitacora = conn.execute("SELECT * FROM bitacora ORDER BY fecha DESC").fetchall()
    conn.close()
    return render_template("imprimir_bitacora.html", bitacora=bitacora)

@app.route("/admin/limpiar_bitacora")
def limpiar_bitacora():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    conn = get_db_connection()
    conn.execute("DELETE FROM bitacora")
    conn.commit()
    conn.close()
    registrar_bitacora(session["username"], "LIMPIEZA", "Vació el historial")
    return redirect(url_for("panel_admin"))

@app.route("/admin/respaldo")
def descargar_respaldo():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists("bajas.db"):
            zf.write("bajas.db", "bajas_respaldo.db")
        carpeta_uploads = app.config["UPLOAD_FOLDER"]
        if os.path.exists(carpeta_uploads):
            for raiz, dirs, archivos in os.walk(carpeta_uploads):
                for archivo in archivos:
                    ruta_completa = os.path.join(raiz, archivo)
                    ruta_relativa = os.path.relpath(ruta_completa, "static")
                    zf.write(ruta_completa, ruta_relativa)
    memory_file.seek(0)
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    nombre_zip = f"Respaldo_Sistema_Bajas_{fecha_hoy}.zip"
    registrar_bitacora(session["username"], "RESPALDO", "Descargó copia de seguridad total en ZIP")
    return send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=nombre_zip,
    )

@app.route("/admin/subir_db", methods=["POST"])
def subir_db():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    
    if "archivo_excel" not in request.files:
        flash("No se subió ningún archivo.", "error")
        return redirect(url_for("panel_admin"))
        
    archivo = request.files["archivo_excel"]
    if archivo.filename == "":
        flash("Nombre de archivo vacío.", "error")
        return redirect(url_for("panel_admin"))
        
    if archivo and archivo.filename.endswith(".xlsx"):
        nombre_seguro = secure_filename(archivo.filename)
        ruta_temporal = os.path.join(app.config["UPLOAD_FOLDER"], f"temp_{nombre_seguro}")
        archivo.save(ruta_temporal)
        
        exito, mensaje = importar_de_excel(ruta_temporal)
        
        # Eliminar el archivo temporal
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
            
        if exito:
            flash(mensaje, "success")
            registrar_bitacora(session["username"], "IMPORTACIÓN EXCEL", mensaje)
        else:
            flash(mensaje, "error")
            registrar_bitacora(session["username"], "ERROR IMPORTACIÓN EXCEL", mensaje)
    else:
        flash("Formato de archivo no permitido. Debe ser un archivo Excel (.xlsx).", "error")
        
    return redirect(url_for("panel_admin"))

@app.route("/admin/limpiar_todo")
def limpiar_todo():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("index"))
    
    try:
        # 1. Vaciar la tabla de solicitudes en la base de datos
        conn = get_db_connection()
        conn.execute("DELETE FROM solicitudes")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='solicitudes'")
        conn.commit()
        conn.close()
        
        # 2. Vaciar la carpeta de PDFs y Fotos
        carpeta_uploads = app.config["UPLOAD_FOLDER"]
        eliminados = 0
        if os.path.exists(carpeta_uploads):
            for archivo in os.listdir(carpeta_uploads):
                ruta_archivo = os.path.join(carpeta_uploads, archivo)
                if os.path.isfile(ruta_archivo):
                    os.unlink(ruta_archivo)
                    eliminados += 1
                    
        mensaje = "Base de datos de solicitudes vaciada y carpeta de expedientes limpia por completo."
        flash(mensaje, "success")
        registrar_bitacora(session["username"], "LIMPIEZA TOTAL", f"Vació solicitudes y borró {eliminados} archivos adjuntos")
    except Exception as e:
        mensaje_error = f"Error al realizar la limpieza total: {e}"
        flash(mensaje_error, "error")
        registrar_bitacora(session["username"], "ERROR LIMPIEZA TOTAL", mensaje_error)
        
    return redirect(url_for("panel_admin"))

@app.route("/cambiar_password", methods=["GET", "POST"])
def cambiar_password():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
        
    if request.method == "POST":
        pass_actual = request.form["pass_actual"]
        pass_nuevo = request.form["pass_nuevo"]
        pass_confirmar = request.form["pass_confirmar"]
        
        if pass_nuevo != pass_confirmar:
            flash("La nueva contraseña y su confirmación no coinciden.", "error")
            return render_template("cambiar_password.html")
            
        conn = get_db_connection()
        usuario = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (session["usuario_id"],)
        ).fetchone()
        
        if not usuario or not check_password_hash(usuario["password"], pass_actual):
            conn.close()
            flash("La contraseña actual es incorrecta.", "error")
            return render_template("cambiar_password.html")
            
        hash_nuevo = generate_password_hash(pass_nuevo)
        conn.execute(
            "UPDATE usuarios SET password = ? WHERE id = ?", (hash_nuevo, session["usuario_id"])
        )
        conn.commit()
        conn.close()
        
        registrar_bitacora(session["username"], "CAMBIO CONTRASEÑA", "El usuario cambió su propia contraseña")
        flash("Contraseña actualizada con éxito.", "success")
        return redirect(url_for("index"))
        
    return render_template("cambiar_password.html")

# ==============================================================================
# INICIO DEL SERVIDOR
# ==============================================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)