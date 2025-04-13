import pandas as pd
import re
import os
from datetime import datetime
from urllib.parse import urlparse
import numpy as np
import logging
from dateutil import parser as date_parser

logger = logging.getLogger('SLAM.Analyzer')

class SquidLogAnalyzer:
    """Clase para analizar logs de Squid."""
    
    def __init__(self, log_path, log_format='auto'):
        """
        Inicializa el analizador con la ruta al archivo de log y el formato.
        
        Args:
            log_path: Ruta al archivo de log
            log_format: Formato del log ('auto', 'detailed', 'common', 'squid_native', 'custom', 'custom_new')
        """
        self.log_path = log_path
        self.log_format = log_format
        self.df = None
        self.log_lines = 0
        self.detected_format = None
        
    def read_log_file(self):
        """Lee el archivo de log de Squid y lo procesa según el formato especificado."""
        self.log_data = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Leer las primeras líneas para detectar el formato si es 'auto'
                if self.log_format == 'auto':
                    sample_lines = [next(f) for _ in range(10) if f]
                    f.seek(0)  # Volver al inicio del archivo
                    self.detected_format = self._detect_log_format(sample_lines)
                    logger.info(f"Formato de log detectado: {self.detected_format}")
                    format_to_use = self.detected_format
                else:
                    format_to_use = self.log_format
                
                # Seleccionar el parser adecuado según el formato
                parser_method = self._get_parser_for_format(format_to_use)
                
                for line in f:
                    # Procesar cada línea según el formato detectado/especificado
                    parsed_line = parser_method(line.strip())
                    if parsed_line:
                        self.log_data.append(parsed_line)
            
            self.log_lines = len(self.log_data)
            return True
        except Exception as e:
            logger.error(f"Error al leer el archivo de log: {e}")
            return False
    
    def _detect_log_format(self, sample_lines):
        """
        Detecta automáticamente el formato del log basado en muestras de líneas.
        
        Args:
            sample_lines: Lista de líneas de muestra del log
        
        Returns:
            Formato detectado ('detailed', 'common', 'squid_native', 'custom', 'custom_new')
        """
        # Patrones para cada formato
        format_patterns = {
            'detailed': r'(\S+) (\S+) "(.*?)" (\d+) (\d+|-) "(.*?)" (\S+)',
            'common': r'(\S+) \S+ (\S+) \[(.*?)\] "(.*?)" (\d+) (\d+|-)',
            'squid_native': r'(\d+\.\d+)\s+\d+\s+(\S+)\s+(\S+)\/(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\/(\S+)\s+(\S+)',
            'custom': r'(\S+) (\S+) (\S+) \[(.*?)\] (\d+) (\S+) (\S+) (\S+) "(.*?)"',
            'custom_new': r'(\S+) (\S+) (\S+) \[(.*?)\] (\d+) (\S+)\/(\d+) (\S+) (\S+) "(.*?)"'
        }
        
        # Contar coincidencias para cada formato
        format_matches = {fmt: 0 for fmt in format_patterns}
        
        for line in sample_lines:
            for fmt, pattern in format_patterns.items():
                if re.match(pattern, line):
                    format_matches[fmt] += 1
        
        # Determinar el formato con más coincidencias
        best_format = max(format_matches.items(), key=lambda x: x[1])
        
        # Si no hay coincidencias claras, usar 'detailed' como fallback
        if best_format[1] == 0:
            logger.warning("No se pudo detectar el formato. Usando 'detailed' por defecto.")
            return 'detailed'
        
        return best_format[0]
    
    def _get_parser_for_format(self, format_name):
        """
        Devuelve el método parser adecuado para el formato especificado.
        
        Args:
            format_name: Nombre del formato ('detailed', 'common', etc.)
        
        Returns:
            Método parser correspondiente
        """
        parsers = {
            'detailed': self._parse_detailed_log_line,
            'common': self._parse_common_log_line,
            'squid_native': self._parse_squid_native_log_line,
            'custom': self._parse_custom_log_line,
            'custom_new': self._parse_custom_new_log_line
        }
        
        return parsers.get(format_name, self._parse_detailed_log_line)
    
    def _parse_detailed_log_line(self, line):
        """
        Parsea una línea de log en formato detallado.
        Formato: client_ip username "method url" status_code size "user_agent" squid_status
        """
        try:
            pattern = r'(\S+) (\S+) "(.*?)" (\d+) (\d+|-) "(.*?)" (\S+)'
            match = re.match(pattern, line)
            
            if not match:
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
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': timestamp,
                'client_ip': client_ip,
                'username': username if username != '-' else None,
                'method': method,
                'url': url,
                'domain': domain,
                'status_code': int(status_code),
                'size': size,
                'referer': None,  # No hay referer en este formato
                'user_agent': user_agent,
                'squid_status': squid_status,
                'content_type': content_type
            }
        except Exception as e:
            logger.error(f"Error al parsear línea en formato detailed: {e}")
            logger.debug(f"Línea: {line}")
            return None
    
    def _parse_common_log_line(self, line):
        """
        Parsea una línea de log en formato común (CLF).
        Formato: client_ip ident username [timestamp] "method url protocol" status_code size
        """
        try:
            pattern = r'(\S+) \S+ (\S+) \[(.*?)\] "(.*?)" (\d+) (\d+|-)'
            match = re.match(pattern, line)
            
            if not match:
                return None
                
            client_ip, username, timestamp_str, request, status_code, size = match.groups()
            
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
            
            # Parsear timestamp
            try:
                timestamp = date_parser.parse(timestamp_str).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': timestamp,
                'client_ip': client_ip,
                'username': username if username != '-' else None,
                'method': method,
                'url': url,
                'domain': domain,
                'status_code': int(status_code),
                'size': size,
                'referer': None,  # No hay referer en este formato
                'user_agent': None,  # No hay user_agent en este formato
                'squid_status': None,  # No hay squid_status en este formato
                'content_type': content_type
            }
        except Exception as e:
            logger.error(f"Error al parsear línea en formato common: {e}")
            logger.debug(f"Línea: {line}")
            return None
    
    def _parse_squid_native_log_line(self, line):
        """
        Parsea una línea de log en formato nativo de Squid.
        Formato: timestamp elapsed client_ip result_code/status_code size method url username hierarchy_code/peer_host content_type
        """
        try:
            pattern = r'(\d+\.\d+)\s+\d+\s+(\S+)\s+(\S+)\/(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\/(\S+)\s+(\S+)'
            match = re.match(pattern, line)
            
            if not match:
                return None
                
            timestamp_epoch, client_ip, result_code, status_code, size, method, url, username, hierarchy_code, peer_host, content_type_raw = match.groups()
            
            # Extraer dominio de la URL
            domain = self._extract_domain(url)
            
            # Determinar tipo de contenido
            content_type = self._determine_content_type(url)
            
            # Convertir timestamp epoch a datetime
            try:
                timestamp = datetime.fromtimestamp(float(timestamp_epoch)).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': timestamp,
                'client_ip': client_ip,
                'username': username if username != '-' else None,
                'method': method,
                'url': url,
                'domain': domain,
                'status_code': int(status_code),
                'size': int(size),
                'referer': None,  # No hay referer en este formato
                'user_agent': None,  # No hay user_agent en este formato
                'squid_status': result_code,
                'content_type': content_type
            }
        except Exception as e:
            logger.error(f"Error al parsear línea en formato squid_native: {e}")
            logger.debug(f"Línea: {line}")
            return None
    
    def _parse_custom_log_line(self, line):
        """
        Parsea una línea de log en formato personalizado.
        Formato: client_ip username url [timestamp] size squid_status/status_code method mime_type "user_agent"
        """
        try:
            pattern = r'(\S+) (\S+) (\S+) \[(.*?)\] (\d+) (\S+) (\S+) (\S+) "(.*?)"'
            match = re.match(pattern, line)
            
            if not match:
                return None
                
            client_ip, username, url, timestamp_str, size, status_info, method, mime_type, user_agent = match.groups()
            
            # Extraer dominio de la URL
            domain = self._extract_domain(url)
            
            # Determinar tipo de contenido
            content_type = self._determine_content_type(url)
            
            # Extraer código de estado
            if '/' in status_info:
                squid_status, status_code = status_info.split('/')
            else:
                squid_status = status_info
                status_code = 0
            
            # Parsear timestamp
            try:
                timestamp = date_parser.parse(timestamp_str).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': timestamp,
                'client_ip': client_ip,
                'username': username if username != '-' else None,
                'method': method,
                'url': url,
                'domain': domain,
                'status_code': int(status_code),
                'size': int(size),
                'referer': None,  # No hay referer en este formato
                'user_agent': user_agent,
                'squid_status': squid_status,
                'content_type': content_type if content_type else mime_type
            }
        except Exception as e:
            logger.error(f"Error al parsear línea en formato custom: {e}")
            logger.debug(f"Línea: {line}")
            return None
    
    def _parse_custom_new_log_line(self, line):
        """
        Parsea una línea de log en formato personalizado nuevo.
        Formato: client_ip username url [timestamp] status_code squid_status/hierarchy_code method mime_type "user_agent"
        """
        try:
            pattern = r'(\S+) (\S+) (\S+) \[(.*?)\] (\d+) (\S+)\/(\d+) (\S+) (\S+) "(.*?)"'
            match = re.match(pattern, line)
            
            if not match:
                return None
                
            client_ip, username, url, timestamp_str, status_code, squid_status, hierarchy_code, method, mime_type, user_agent = match.groups()
            
            # Extraer dominio de la URL
            domain = self._extract_domain(url)
            
            # Determinar tipo de contenido
            content_type = self._determine_content_type(url)
            
            # Parsear timestamp
            try:
                timestamp = date_parser.parse(timestamp_str).strftime('%Y-%m-%d %H:%M:%S')
            except:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'timestamp': timestamp,
                'client_ip': client_ip,
                'username': username if username != '-' else None,
                'method': method,
                'url': url,
                'domain': domain,
                'status_code': int(status_code),
                'size': 0,  # No hay tamaño en este formato, se podría añadir después
                'referer': None,  # No hay referer en este formato
                'user_agent': user_agent,
                'squid_status': squid_status,
                'content_type': content_type if content_type else mime_type
            }
        except Exception as e:
            logger.error(f"Error al parsear línea en formato custom_new: {e}")
            logger.debug(f"Línea: {line}")
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
        if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']):
            return 'image'
        # Documentos
        elif any(ext in url_lower for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv']):
            return 'document'
        # Audio/Video
        elif any(ext in url_lower for ext in ['.mp3', '.mp4', '.avi', '.mov', '.flv', '.wav', '.ogg', '.webm', '.mkv']):
            return 'media'
        # Web
        elif any(ext in url_lower for ext in ['.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.do']):
            return 'web'
        # JavaScript/CSS
        elif any(ext in url_lower for ext in ['.js', '.css', '.json', '.xml']):
            return 'web-resource'
        # Comprimidos
        elif any(ext in url_lower for ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']):
            return 'archive'
        # Ejecutables
        elif any(ext in url_lower for ext in ['.exe', '.msi', '.bin', '.sh', '.bat', '.apk']):
            return 'executable'
        # Fuentes
        elif any(ext in url_lower for ext in ['.ttf', '.otf', '.woff', '.woff2', '.eot']):
            return 'font'
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
        if 'timestamp' in self.df.columns:
            try:
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
                self.df['date'] = self.df['timestamp'].dt.date
                self.df['hour'] = self.df['timestamp'].dt.hour
                self.df['day_of_week'] = self.df['timestamp'].dt.day_name()
            except Exception as e:
                logger.warning(f"Error al procesar timestamps: {e}")
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
        
        # Determinar qué columna usar para el usuario
        user_column = None
        for col in ['username', 'user']:
            if col in self.df.columns:
                user_column = col
                break
        
        unique_users = self.df[user_column].nunique() if user_column and user_column in self.df.columns else 0
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
        
        # Determinar qué columna usar para el usuario
        user_column = None
        for col in ['username', 'user']:
            if col in self.df.columns:
                user_column = col
                break
        
        if self.df.empty or not user_column:
            # Devolver un DataFrame vacío con las columnas esperadas
            return pd.DataFrame(columns=['user', 'traffic', 'requests', 'traffic_readable'])
        
        # Filtrar usuarios excluidos y nulos
        filtered_df = self.df[
            (~self.df[user_column].isin(excluded)) & 
            (self.df[user_column].notna())
        ]
        
        if filtered_df.empty:
            return pd.DataFrame(columns=['user', 'traffic', 'requests', 'traffic_readable'])
        
        # Agrupar por usuario y sumar el tráfico
        user_traffic = filtered_df.groupby(user_column).agg({
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
        
        if 'status_code' not in self.df.columns:
            return pd.DataFrame(columns=['status_code', 'count', 'description'])
        
        status_counts = self.df['status_code'].value_counts().reset_index()
        status_counts.columns = ['status_code', 'count']
        
        # Añadir descripción de los códigos
        from config import HTTP_CODE_DESCRIPTIONS
        
        status_counts['description'] = status_counts['status_code'].map(
            lambda x: HTTP_CODE_DESCRIPTIONS.get(x, 'Unknown')
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
        
        # Determinar qué columna usar para el usuario
        user_column = None
        for col in ['username', 'user']:
            if col in self.df.columns:
                user_column = col
                break
        
        if not user_column:
            return None
        
        # Filtrar por usuario
        user_df = self.df[self.df[user_column] == username]
        
        if user_df.empty:
            return None
        
        # Estadísticas básicas
        total_requests = len(user_df)
        total_traffic = user_df['size'].sum() if 'size' in user_df.columns else 0
        traffic_readable = self._bytes_to_human_readable(total_traffic)
        
        # Dominios más visitados
        top_domains = user_df['domain'].value_counts().head(10).reset_index() if 'domain' in user_df.columns else pd.DataFrame(columns=['domain', 'count'])
        top_domains.columns = ['domain', 'visits']
        
        # Códigos de estado
        status_codes = user_df['status_code'].value_counts().reset_index() if 'status_code' in user_df.columns else pd.DataFrame(columns=['status_code', 'count'])
        status_codes.columns = ['status_code', 'count']
        
        # Tipos de contenido
        content_types = user_df['content_type'].value_counts().reset_index() if 'content_type' in user_df.columns else pd.DataFrame(columns=['content_type', 'count'])
        content_types.columns = ['content_type', 'count']
        
        # URLs más visitadas
        top_urls = user_df['url'].value_counts().head(10).reset_index() if 'url' in user_df.columns else pd.DataFrame(columns=['url', 'count'])
        top_urls.columns = ['url', 'visits']
        
        # Tamaño promedio de respuesta
        avg_response_size = user_df['size'].mean() if 'size' in user_df.columns else 0
        avg_response_readable = self._bytes_to_human_readable(avg_response_size)
        
        # Porcentaje de solicitudes exitosas (códigos 2xx)
        if 'status_code' in user_df.columns:
            success_requests = len(user_df[user_df['status_code'].between(200, 299)])
            success_rate = (success_requests / total_requests) * 100 if total_requests > 0 else 0
            
            # Porcentaje de solicitudes fallidas (códigos 4xx, 5xx)
            error_requests = len(user_df[user_df['status_code'] >= 400])
            error_rate = (error_requests / total_requests) * 100 if total_requests > 0 else 0
        else:
            success_rate = 0
            error_rate = 0
        
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
        if self.df is None:
            self.to_dataframe()
        
        if 'timestamp' in self.df.columns and not self.df.empty:
            try:
                timestamps = pd.to_datetime(self.df['timestamp'])
                return timestamps.min(), timestamps.max()
            except:
                pass
        
        # Si no hay timestamps válidos, devolver la fecha actual
        now = datetime.now()
        return now, now

    def filter_by_date(self, start_date=None, end_date=None):
        """Filtra los datos por rango de fechas."""
        if self.df is None:
            self.to_dataframe()
        
        filtered_analyzer = SquidLogAnalyzer(self.log_path, self.log_format)
        
        if 'timestamp' not in self.df.columns or self.df.empty:
            filtered_analyzer.df = self.df.copy() if self.df is not None else None
            return filtered_analyzer
        
        try:
            # Convertir a datetime si no lo son
            if start_date and not isinstance(start_date, datetime):
                start_date = pd.to_datetime(start_date)
            if end_date and not isinstance(end_date, datetime):
                end_date = pd.to_datetime(end_date)
            
            # Convertir la columna timestamp a datetime
            df_copy = self.df.copy()
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
            
            # Aplicar filtros
            if start_date:
                df_copy = df_copy[df_copy['timestamp'] >= start_date]
            if end_date:
                df_copy = df_copy[df_copy['timestamp'] <= end_date]
            
            filtered_analyzer.df = df_copy
        except Exception as e:
            logger.error(f"Error al filtrar por fecha: {e}")
            filtered_analyzer.df = self.df.copy()
        
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
        
        # Información adicional sobre el formato detectado
        if hasattr(self, 'detected_format'):
            print(f"\nFormato detectado: {self.detected_format}")
        else:
            print(f"\nFormato configurado: {self.log_format}")
