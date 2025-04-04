
"""
Configuración para Squid Log Analyzer.
"""
import os
from pathlib import Path

# Rutas de directorios
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
REPORTS_DIR = "/var/www/slam"

# Asegurar que los directorios existan
for directory in [TEMPLATES_DIR, STATIC_DIR]:
    os.makedirs(directory, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)  # Solo crear REPORTS_DIR ya que es una ruta absoluta

# Configuración por defecto
DEFAULT_CONFIG = {
    "squid_log_path": "/var/log/squid/access.log",  # Ruta típica de Squid en Linux
    "report_title": "Squid Usage Report",
    "refresh_interval": 3600,  # en segundos
    "max_users": 10,  # Top N usuarios
    "max_sites": 20,  # Top N sitios
    "date_format": "%Y-%m-%d",
    "time_format": "%H:%M:%S",
    "excluded_domains": [
        "localhost",
        "127.0.0.1",
        "::1"
    ],
    "excluded_users": [
        "proxy",
        "admin"
    ],
    "theme": "light",
    "language": "es",
}

# Colores para gráficos
CHART_COLORS = [
    "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
]

# Estructura del archivo de log de Squid
# Formato: timestamp elapsed remotehost code/status bytes method URL rfc931 peerstatus/peerhost type
LOG_FIELDS = [
    "timestamp",
    "elapsed",
    "client_address",
    "result_code",
    "size",
    "method",
    "url",
    "user",
    "hierarchy_code",
    "content_type"
]

# Mapeo de códigos HTTP a descripciones
HTTP_CODE_DESCRIPTIONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    206: "Partial Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout"
}
