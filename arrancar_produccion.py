from waitress import serve
from app import app
import socket


# Truco infalible para obtener tu IP real en la red de la oficina
def obtener_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


mi_ip = obtener_ip()

print("\n" + "=" * 50)
print("🚀 SERVIDOR DE BAJAS ACTIVO (MODO PRODUCCIÓN)")
print("=" * 50)
print(f"👉 Toma tu celular (conectado al WiFi) y entra a:")
print(f"🌐 http://{mi_ip}:8080")
print("=" * 50)
print("Presiona Ctrl+C para apagar el servidor.\n")

# Arrancamos el motor Waitress en el puerto 8080
serve(app, host="0.0.0.0", port=8080)
