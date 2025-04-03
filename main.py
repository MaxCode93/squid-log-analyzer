import sys
import os
import argparse
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser

from analyzer import SquidLogAnalyzer
from report_generator import SquidReportGenerator
from config import DEFAULT_CONFIG, REPORTS_DIR

def parse_args():
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description='Squid Log Analyzer')
    parser.add_argument('log_file', nargs='?', default=DEFAULT_CONFIG["squid_log_path"], help='Path to the Squid log file')  # Usar ruta por defecto
    parser.add_argument('-o', '--output', help='Output directory for the report')
    parser.add_argument('-d', '--days', type=int, default=0, help='Number of days to analyze (0 for all)')
    parser.add_argument('-u', '--user', help='Filter by specific user')
    parser.add_argument('-g', '--gui', action='store_true', help='Launch GUI mode')
    parser.add_argument('-f', '--format', choices=['detailed', 'optimized'], default='optimized',
                       help='Log format: detailed or optimized (default: optimized)')
    
    return parser.parse_args()

def run_gui():
    """Ejecuta la interfaz gráfica."""
    try:
        from gui import SquidAnalyzerGUI
        app = SquidAnalyzerGUI()
        app.mainloop()
    except ImportError as e:
        print(f"Error al cargar la interfaz gráfica: {e}")
        print("Ejecutando en modo consola...")
        run_cli([])

def run_cli(args_list):
    """Ejecuta el analizador en modo consola."""
    args = parse_args()
    
    # Si no se especificó un archivo de log, solicitar uno
    if not args.log_file:
        print("No se especificó un archivo de log.")
        if sys.stdin.isatty():  # Si estamos en una terminal interactiva
            log_file = input("Ingrese la ruta al archivo de log: ")
            if not log_file:
                print("No se proporcionó un archivo de log. Saliendo.")
                return
            args.log_file = log_file
        else:
            print("No se proporcionó un archivo de log. Saliendo.")
            return
    
    # Verificar que el archivo existe
    if not os.path.isfile(args.log_file):
        print(f"El archivo {args.log_file} no existe.")
        return
    
    print(f"Analizando archivo de log: {args.log_file}")
    print(f"Formato de log: {args.format}")
    
    # Crear analizador
    analyzer = SquidLogAnalyzer(args.log_file)
    
    # Leer y procesar el archivo
    print("Procesando archivo de log...")
    analyzer.to_dataframe()
    
    # Filtrar por fecha si se especificó
    if args.days > 0:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        print(f"Filtrando por fecha: desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
        analyzer = analyzer.filter_by_date(start_date, end_date)
    
    # Filtrar por usuario si se especificó
    if args.user:
        print(f"Filtrando por usuario: {args.user}")
        user_data = analyzer.get_user_data(args.user)
        if user_data:
            print(f"\nDatos para el usuario {args.user}:")
            print(f"Total de solicitudes: {user_data['total_requests']}")
            print(f"Tráfico total: {user_data['traffic_readable']}")
            print("\nDominios más visitados:")
            for domain in user_data['top_domains'].itertuples():
                print(f"  {domain.domain}: {domain.visits} visitas")
        else:
            print(f"No se encontraron datos para el usuario {args.user}")
        return
    
    # Generar informe completo
    print("Generando informe completo...")
    report_generator = SquidReportGenerator(analyzer)
    report_dir = report_generator.generate_report(args.output)
    
    # Mostrar resumen
    summary = analyzer.get_summary()
    print("\nResumen del análisis:")
    print(f"Total de solicitudes: {summary['total_requests']}")
    print(f"Tráfico total: {summary['total_bytes'] / (1024*1024):.2f} MB")
    print(f"Usuarios únicos: {summary['unique_users']}")
    print(f"IPs únicas: {summary['unique_ips']}")
    
    # Abrir el informe en el navegador
    report_path = os.path.join(report_dir, 'index.html')
    print(f"\nInforme generado en: {report_path}")

def main():
    """Función principal."""
    args = parse_args()
    
    # Asegurar que existan los directorios necesarios
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    if args.gui:
        run_gui()
    else:
        run_cli(sys.argv[1:])

if __name__ == "__main__":
    main()
