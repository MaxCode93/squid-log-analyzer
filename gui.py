import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import webbrowser
from datetime import datetime, timedelta
import logging

from analyzer import SquidLogAnalyzer
from report_generator import SquidReportGenerator
from config import DEFAULT_CONFIG, REPORTS_DIR

# Configurar logging
logger = logging.getLogger('SLAM.GUI')

class SquidAnalyzerGUI(tk.Tk):
    """Interfaz gráfica para el analizador de logs de Squid."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Squid Log Analyzer")
        self.geometry("800x600")
        self.minsize(600, 500)
        
        # Variables
        self.log_file_var = tk.StringVar(value=DEFAULT_CONFIG["squid_log_path"])
        self.days_var = tk.IntVar(value=0)
        self.user_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Listo para analizar")
        self.progress_var = tk.DoubleVar(value=0)
        self.format_var = tk.StringVar(value="auto")
        
        # Crear interfaz
        self._create_widgets()
        self._create_menu()
        
        # Centrar ventana
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """Crea los widgets de la interfaz."""
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sección de archivo de log
        log_frame = ttk.LabelFrame(main_frame, text="Archivo de Log", padding=10)
        log_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(log_frame, text="Ruta del archivo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(log_frame, textvariable=self.log_file_var, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(log_frame, text="Examinar", command=self._browse_log_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Sección de opciones
        options_frame = ttk.LabelFrame(main_frame, text="Opciones de análisis", padding=10)
        options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(options_frame, text="Días a analizar (0 = todos):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(options_frame, from_=0, to=365, textvariable=self.days_var, width=5).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(options_frame, text="Usuario específico (opcional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.user_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(options_frame, text="Formato de log:").grid(row=2, column=0, sticky=tk.W, pady=5)
        format_combo = ttk.Combobox(options_frame, textvariable=self.format_var, width=15)
        format_combo['values'] = ('auto', 'detailed', 'common', 'squid_native', 'custom', 'custom_new')
        format_combo.current(0)
        format_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Botones de acción
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(actions_frame, text="Analizar", command=self._analyze).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Ver último informe", command=self._open_last_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Salir", command=self.quit).pack(side=tk.RIGHT, padx=5)
        
        # Barra de progreso y estado
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor=tk.W)
        
        # Área de resultados
        results_frame = ttk.LabelFrame(main_frame, text="Resultados", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.results_text = tk.Text(results_frame, wrap=tk.WORD, height=10)
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar para el área de resultados
        scrollbar = ttk.Scrollbar(self.results_text, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)
        
        # Configurar grid
        log_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(1, weight=1)
    
    def _create_menu(self):
        """Crea el menú de la aplicación."""
        menubar = tk.Menu(self)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir archivo de log", command=self._browse_log_file)
        file_menu.add_command(label="Ver último informe", command=self._open_last_report)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Análisis
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="Analizar log", command=self._analyze)
        analysis_menu.add_command(label="Limpiar resultados", command=self._clear_results)
        menubar.add_cascade(label="Análisis", menu=analysis_menu)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Ver índice de informes", command=self._open_reports_index)
        tools_menu.add_command(label="Configuración", command=self._show_config)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self._show_about)
        help_menu.add_command(label="Ayuda", command=self._show_help)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        
        self.config(menu=menubar)
    
    def _browse_log_file(self):
        """Abre un diálogo para seleccionar el archivo de log."""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de log",
            filetypes=[("Archivos de log", "*.log"), ("Todos los archivos", "*.*")]
        )
        
        if filename:
            self.log_file_var.set(filename)
    
    def _analyze(self):
        """Inicia el análisis del archivo de log."""
        log_file = self.log_file_var.get()
        
        if not log_file:
            messagebox.showerror("Error", "Debe seleccionar un archivo de log")
            return
        
        if not os.path.isfile(log_file):
            messagebox.showerror("Error", f"El archivo {log_file} no existe")
            return
        
        # Iniciar análisis en un hilo separado
        self.status_var.set("Analizando...")
        self.progress_var.set(0)
        
        # Deshabilitar botones durante el análisis
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.DISABLED)
        
        # Limpiar resultados anteriores
        self._clear_results()
        
        # Iniciar hilo de análisis
        threading.Thread(target=self._run_analysis, daemon=True).start()
    
    def _run_analysis(self):
        """Ejecuta el análisis en un hilo separado."""
        try:
            log_file = self.log_file_var.get()
            days = self.days_var.get()
            user = self.user_var.get()
            log_format = self.format_var.get()
            
            # Actualizar progreso
            self._update_status("Iniciando análisis...", 10)
            
            # Crear analizador con el formato especificado
            analyzer = SquidLogAnalyzer(log_file, log_format)
            
            # Leer y procesar el archivo
            self._update_status("Procesando archivo de log...", 20)
            analyzer.to_dataframe()
            
            # Mostrar formato detectado si se usó auto
            if log_format == 'auto' and hasattr(analyzer, 'detected_format'):
                self._update_results(f"Formato de log detectado: {analyzer.detected_format}")
            
            # Filtrar por fecha si se especificó
            if days > 0:
                self._update_status(f"Filtrando por los últimos {days} días...", 40)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                analyzer = analyzer.filter_by_date(start_date, end_date)
            
            # Filtrar por usuario si se especificó
            if user:
                self._update_status(f"Filtrando por usuario: {user}...", 60)
                user_data = analyzer.get_user_data(user)
                
                if user_data:
                    self._update_results(f"\nDatos para el usuario {user}:")
                    self._update_results(f"Total de solicitudes: {user_data['total_requests']}")
                    self._update_results(f"Tráfico total: {user_data['traffic_readable']}")
                    self._update_results("\nDominios más visitados:")
                    
                    for domain in user_data['top_domains'].itertuples():
                        self._update_results(f"  {domain.domain}: {domain.visits} visitas")
                    
                    self._update_status("Análisis completado", 100)
                else:
                    self._update_results(f"No se encontraron datos para el usuario {user}")
                    self._update_status("No se encontraron datos", 100)
                
                # Habilitar botones
                self.after(0, self._enable_buttons)
                return
            
            # Generar informe completo
            self._update_status("Generando informe completo...", 70)
            report_generator = SquidReportGenerator(analyzer)
            report_dir = report_generator.generate_report()
            
            # Mostrar resumen
            summary = analyzer.get_summary()
            self._update_results("\nResumen del análisis:")
            self._update_results(f"Total de solicitudes: {summary['total_requests']}")
            self._update_results(f"Tráfico total: {summary['total_bytes'] / (1024*1024):.2f} MB")
            self._update_results(f"Usuarios únicos: {summary['unique_users']}")
            self._update_results(f"IPs únicas: {summary['unique_ips']}")
            
            # Mostrar ruta del informe
            report_path = os.path.join(report_dir, 'index.html')
            self._update_results(f"\nInforme generado en: {report_path}")
            
            # Preguntar si desea abrir el informe
            self.after(0, lambda: self._ask_open_report(report_path))
            
            self._update_status("Análisis completado", 100)
        except Exception as e:
            self._update_results(f"\nError durante el análisis: {str(e)}")
            self._update_status("Error en el análisis", 0)
            logger.exception("Error durante el análisis")
        finally:
            # Habilitar botones
            self.after(0, self._enable_buttons)
    
    def _update_status(self, message, progress):
        """Actualiza el estado y la barra de progreso."""
        self.after(0, lambda: self.status_var.set(message))
        self.after(0, lambda: self.progress_var.set(progress))
    
    def _update_results(self, message):
        """Actualiza el área de resultados."""
        self.after(0, lambda: self.results_text.insert(tk.END, message + "\n"))
        self.after(0, lambda: self.results_text.see(tk.END))
    
    def _clear_results(self):
        """Limpia el área de resultados."""
        self.results_text.delete(1.0, tk.END)
    
    def _enable_buttons(self):
        """Habilita los botones de la interfaz."""
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=tk.NORMAL)
    
    def _ask_open_report(self, report_path):
        """Pregunta si desea abrir el informe en el navegador."""
        answer = messagebox.askyesno(
            "Informe generado",
            "El informe ha sido generado. ¿Desea abrirlo en el navegador?"
        )
        
        if answer:
            self._open_report(report_path)
    
    def _open_report(self, report_path):
        """Abre el informe en el navegador."""
        try:
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el navegador: {e}")
            logger.error(f"Error al abrir el navegador: {e}")
    
    def _open_last_report(self):
        """Abre el último informe generado."""
        try:
            # Buscar el directorio de informe más reciente
            reports = [os.path.join(REPORTS_DIR, d) for d in os.listdir(REPORTS_DIR) 
                      if os.path.isdir(os.path.join(REPORTS_DIR, d))]
            
            if not reports:
                messagebox.showinfo("Información", "No hay informes generados")
                return
            
            # Ordenar por fecha de modificación (más reciente primero)
            reports.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Verificar si existe el archivo index.html
            report_path = os.path.join(reports[0], 'index.html')
            if not os.path.isfile(report_path):
                messagebox.showerror("Error", "El informe no existe o está incompleto")
                return
            
            # Abrir el informe
            self._open_report(report_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el último informe: {e}")
            logger.error(f"Error al abrir el último informe: {e}")
    
    def _open_reports_index(self):
        """Abre el índice de informes generados."""
        try:
            from report_generator import SquidReportGenerator
            index_path = SquidReportGenerator.generate_reports_index()
            
            if index_path and os.path.isfile(index_path):
                self._open_report(index_path)
            else:
                messagebox.showinfo("Información", "No se pudo generar el índice de informes")
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar índice de informes: {e}")
            logger.error(f"Error al generar índice de informes: {e}")
    
    def _show_config(self):
        """Muestra la ventana de configuración."""
        config_window = tk.Toplevel(self)
        config_window.title("Configuración")
        config_window.geometry("500x400")
        config_window.resizable(True, True)
        config_window.transient(self)
        config_window.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(config_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para pestañas
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pestaña de configuración general
        general_tab = ttk.Frame(notebook, padding=10)
        notebook.add(general_tab, text="General")
        
        # Configuración de rutas
        ttk.Label(general_tab, text="Ruta de logs de Squid:").grid(row=0, column=0, sticky=tk.W, pady=5)
        squid_log_entry = ttk.Entry(general_tab, width=40)
        squid_log_entry.insert(0, DEFAULT_CONFIG["squid_log_path"])
        squid_log_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(general_tab, text="Directorio de informes:").grid(row=1, column=0, sticky=tk.W, pady=5)
        reports_dir_entry = ttk.Entry(general_tab, width=40)
        reports_dir_entry.insert(0, REPORTS_DIR)
        reports_dir_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Configuración de análisis
        ttk.Label(general_tab, text="Intervalo de actualización (seg):").grid(row=2, column=0, sticky=tk.W, pady=5)
        refresh_entry = ttk.Entry(general_tab, width=10)
        refresh_entry.insert(0, str(DEFAULT_CONFIG["refresh_interval"]))
        refresh_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(general_tab, text="Formato de log predeterminado:").grid(row=3, column=0, sticky=tk.W, pady=5)
        format_combo = ttk.Combobox(general_tab, width=15)
        format_combo['values'] = ('auto', 'detailed', 'common', 'squid_native', 'custom', 'custom_new')
        format_combo.current(0)
        format_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Pestaña de exclusiones
        exclusions_tab = ttk.Frame(notebook, padding=10)
        notebook.add(exclusions_tab, text="Exclusiones")
        
        ttk.Label(exclusions_tab, text="Dominios excluidos:").grid(row=0, column=0, sticky=tk.W, pady=5)
        domains_text = tk.Text(exclusions_tab, width=40, height=5)
        domains_text.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        for domain in DEFAULT_CONFIG["excluded_domains"]:
            domains_text.insert(tk.END, domain + "\n")
        
        ttk.Label(exclusions_tab, text="Usuarios excluidos:").grid(row=1, column=0, sticky=tk.W, pady=5)
        users_text = tk.Text(exclusions_tab, width=40, height=5)
        users_text.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        for user in DEFAULT_CONFIG["excluded_users"]:
            users_text.insert(tk.END, user + "\n")
        
        # Pestaña de apariencia
        appearance_tab = ttk.Frame(notebook, padding=10)
        notebook.add(appearance_tab, text="Apariencia")
        
        ttk.Label(appearance_tab, text="Tema:").grid(row=0, column=0, sticky=tk.W, pady=5)
        theme_combo = ttk.Combobox(appearance_tab, width=15)
        theme_combo['values'] = ('light', 'dark', 'system')
        theme_combo.current(0 if DEFAULT_CONFIG["theme"] == "light" else 1)
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(appearance_tab, text="Idioma:").grid(row=1, column=0, sticky=tk.W, pady=5)
        lang_combo = ttk.Combobox(appearance_tab, width=15)
        lang_combo['values'] = ('es', 'en')
        lang_combo.current(0 if DEFAULT_CONFIG["language"] == "es" else 1)
        lang_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Botones de acción
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Guardar", command=lambda: self._save_config(
            squid_log_entry.get(),
            reports_dir_entry.get(),
            refresh_entry.get(),
            format_combo.get(),
            domains_text.get(1.0, tk.END),
            users_text.get(1.0, tk.END),
            theme_combo.get(),
            lang_combo.get(),
            config_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(buttons_frame, text="Cancelar", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Configurar grid
        general_tab.columnconfigure(1, weight=1)
        exclusions_tab.columnconfigure(1, weight=1)
        appearance_tab.columnconfigure(1, weight=1)
    
    def _save_config(self, squid_log, reports_dir, refresh, log_format, domains, users, theme, language, window):
        """Guarda la configuración."""
        try:
            # Aquí se implementaría la lógica para guardar la configuración
            # Por ahora, solo mostramos un mensaje
            messagebox.showinfo("Información", "La funcionalidad de guardar configuración no está implementada aún")
            window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la configuración: {e}")
            logger.error(f"Error al guardar la configuración: {e}")
    
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        messagebox.showinfo(
            "Acerca de",
            "Squid Log Analyzer (SLAM)\n\n"
            "Una herramienta para analizar logs de Squid Proxy.\n\n"
            "Versión: 1.1.1\n"
            "© 2023 - Todos los derechos reservados"
        )
    
    def _show_help(self):
        """Muestra la ayuda de la aplicación."""
        help_window = tk.Toplevel(self)
        help_window.title("Ayuda de SLAM")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        help_window.transient(self)
        
        # Frame principal
        main_frame = ttk.Frame(help_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Ayuda de Squid Log Analyzer", font=("Helvetica", 14, "bold")).pack(pady=10)
        
        # Área de texto con scrollbar
        help_frame = ttk.Frame(main_frame)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text = tk.Text(help_frame, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(help_frame, command=help_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_text.config(yscrollcommand=scrollbar.set)
        
        # Contenido de la ayuda
        help_content = """
# Guía de uso de SLAM

## Introducción
SLAM (Squid Log Analyzer Manager) es una herramienta diseñada para analizar los archivos de log del proxy Squid y generar informes detallados sobre su uso.

## Funcionalidades principales

### 1. Análisis de logs
- Seleccione un archivo de log de Squid
- Elija el formato del log (o use detección automática)
- Filtre por fecha o usuario específico
- Genere informes completos con estadísticas y gráficos

### 2. Formatos de log soportados
- auto: Detección automática del formato
- detailed: Formato detallado personalizado
- common: Formato común de logs web (CLF)
- squid_native: Formato nativo de Squid
- custom: Formato personalizado 1
- custom_new: Formato personalizado 2

### 3. Filtros disponibles
- Por rango de fechas (últimos N días)
- Por usuario específico

### 4. Visualización de informes
- Informes HTML interactivos
- Gráficos de uso por dominio, usuario, hora, etc.
- Estadísticas detalladas de tráfico

## Consejos de uso
- Para un análisis completo, use la detección automática de formato
- Si conoce el formato exacto de su log, selecciónelo para un análisis más preciso
- Los informes se guardan en el directorio configurado y pueden ser accedidos posteriormente
- Use el índice de informes para acceder a todos los informes generados

## Solución de problemas
- Si el análisis falla, verifique que el archivo de log tenga el formato correcto
- Asegúrese de tener permisos de lectura sobre el archivo de log
- Para logs muy grandes, el análisis puede tomar varios minutos
        """
        
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        # Botón de cerrar
        ttk.Button(main_frame, text="Cerrar", command=help_window.destroy).pack(pady=10)

if __name__ == "__main__":
    app = SquidAnalyzerGUI()
    app.mainloop()
