import pandas as pd
import re
import os
from datetime import datetime
from urllib.parse import urlparse
import numpy as np

class SquidLogAnalyzer:
    """Clase para analizar logs de Squid."""
    
    def __init__(self, log_path):
        """Inicializa el analizador con la ruta al archivo de log."""
        self.log_path = log_path
        self.df = None
        self.log_lines = 0
        
    def read_log_file(self):
        """Lee el archivo de log de Squid y lo procesa."""
        self.log_data = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Procesar cada línea según el formato detailed
                    parsed_line = self._parse_detailed_log_line(line.strip())
                    if parsed_line:
                        self.log_data.append(parsed_line)
            
            self.log_lines = len(self.log_data)
            return True
        except Exception as e:
            print(f"Error al leer el archivo de log: {e}")
            return False
    
    def _parse_detailed_log_line(self, line):
        """
        Parsea una línea de log en formato optimizado.
        
        Format: %>a %un "%rm %ru HTTP/%rv" %>Hs %<st "%{User-Agent}>h" %Ss:%Sh
        Ejemplo: 192.168.1.254 maxwell "GET http://detectportal.firefox.com/canonical.html HTTP/1.1" 502 4014 "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0" TCP_MISS:HIER_NONE
        """
        try:
            # Usar una expresión regular para el nuevo formato
            pattern = r'(\S+) (\S+) "(.*?)" (\d+) (\d+|-) "(.*?)" (\S+)'
            match = re.match(pattern, line)
            
            if not match:
                print(f"No match for line: {line}")
                return None
                
            client_ip, username, request, status_code, size, user_agent, squid_status = match.groups()
            
            # Extraer método y URL del request
            request_parts = request.split()
            method = request_parts[0] if len(request_parts) > 0 else "-"
            url = request_parts[1] if len(request_parts) > 1 else "-"
            
            # Extraer dominio de la URL
            domain = self._extract_domain(url)
            
            # Determinar tipo de contenido basado en la URL
            content_type = self._determine_content_type(url)
            
            # Convertir tamaño a entero
            size = int(size) if size != '-' else 0
            
            # Usar la fecha actual como timestamp ya que no está en el log
            # Esto es solo para mantener la estructura del DataFrame
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': timestamp,
                'client_ip': client_ip,
                'user': username if username != '-' else None,
                'method': method,
                'url': url,
                'domain': domain,
                'status_code': int(status_code),
                'size': size,
                'referer': None,  # No hay referer en el nuevo formato
                'user_agent': user_agent,
                'squid_status': squid_status,
                'content_type': content_type
            }
        except Exception as e:
            print(f"Error al parsear línea: {e}")
            print(f"Línea: {line}")
            return None
        
    def _extract_domain(self, url):
        """Extrae el dominio de una URL."""
        try:
            if url == '-':
                return '-'
                
            # Manejar URLs con y sin protocolo
            if '://' not in url:
                url = 'http://' + url
                
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Si no hay dominio, intentar extraerlo de otra manera
            if not domain and ':' in url:
                domain = url.split(':', 1)[0]
            
            return domain if domain else url
        except:
            return url
    
    def _determine_content_type(self, url):
        """Determina el tipo de contenido basado en la URL."""
        if url == '-':
            return 'unknown'
            
        url_lower = url.lower()
        
        # Imágenes
        if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
            return 'image'
        # Documentos
        elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
            return 'document'
        # Audio/Video
        elif any(ext in url_lower for ext in ['.mp3', '.mp4', '.avi', '.mov', '.flv', '.wav', '.ogg']):
            return 'media'
        # Web
        elif any(ext in url_lower for ext in ['.html', '.htm', '.php', '.asp', '.aspx', '.jsp']):
            return 'web'
        # JavaScript/CSS
        elif any(ext in url_lower for ext in ['.js', '.css']):
            return 'web-resource'
        # Comprimidos
        elif any(ext in url_lower for ext in ['.zip', '.rar', '.7z', '.tar', '.gz']):
            return 'archive'
        # Ejecutables
        elif any(ext in url_lower for ext in ['.exe', '.msi', '.bin', '.sh']):
            return 'executable'
        else:
            return 'other'
    
    def to_dataframe(self):
        """Convierte los datos procesados a un DataFrame de pandas."""
        if not hasattr(self, 'log_data') or not self.log_data:
            if not self.read_log_file():
                raise ValueError("No se pudo leer el archivo de log")
        
        # Crear DataFrame a partir de la lista de diccionarios
        self.df = pd.DataFrame(self.log_data)
        
        # Añadir columnas derivadas útiles para el análisis
        # Como no tenemos timestamp en el log, usamos la fecha actual para las columnas derivadas
        # o simplemente omitimos estas columnas
        if 'timestamp' in self.df.columns:
            try:
                self.df['date'] = pd.to_datetime(self.df['timestamp']).dt.date
                self.df['hour'] = pd.to_datetime(self.df['timestamp']).dt.hour
                self.df['day_of_week'] = pd.to_datetime(self.df['timestamp']).dt.day_name()
            except:
                # Si hay problemas con el timestamp, crear columnas con valores por defecto
                self.df['date'] = datetime.now().date()
                self.df['hour'] = datetime.now().hour
                self.df['day_of_week'] = datetime.now().strftime('%A')
        
        return self.df
    
    def get_summary(self):
        """Obtiene un resumen del análisis."""
        if self.df is None:
            self.to_dataframe()
        
        if self.df.empty:
            return {
                'total_requests': 0,
                'total_bytes': 0,
                'unique_users': 0,
                'unique_ips': 0
            }
        
        total_requests = len(self.df)
        
        # Verificar que las columnas existen
        total_bytes = self.df['size'].sum() if 'size' in self.df.columns else 0
        unique_users = self.df['user'].nunique() if 'user' in self.df.columns else 0
        unique_ips = self.df['client_ip'].nunique() if 'client_ip' in self.df.columns else 0
        
        return {
            'total_requests': total_requests,
            'total_bytes': total_bytes,
            'unique_users': unique_users,
            'unique_ips': unique_ips
        }

    def get_top_users(self, limit=10, excluded=None):
        """Obtiene los usuarios con más tráfico."""
        if self.df is None:
            self.to_dataframe()
        
        if excluded is None:
            excluded = []
        
        if self.df.empty or 'user' not in self.df.columns:
            # Devolver un DataFrame vacío con las columnas esperadas
            return pd.DataFrame(columns=['user', 'traffic', 'requests', 'traffic_readable'])
        
        # Filtrar usuarios excluidos y nulos
        filtered_df = self.df[
            (~self.df['user'].isin(excluded)) & 
            (self.df['user'].notna())
        ]
        
        if filtered_df.empty:
            return pd.DataFrame(columns=['user', 'traffic', 'requests', 'traffic_readable'])
        
        # Agrupar por usuario y sumar el tráfico
        user_traffic = filtered_df.groupby('user').agg({
            'size': 'sum',
            'url': 'count'
        }).reset_index()
        
        user_traffic.columns = ['user', 'traffic', 'requests']
        user_traffic = user_traffic.sort_values('traffic', ascending=False).head(limit)
        
        # Convertir bytes a formato legible
        user_traffic['traffic_readable'] = user_traffic['traffic'].apply(self._bytes_to_human_readable)
        
        return user_traffic

    def get_top_domains(self, limit=20, excluded=None):
        """Obtiene los dominios más visitados."""
        if self.df is None:
            self.to_dataframe()
        
        if excluded is None:
            excluded = []
        
        if self.df.empty or 'domain' not in self.df.columns:
            # Devolver un DataFrame vacío con las columnas esperadas
            return pd.DataFrame(columns=['domain', 'visits', 'traffic', 'traffic_readable'])
        
        # Filtrar dominios excluidos y nulos
        filtered_df = self.df[
            (~self.df['domain'].isin(excluded)) & 
            (self.df['domain'].notna())
        ]
        
        if filtered_df.empty:
            return pd.DataFrame(columns=['domain', 'visits', 'traffic', 'traffic_readable'])
        
        # Agrupar por dominio y contar visitas
        domain_visits = filtered_df.groupby('domain').agg({
            'url': 'count',
            'size': 'sum'
        }).reset_index()
        
        domain_visits.columns = ['domain', 'visits', 'traffic']
        domain_visits = domain_visits.sort_values('visits', ascending=False).head(limit)
        
        # Convertir bytes a formato legible
        domain_visits['traffic_readable'] = domain_visits['traffic'].apply(self._bytes_to_human_readable)
        
        return domain_visits
        
    def get_hourly_usage(self):
        """Obtiene el uso por hora del día."""
        if self.df is None:
            self.to_dataframe()
        
        if 'hour' not in self.df.columns:
            return pd.DataFrame()
        
        hourly_usage = self.df.groupby('hour').agg({
            'url': 'count',
            'size': 'sum'
        }).reset_index()
        
        hourly_usage.columns = ['hour', 'requests', 'traffic']
        
        # Asegurar que todas las horas estén representadas
        all_hours = pd.DataFrame({'hour': range(24)})
        hourly_usage = pd.merge(all_hours, hourly_usage, on='hour', how='left').fillna(0)
        
        return hourly_usage
    
    def get_daily_usage(self):
        """Obtiene el uso por día de la semana."""
        if self.df is None:
            self.to_dataframe()
        
        if 'day_of_week' not in self.df.columns:
            return pd.DataFrame()
        
        # Orden de los días de la semana
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        daily_usage = self.df.groupby('day_of_week').agg({
            'url': 'count',
            'size': 'sum'
        }).reset_index()
        
        daily_usage.columns = ['day_of_week', 'requests', 'traffic']
        
        # Ordenar por día de la semana
        daily_usage['day_of_week'] = pd.Categorical(
            daily_usage['day_of_week'], 
            categories=day_order, 
            ordered=True
        )
        daily_usage = daily_usage.sort_values('day_of_week')
        
        return daily_usage
    
    def get_status_codes(self):
        """Obtiene la distribución de códigos de estado HTTP."""
        if self.df is None:
            self.to_dataframe()
        
        status_counts = self.df['status_code'].value_counts().reset_index()
        status_counts.columns = ['status_code', 'count']
        
        # Añadir descripción de los códigos
        status_descriptions = {
            200: 'OK',
            201: 'Created',
            204: 'No Content',
            206: 'Partial Content',
            301: 'Moved Permanently',
            302: 'Found',
            304: 'Not Modified',
            307: 'Temporary Redirect',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            407: 'Proxy Authentication Required',
            408: 'Request Timeout',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable',
            504: 'Gateway Timeout'
        }
        
        status_counts['description'] = status_counts['status_code'].map(
            lambda x: status_descriptions.get(x, 'Unknown')
        )
        
        return status_counts
    
    def get_content_types(self):
        """Obtiene la distribución de tipos de contenido."""
        if self.df is None:
            self.to_dataframe()
        
        if 'content_type' not in self.df.columns:
            return pd.Series(dtype='object')
        
        return self.df['content_type'].value_counts().head(10)
    
    def get_user_data(self, username):
        """Obtiene datos específicos para un usuario."""
        if self.df is None:
            self.to_dataframe()
        
        # Filtrar por usuario
        user_df = self.df[self.df['user'] == username]
        
        if user_df.empty:
            return None
        
        # Estadísticas básicas
        total_requests = len(user_df)
        total_traffic = user_df['size'].sum()
        traffic_readable = self._bytes_to_human_readable(total_traffic)
        
        # Dominios más visitados
        top_domains = user_df['domain'].value_counts().head(10).reset_index()
        top_domains.columns = ['domain', 'visits']
        
        # Códigos de estado
        status_codes = user_df['status_code'].value_counts().reset_index()
        status_codes.columns = ['status_code', 'count']
        
        # Tipos de contenido
        content_types = user_df['content_type'].value_counts().reset_index()
        content_types.columns = ['content_type', 'count']
        
        # URLs más visitadas
        top_urls = user_df['url'].value_counts().head(10).reset_index()
        top_urls.columns = ['url', 'visits']
        
        # Tamaño promedio de respuesta
        avg_response_size = user_df['size'].mean()
        avg_response_readable = self._bytes_to_human_readable(avg_response_size)
        
        # Porcentaje de solicitudes exitosas (códigos 2xx)
        success_requests = len(user_df[user_df['status_code'].between(200, 299)])
        success_rate = (success_requests / total_requests) * 100 if total_requests > 0 else 0
        
        # Porcentaje de solicitudes fallidas (códigos 4xx, 5xx)
        error_requests = len(user_df[user_df['status_code'] >= 400])
        error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            'username': username,
            'total_requests': total_requests,
            'total_traffic': total_traffic,
            'traffic_readable': traffic_readable,
            'top_domains': top_domains,
            'status_codes': status_codes,
            'content_types': content_types,
            'top_urls': top_urls,
            'avg_response_size': avg_response_size,
            'avg_response_readable': avg_response_readable,
            'success_rate': success_rate,
            'error_rate': error_rate
        }
    
    def get_date_range(self):
        """Obtiene el rango de fechas en el log."""
        # Como no tenemos timestamp real, devolvemos la fecha actual
        now = datetime.now()
        return now, now

    def filter_by_date(self, start_date=None, end_date=None):
        """Filtra los datos por rango de fechas."""
        # Como no tenemos timestamp real, simplemente devolvemos una copia del analizador
        filtered_analyzer = SquidLogAnalyzer(self.log_path)
        filtered_analyzer.df = self.df.copy() if self.df is not None else None
        return filtered_analyzer
    
    def _bytes_to_human_readable(self, bytes_value):
        """Convierte bytes a formato legible por humanos."""
        if bytes_value == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while bytes_value >= 1024 and i < len(size_names) - 1:
            bytes_value /= 1024
            i += 1
        
        return f"{bytes_value:.2f} {size_names[i]}"
        
    def debug_dataframe(self):
        """Imprime información de depuración sobre el DataFrame."""
        if self.df is None:
            print("DataFrame no inicializado")
            return
        
        print(f"Columnas del DataFrame: {self.df.columns.tolist()}")
        print(f"Número de filas: {len(self.df)}")
        print("\nPrimeras 5 filas:")
        print(self.df.head())
