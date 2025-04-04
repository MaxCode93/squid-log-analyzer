import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import webbrowser
from datetime import datetime, timedelta

from analyzer import SquidLogAnalyzer
from report_generator import SquidReportGenerator
from config import DEFAULT_CONFIG, REPORTS_DIR

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
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self._show_about)
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
            
            # Actualizar progreso
            self._update_status("Iniciando análisis...", 10)
            
            # Crear analizador
            analyzer = SquidLogAnalyzer(log_file)
            
            # Leer y procesar el archivo
            self._update_status("Procesando archivo de log...", 20)
            analyzer.to_dataframe()
            
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
    
    def _show_about(self):
        """Muestra información sobre la aplicación."""
        messagebox.showinfo(
            "Acerca de",
            "Squid Log Analyzer(SLAM)\n\n"
            "Una herramienta para analizar logs de Squid Proxy.\n\n"
            "Versión: 1.1.1\n"
            "© 2025 - Todos los derechos reservados"
        )

if __name__ == "__main__":
    app = SquidAnalyzerGUI()
    app.mainloop()
