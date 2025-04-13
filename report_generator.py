import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import jinja2
import shutil
import json
import re
import logging
from config import TEMPLATES_DIR, REPORTS_DIR, CHART_COLORS, STATIC_DIR

logger = logging.getLogger('SLAM.ReportGenerator')

class SquidReportGenerator:
    
    def __init__(self, analyzer):
        """Inicializa el generador de Reportes con un analizador."""
        self.analyzer = analyzer
        self.report_data = {}

    @staticmethod
    def generate_reports_index():
        """Genera un índice HTML de todos los Reportes disponibles."""
        try:
            # Buscar todos los directorios de Reportes
            reports = []
            for item in os.listdir(REPORTS_DIR):
                item_path = os.path.join(REPORTS_DIR, item)
                if os.path.isdir(item_path):
                    report_html = os.path.join(item_path, 'index.html')  # Cambiado de 'report.html' a 'index.html'
                    if os.path.isfile(report_html):
                        # Obtener fecha de creación del Reporte
                        creation_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        
                        # Intentar extraer el título del Reporte del archivo HTML
                        title = f"{item}"
                        try:
                            with open(report_html, 'r', encoding='utf-8') as f:
                                content = f.read()
                                title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content)
                                if title_match:
                                    title = title_match.group(1)
                                    # Limpiar etiquetas HTML
                                    title = re.sub(r'<[^>]+>', '', title).strip()
                        except:
                            pass
                        
                        reports.append({
                            'id': item,
                            'path': os.path.join(item, 'index.html'),
                            'title': title,
                            'date': creation_time.strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            # Ordenar por fecha (más reciente primero)
            reports.sort(key=lambda x: x['date'], reverse=True)
            
            # Preparar datos para la plantilla
            template_data = {
                'title': 'Índice de Reportes de Squid Log Analyzer',
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'reports': reports
            }
            
            # Cargar plantilla
            template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
            template_env = jinja2.Environment(loader=template_loader)
            template = template_env.get_template('reports_index.html')
            
            # Generar HTML
            html_output = template.render(**template_data)
            
            # Guardar HTML
            index_path = os.path.join(REPORTS_DIR, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_output)
            
            # Copiar archivos estáticos si no existen
            static_dir = os.path.join(STATIC_DIR)
            dest_static_dir = os.path.join(REPORTS_DIR, 'static')
            
            if os.path.exists(static_dir) and not os.path.exists(dest_static_dir):
                os.makedirs(dest_static_dir, exist_ok=True)
                for item in os.listdir(static_dir):
                    src = os.path.join(static_dir, item)
                    dst = os.path.join(dest_static_dir, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                    elif os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
            
            logger.info(f"Índice de Reportes generado en: {index_path}")
            return index_path
        except Exception as e:
            logger.error(f"Error al generar índice de reportes: {e}")
            return None
   
    def _generate_charts(self, report_dir, user=None):
        charts = {}
        
        # Configurar estilo de los gráficos
        plt.style.use('ggplot')
        sns.set_palette(CHART_COLORS)
        
        if user:
            # Gráficos específicos para el usuario
            user_data = self.analyzer.get_user_data(user)
            if not user_data:
                return charts
            
            # Gráfico de dominios más visitados por el usuario
            try:
                top_domains = user_data['top_domains']
                if not top_domains.empty:
                    plt.figure(figsize=(12, 6))
                    ax = sns.barplot(x='domain', y='visits', data=top_domains)
                    plt.title(f'Top Domains Visited by {user}')
                    plt.xlabel('Domain')
                    plt.ylabel('Visits')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    chart_path = os.path.join(report_dir, f'user_{user}_domains.png')
                    plt.savefig(chart_path)
                    plt.close()
                    charts['user_domains'] = os.path.basename(chart_path)
            except Exception as e:
                logger.error(f"Error al generar gráfico de dominios para usuario {user}: {e}")
            
            # Gráfico de códigos de estado para el usuario
            try:
                status_codes = user_data['status_codes']
                if not status_codes.empty:
                    plt.figure(figsize=(10, 6))
                    ax = sns.barplot(x='status_code', y='count', data=status_codes)
                    plt.title(f'HTTP Status Codes for {user}')
                    plt.xlabel('Status Code')
                    plt.ylabel('Count')
                    plt.tight_layout()
                    chart_path = os.path.join(report_dir, f'user_{user}_status.png')
                    plt.savefig(chart_path)
                    plt.close()
                    charts['user_status'] = os.path.basename(chart_path)
            except Exception as e:
                logger.error(f"Error al generar gráfico de códigos de estado para usuario {user}: {e}")
            
            # Gráfico de tipos de contenido para el usuario
            try:
                content_types = user_data['content_types']
                if not content_types.empty and len(content_types) > 1:
                    plt.figure(figsize=(10, 6))
                    content_types.plot(kind='pie', y='count', labels=content_types['content_type'], autopct='%1.1f%%')
                    plt.title(f'Content Types for {user}')
                    plt.ylabel('')
                    plt.tight_layout()
                    chart_path = os.path.join(report_dir, f'user_{user}_content_types.png')
                    plt.savefig(chart_path)
                    plt.close()
                    charts['user_content_types'] = os.path.basename(chart_path)
            except Exception as e:
                logger.error(f"Error al generar gráfico de tipos de contenido para usuario {user}: {e}")
            
            return charts

        # Gráfico de usuarios con más tráfico
        try:
            top_users = self.analyzer.get_top_users()
            if not top_users.empty:
                plt.figure(figsize=(10, 6))
                ax = sns.barplot(x='user', y='traffic', data=top_users)
                plt.title('Top Usuarios por Trafico')
                plt.xlabel('Usuario')
                plt.ylabel('Trafico (bytes)')
                plt.xticks(rotation=45, ha='right')
                
                # Añadir etiquetas de tráfico legible
                for i, row in enumerate(top_users.itertuples()):
                    ax.text(i, row.traffic, row.traffic_readable, 
                            ha='center', va='bottom', rotation=0)
                
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'top_users.png')
                plt.savefig(chart_path)
                plt.close()
                charts['top_users'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de usuarios: {e}")
        
        # Gráfico de dominios más visitados
        try:
            top_domains = self.analyzer.get_top_domains()
            if not top_domains.empty:
                plt.figure(figsize=(12, 6))
                ax = sns.barplot(x='domain', y='visits', data=top_domains)
                plt.title('Top Sitios por Visitas')
                plt.xlabel('Sitios')
                plt.ylabel('Visitas')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'top_domains.png')
                plt.savefig(chart_path)
                plt.close()
                charts['top_domains'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de dominios: {e}")
        
        # Gráfico de dominios por tráfico
        try:
            top_domains_traffic = self.analyzer.get_top_domains()
            if not top_domains_traffic.empty:
                # Ordenar por tráfico en lugar de visitas
                top_domains_traffic = top_domains_traffic.sort_values('traffic', ascending=False).head(20)
                
                plt.figure(figsize=(12, 6))
                ax = sns.barplot(x='domain', y='traffic', data=top_domains_traffic)
                plt.title('Top Sitios por Tráfico')
                plt.xlabel('Sitios')
                plt.ylabel('Tráfico (bytes)')
                plt.xticks(rotation=45, ha='right')
                
                # Añadir etiquetas de tráfico legible
                for i, row in enumerate(top_domains_traffic.itertuples()):
                    ax.text(i, row.traffic, row.traffic_readable, 
                            ha='center', va='bottom', rotation=0)
                
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'top_domains_traffic.png')
                plt.savefig(chart_path)
                plt.close()
                charts['top_domains_traffic'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de dominios por tráfico: {e}")
        
        # Gráfico de códigos de estado
        try:
            status_codes = self.analyzer.get_status_codes()
            if not status_codes.empty:
                plt.figure(figsize=(10, 6))
                ax = sns.barplot(x='status_code', y='count', data=status_codes)
                plt.title('HTTP Status')
                plt.xlabel('Status')
                plt.ylabel('Total')
                
                # Añadir descripciones como etiquetas
                for i, row in enumerate(status_codes.itertuples()):
                    ax.text(i, row.count/2, row.description, 
                            ha='center', va='center', rotation=90, color='white', fontweight='bold')
                
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'status_codes.png')
                plt.savefig(chart_path)
                plt.close()
                charts['status_codes'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de códigos de estado: {e}")
        
        # Gráfico de tipos de contenido
        try:
            content_types = self.analyzer.get_content_types()
            if not content_types.empty:
                plt.figure(figsize=(10, 6))
                content_types.plot(kind='pie', autopct='%1.1f%%')
                plt.title('Tipo de Contenido')
                plt.ylabel('')
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'content_types.png')
                plt.savefig(chart_path)
                plt.close()
                charts['content_types'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de tipos de contenido: {e}")
        
        # Gráfico de uso por hora
        try:
            hourly_usage = self.analyzer.get_hourly_usage()
            if not hourly_usage.empty:
                plt.figure(figsize=(12, 6))
                ax = sns.lineplot(x='hour', y='requests', data=hourly_usage, marker='o')
                plt.title('Uso por Hora del Día')
                plt.xlabel('Hora')
                plt.ylabel('Solicitudes')
                plt.xticks(range(0, 24, 2))
                plt.grid(True)
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'hourly_usage.png')
                plt.savefig(chart_path)
                plt.close()
                charts['hourly_usage'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de uso por hora: {e}")
        
        # Gráfico de uso por día de la semana
        try:
            daily_usage = self.analyzer.get_daily_usage()
            if not daily_usage.empty:
                plt.figure(figsize=(12, 6))
                ax = sns.barplot(x='day_of_week', y='requests', data=daily_usage)
                plt.title('Uso por Día de la Semana')
                plt.xlabel('Día')
                plt.ylabel('Solicitudes')
                plt.tight_layout()
                chart_path = os.path.join(report_dir, 'daily_usage.png')
                plt.savefig(chart_path)
                plt.close()
                charts['daily_usage'] = os.path.basename(chart_path)
        except Exception as e:
            logger.error(f"Error al generar gráfico de uso por día: {e}")
        
        return charts
    
    def generate_report(self, output_dir=None):
        """
        Genera un informe completo del análisis.
        
        Args:
            output_dir: Directorio de salida para el informe. Si es None, se genera uno automáticamente.
            
        Returns:
            Ruta al directorio del informe generado.
        """
        # Preparar directorio de salida
        if output_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_dir = os.path.join(REPORTS_DIR, f'reporte_{timestamp}')
        else:
            report_dir = output_dir
        
        os.makedirs(report_dir, exist_ok=True)
        
        # Generar gráficos generales
        charts = self._generate_charts(report_dir)
        
        # Obtener datos
        summary = self.analyzer.get_summary()
        top_users = self.analyzer.get_top_users()
        top_domains = self.analyzer.get_top_domains()
        status_codes = self.analyzer.get_status_codes()
        start_date, end_date = self.analyzer.get_date_range()
        
        # Obtener formato de log detectado si está disponible
        log_format = getattr(self.analyzer, 'detected_format', 'No especificado')
        
        # Preparar datos para la plantilla
        template_data = {
            'title': 'Squid Log Analyzer - DGE',
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'No disponible',
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'No disponible',
            'log_format': log_format,
            'log_file': self.analyzer.log_path,
            'summary': summary,
            'top_users': top_users.to_dict('records') if not top_users.empty else [],
            'top_domains': top_domains.to_dict('records') if not top_domains.empty else [],
            'status_codes': status_codes.to_dict('records') if not status_codes.empty else [],
            'charts': charts
        }
        
        # Guardar datos para reportes de usuario
        users_data = {}
        for user in top_users['user'].tolist() if not top_users.empty else []:
            user_data = self.analyzer.get_user_data(user)
            if user_data:
                # Generar gráficos específicos para el usuario
                user_charts = self._generate_charts(report_dir, user)
                
                # Preparar datos para la plantilla de usuario
                user_template_data = {
                    'title': f'Trazas de Usuario: {user}',
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'user_data': user_data,
                    'charts': user_charts
                }
                
                # Guardar datos para el usuario
                users_data[user] = user_template_data
                
                # Generar HTML para el usuario
                self._generate_user_report(user, user_template_data, report_dir)
        
        # Guardar datos de usuarios para JavaScript
        with open(os.path.join(report_dir, 'users_data.js'), 'w', encoding='utf-8') as f:
            f.write(f"const usersData = {json.dumps({'users': list(users_data.keys())})};\n")
        
        # Cargar plantilla
        template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template('report_template.html')
        
        # Generar HTML
        html_output = template.render(**template_data)
        
        # Guardar HTML
        report_path = os.path.join(report_dir, 'index.html')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        # Copiar archivos estáticos
        self._copy_static_files(report_dir)
        
        # Generar índice de reportes
        try:
            SquidReportGenerator.generate_reports_index()
        except Exception as e:
            logger.error(f"Error al generar índice de reportes: {e}")
         
        logger.info(f"Reporte generado en: {report_path}")
        return report_dir
    
    def _generate_user_report(self, username, template_data, report_dir):
        """
        Genera un Reporte HTML específico para un usuario.
        
        Args:
            username: Nombre del usuario
            template_data: Datos para la plantilla
            report_dir: Directorio donde se guardará el Reporte
        """
        try:
            # Cargar plantilla
            template_loader = jinja2.FileSystemLoader(searchpath=TEMPLATES_DIR)
            template_env = jinja2.Environment(loader=template_loader)
            template = template_env.get_template('user_report_template.html')
            
            # Generar HTML
            html_output = template.render(**template_data)
            
            # Guardar HTML
            user_report_path = os.path.join(report_dir, f'user_{username}.html')
            with open(user_report_path, 'w', encoding='utf-8') as f:
                f.write(html_output)
                
            logger.info(f"Reporte de usuario generado: {user_report_path}")
        except Exception as e:
            logger.error(f"Error al generar reporte para usuario {username}: {e}")
    
    def _copy_static_files(self, report_dir):
        """
        Copia archivos estáticos al directorio del Reporte.
        
        Args:
            report_dir: Directorio donde se copiaran los archivos
        """
        try:
            dest_static_dir = os.path.join(report_dir, 'static')
            os.makedirs(dest_static_dir, exist_ok=True)
            
            # Copiar CSS, JS e imágenes
            for subdir in ['css', 'js', 'img', 'webfonts']:
                src_dir = os.path.join(STATIC_DIR, subdir)
                dst_dir = os.path.join(dest_static_dir, subdir)
                
                if os.path.exists(src_dir):
                    os.makedirs(dst_dir, exist_ok=True)
                    for item in os.listdir(src_dir):
                        src = os.path.join(src_dir, item)
                        dst = os.path.join(dst_dir, item)
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)
                            
            logger.info(f"Archivos estáticos copiados a {dest_static_dir}")
        except Exception as e:
            logger.error(f"Error al copiar archivos estáticos: {e}")
    
    def generate_json_report(self, output_file=None):
        """
        Genera un informe en formato JSON.
        
        Args:
            output_file: Ruta al archivo de salida. Si es None, se genera uno automáticamente.
            
        Returns:
            Ruta al archivo JSON generado.
        """
        try:
            # Obtener datos
            summary = self.analyzer.get_summary()
            top_users = self.analyzer.get_top_users()
            top_domains = self.analyzer.get_top_domains()
            status_codes = self.analyzer.get_status_codes()
            start_date, end_date = self.analyzer.get_date_range()
            
            # Preparar datos para JSON
            report_data = {
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'No disponible',
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'No disponible',
                'log_file': self.analyzer.log_path,
                'log_format': getattr(self.analyzer, 'detected_format', 'No especificado'),
                'summary': summary,
                'top_users': top_users.to_dict('records') if not top_users.empty else [],
                'top_domains': top_domains.to_dict('records') if not top_domains.empty else [],
                'status_codes': status_codes.to_dict('records') if not status_codes.empty else []
            }
            
            # Determinar ruta de salida
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = os.path.join(REPORTS_DIR, f'reporte_{timestamp}.json')
            
            # Guardar JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Reporte JSON generado en: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error al generar reporte JSON: {e}")
            return None
    
    def generate_csv_reports(self, output_dir=None):
        """
        Genera informes en formato CSV.
        
        Args:
            output_dir: Directorio de salida para los archivos CSV. Si es None, se genera uno automáticamente.
            
        Returns:
            Ruta al directorio de informes CSV.
        """
        try:
            # Preparar directorio de salida
            if output_dir is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_dir = os.path.join(REPORTS_DIR, f'csv_reporte_{timestamp}')
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Obtener datos
            top_users = self.analyzer.get_top_users()
            top_domains = self.analyzer.get_top_domains()
            status_codes = self.analyzer.get_status_codes()
            hourly_usage = self.analyzer.get_hourly_usage()
            daily_usage = self.analyzer.get_daily_usage()
            
            # Guardar CSVs
            if not top_users.empty:
                top_users.to_csv(os.path.join(output_dir, 'top_users.csv'), index=False)
            
            if not top_domains.empty:
                top_domains.to_csv(os.path.join(output_dir, 'top_domains.csv'), index=False)
            
            if not status_codes.empty:
                status_codes.to_csv(os.path.join(output_dir, 'status_codes.csv'), index=False)
            
            if not hourly_usage.empty:
                hourly_usage.to_csv(os.path.join(output_dir, 'hourly_usage.csv'), index=False)
            
            if not daily_usage.empty:
                daily_usage.to_csv(os.path.join(output_dir, 'daily_usage.csv'), index=False)
            
            # Crear archivo README
            with open(os.path.join(output_dir, 'README.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Informes CSV generados el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Archivo de log analizado: {self.analyzer.log_path}\n")
                f.write(f"Formato de log: {getattr(self.analyzer, 'detected_format', 'No especificado')}\n\n")
                f.write("Archivos incluidos:\n")
                f.write("- top_users.csv: Usuarios con más tráfico\n")
                f.write("- top_domains.csv: Dominios más visitados\n")
                f.write("- status_codes.csv: Distribución de códigos de estado HTTP\n")
                f.write("- hourly_usage.csv: Uso por hora del día\n")
                f.write("- daily_usage.csv: Uso por día de la semana\n")
            
            logger.info(f"Informes CSV generados en: {output_dir}")
            return output_dir
        except Exception as e:
            logger.error(f"Error al generar informes CSV: {e}")
            return None
