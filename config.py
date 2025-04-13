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
os.makedirs(REPORTS_DIR, exist_ok=True)

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
    "log_format": "auto",  # Formato de log: auto, detailed, common, squid_native, custom
}

# Colores para gráficos
CHART_COLORS = [
    "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
    "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
]

# Formatos de log soportados
LOG_FORMATS = {
    'auto': 'Detección automática',
    'detailed': 'Detallado (personalizado)',
    'common': 'Común (CLF)',
    'squid_native': 'Nativo de Squid',
    'custom': 'Personalizado (estándar)',
    'custom_new': 'Personalizado (nuevo)'
}

# Descripción de los formatos de log
LOG_FORMAT_DESCRIPTIONS = {
    'detailed': 'client_ip username "method url" status_code size "user_agent" squid_status',
    'common': 'client_ip ident username [timestamp] "method url protocol" status_code size',
    'squid_native': 'timestamp elapsed client_ip result_code/status_code size method url username hierarchy_code/peer_host content_type',
    'custom': 'client_ip username url [timestamp] size squid_status/status_code method mime_type "user_agent"',
    'custom_new': '%>a %un %ru [%{%d/%b/%Y:%H:%M:%S %z}tl] %st %Ss/%03>Hs %rm %mt "%{User-Agent}>h"'
}

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
