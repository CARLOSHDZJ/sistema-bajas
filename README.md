# 📦 Sistema de Gestión y Recolección de Bajas Escolares (IEEPO)

Plataforma web Full-Stack para la digitalización, seguimiento logístico y control de solicitudes de recolección de bienes muebles en centros educativos divididos por regiones.

## ✨ Características Principales
* **Dashboard Operativo en Tiempo Real:** Visualización de solicitudes pendientes, cálculo automático de días transcurridos, etiquetado de prioridad/urgencia y filtros dinámicos con DataTables.
* **Gestión de Expedientes Documentales:** Carga y validación de archivos PDF de respaldo y evidencia fotográfica por Centro de Trabajo (CCT).
* **Analítica y Reportes por Región:** Métricas históricas de productividad, conteo de bienes recolectados y distribución geográfica en las 8 regiones del estado.
* **Importación Masiva y Respaldos:** Carga masiva desde hojas de cálculo Excel (`datos.xlsx` con datos sintéticos de demostración incluidos) y descarga de copias de seguridad en ZIP desde el panel administrativo.
* **Control de Acceso Basado en Roles (RBAC) y Bitácora:** Gestión de usuarios (`admin`, `editor`, `visor`) con contraseñas cifradas (`werkzeug.security`) y auditoría completa de acciones.

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python 3, Flask, SQLite3 (modo concurrente WAL), Pandas, OpenPyXL.
* **Frontend:** HTML5, Jinja2, Bootstrap 5, DataTables, Chart.js, Font Awesome.
* **Despliegue:** Docker, Waitress / Gunicorn.

## 🚀 Instalación y Uso Rápido (Modo Demo)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Inicializar base de datos, usuario administrador y datos de demostración
python setup_db.py
python crear_seguridad.py
python importar_excel.py

# 3. Iniciar el servidor
python app.py
```

* **Acceso local:** `http://127.0.0.1:8080`
* **Usuario Demo:** `admin` / `admin123`

> **Nota de Privacidad:** Este repositorio público incluye únicamente registros sintéticos de demostración en `datos.xlsx`. Ningún dato real de centros de trabajo ni información de contacto personal se encuentra almacenado en este repositorio.
