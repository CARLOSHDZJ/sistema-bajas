import pandas as pd
import sqlite3
from datetime import datetime

def importar_de_excel(ruta_archivo):
    # 1. Leemos el Excel
    try:
        df = pd.read_excel(ruta_archivo)
        # Rellenamos los espacios vacíos con texto vacío para que no de error
        df = df.fillna("")
    except Exception as e:
        return False, f"Error al leer el archivo Excel: {e}"

    # 2. Conectamos a la Base de Datos
    try:
        conn = sqlite3.connect("bajas.db")
        c = conn.cursor()
        
        # 3. Recorremos el Excel fila por fila
        count = 0
        errores = 0
        advertencias_duplicados = 0
        for index, row in df.iterrows():
            try:
                # Limpieza de fecha
                fecha_raw = row.get("FECHA DE RECIBIDO")
                fecha_final = datetime.now().strftime("%Y-%m-%d")  # Por defecto hoy si falla
        
                if pd.notnull(fecha_raw) and fecha_raw != "":
                    try:
                        fecha_final = pd.to_datetime(fecha_raw).strftime("%Y-%m-%d")
                    except:
                        pass
        
                ct_val = str(row.get("CT", "")).strip().upper()
                
                # Check for duplicate
                existe = c.execute("SELECT COUNT(*) FROM solicitudes WHERE ct = ?", (ct_val,)).fetchone()[0]
                if existe > 0:
                    advertencias_duplicados += 1
                
                c.execute(
                    """
                    INSERT INTO solicitudes (
                        ct, fecha_recibido, en_bodega, faltantes, cantidad_bienes, 
                        region, localidad, municipio, contacto, correo, 
                        observaciones, recibio, tipo_documento, estatus
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ct_val,
                        fecha_final,
                        str(row.get("EN BODEGA", "no")).lower(),
                        str(row.get("FALTANTES", "no")).lower(),
                        row.get("CANTIDAD DE BIENES", 0) if row.get("CANTIDAD DE BIENES", "") != "" else 0,
                        str(row.get("REGION", "")).strip().upper(),
                        str(row.get("LOCALIDAD", "")).strip().upper(),
                        str(row.get("MUNICIPIO", "")).strip().upper(),
                        str(row.get("CONTACTO", "")),
                        str(row.get("CORREO", "")),
                        str(row.get("OBSERVACIONES", "")),
                        str(row.get("RECIBIO", "")),
                        str(row.get("TIPO DE DOCUMENTO", "")),
                        "Pendiente",
                    ),
                )
                count += 1
            except Exception as e:
                errores += 1
                print(f"⚠️ Error en la fila {index}: {e}")
        
        conn.commit()
        conn.close()
        
        mensaje = f"Se importaron {count} solicitudes con éxito. Fila(s) con error: {errores}."
        if advertencias_duplicados > 0:
            mensaje += f" ⚠️ Ojo: {advertencias_duplicados} de estas solicitudes tienen un CT que ya estaba registrado previamente (posibles duplicados)."
        
        return True, mensaje
    except Exception as e:
        return False, f"Error en la base de datos: {e}"

if __name__ == "__main__":
    print("🔄 Iniciando importación de datos de prueba (datos.xlsx)...")
    exito, mensaje = importar_de_excel("datos.xlsx")
    if exito:
        print(f"✅ {mensaje}")
    else:
        print(f"❌ {mensaje}")
