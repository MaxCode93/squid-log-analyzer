import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import jinja2
import shutil
import json
import re
from config import TEMPLATES_DIR, REPORTS_DIR, CHART_COLORS, STATIC_DIR

class SquidReportGenerator:
    """Clase para generar Reportes a partir del análisis de logs de Squid."""
    
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
            
            print(f"Índice de Reportes generado en: {index_path}")
            return index_path
        except Exception as e:
            print(f"Error al generar índice de reportes: {e}")
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
                print(f"Error al generar gráfico de dominios para usuario {user}: {e}")
            
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
                print(f"Error al generar gráfico de códigos de estado para usuario {user}: {e}")
            
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
            print(f"Error al generar gráfico de usuarios: {e}")
        
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
            print(f"Error al generar gráfico de dominios: {e}")
        
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
            print(f"Error al generar gráfico de códigos de estado: {e}")
        
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
            print(f"Error al generar gráfico de tipos de contenido: {e}")
        
        return charts
    
    def generate_report(self, output_dir=None):
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
        
        # Preparar datos para la plantilla
        template_data = {
            'title': 'Squid Log Analyzer - DGE',
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else 'No disponible',
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else 'No disponible',
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
                    'title': f'Trasas de Usuario: {user}',
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
        
        SquidReportGenerator.generate_reports_index()
         
        print(f"Reporte generado en: {report_path}")
        return report_dir
    
    def _generate_user_report(self, username, template_data, report_dir):
        """
        Genera un Reporte HTML específico para un usuario.
        
        Args:
            username: Nombre del usuario
            template_data: Datos para la plantilla
            report_dir: Directorio donde se guardará el Reporte
        """
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
    
    def _copy_static_files(self, report_dir):
        """
        Copia archivos estáticos al directorio del Reporte.
        
        Args:
            report_dir: Directorio donde se copiaran los archivos
        """
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
