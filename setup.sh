#!/bin/bash
# SLAM (Squid Log Analyzer Manager) - By Maxwell
# v1.1.1

# Configuración de colores
RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
MAGENTA='\033[1;35m'
CYAN='\033[1;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

INSTALL_DIR="/etc/slam"
LOG_DIR="/var/log/slam"
BIN_DIR="/usr/local/bin"
CRON_JOB="0 * * * * root /usr/local/bin/slam"
REPORTS_DIR="/var/www/slam"
INSTALL_LOG="/var/log/slam_install.log"
SQUID_CONF="/etc/squid/squid.conf"
SQUID_LOG_FORMAT='logformat custom %>a %un "%rm %ru HTTP/%rv" %>Hs %<st "%{User-Agent}>h" %Ss:%Sh'
SQUID_ACCESS_LOG='access_log daemon:/var/log/squid/access.log custom'

safe_sleep() {
    local duration=$1
    if sleep 0.1 2>/dev/null; then
        sleep $duration 2>/dev/null || sleep $(printf "%.0f" "$duration")
    else
        sleep $(printf "%.0f" "$duration")
    fi
}

spinner() {
    local pid=$!
    local delay=0.1
    local spinstr='|/-\'
    
    trap 'printf "\n"; exit 1' SIGINT
    
    while kill -0 $pid 2>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        safe_sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

progress_bar() {
    local duration=${1:-1}
    local bar_length=30
    local sleep_interval
    
    if command -v bc >/dev/null; then
        sleep_interval=$(bc -l <<< "$duration/$bar_length" 2>/dev/null || echo 0.03)
    else
        sleep_interval=$(awk -v d="$duration" -v bl="$bar_length" 'BEGIN {print d/bl}' 2>/dev/null || echo 0.03)
    fi
    
    printf "["
    for ((i=0; i<=bar_length; i++)); do
        printf "#"
        safe_sleep $sleep_interval
    done
    printf "]"
    echo
}

show_credits() {
    clear
    echo -e "${MAGENTA}"
    echo "   _____ _               __  __   "
    echo "  / ____| |        /\   |  \/  |  "
    echo " | (___ | |       /  \  | \  / |  "
    echo "  \___ \| |      / /\ \ | |\/| |  "
    echo "  ____) | |____ / ____ \| |  | |  "
    echo " |_____/|______/_/    \_|_|  |_|  "
    echo -e "${NC}"
    echo -e "${CYAN} SQUID LOG ANALYZER MANAGER${NC}"
    echo -e "${YELLOW} Versión 1.1 - By Maxwell${NC}"
    echo -e "${BLUE}--------------------------------------${NC}"
    echo
    safe_sleep 1.5
}

check_root() {
    if [ "$(id -u)" -ne 0 ]; then
        echo -e "${RED}✗ Este script debe ejecutarse como root${NC}"
        exit 1
    fi
}

check_bc() {
    if ! command -v bc >/dev/null; then
        echo -ne "${YELLOW}■ Instalando bc para cálculos...${NC}"
        (apt-get install -y bc >/dev/null 2>&1) & spinner
        echo -e " ${GREEN}✓${NC}"
    fi
}

check_squid() {
    echo -e "${BLUE}■ Verificando instalación de Squid...${NC}"
    if systemctl list-unit-files | grep -q squid; then
        echo -e "${GREEN}  ✓ Squid está instalado${NC}"
        SQUID_INSTALLED=true
    else
        echo -e "${YELLOW}  ! Squid no está instalado${NC}"
        echo -e "${YELLOW}  ! El análisis funcionará pero necesitarás instalar Squid después${NC}"
        SQUID_INSTALLED=false
    fi
    safe_sleep 1
}

configure_squid() {
    echo -e "${BLUE}■ Configuración de Squid${NC}"
    
    if [ ! -f "$SQUID_CONF" ]; then
        echo -e "${YELLOW}  ! Archivo squid.conf no encontrado${NC}"
        return
    fi
    
	echo -e "${YELLOW}■ Es necesario aplicar un formato de log personalizado al Squid.${NC}"
	echo -e "${YELLOW}■ Eje: 192.168.1.10 johndoe GET /images/logo.png HTTP/1.1 200 45 Mozilla/5.0 (Windows NT 10.0; Win64; x64) TCP_HIT:-${NC}"
    read -p "¿Deseas configurar automáticamente el formato de logs en squid.conf? [s/N]: " choice
    case "$choice" in
        s|S|y|Y)
            echo -ne "${YELLOW}  Configurando formato de log...${NC}"
            
            cp "$SQUID_CONF" "${SQUID_CONF}.bak"
            
            if grep -q "^logformat custom" "$SQUID_CONF"; then
                sed -i "/^logformat custom/c\\$SQUID_LOG_FORMAT" "$SQUID_CONF"
            else
                echo "$SQUID_LOG_FORMAT" >> "$SQUID_CONF"
            fi
            
            if grep -q "^access_log" "$SQUID_CONF"; then
                sed -i "/^access_log/c\\$SQUID_ACCESS_LOG" "$SQUID_CONF"
            else
                echo "$SQUID_ACCESS_LOG" >> "$SQUID_CONF"
            fi
            
            if [ "$SQUID_INSTALLED" = true ]; then
                systemctl restart squid >/dev/null 2>&1
            fi
            
            echo -e " ${GREEN}✓${NC}"
            ;;
        *)
            echo -e "${YELLOW}  ✓ Saltando configuración de squid.conf${NC}"
            ;;
    esac
}

install_packages() {
    echo -e "${BLUE}■ Instalando dependencias del sistema...${NC}"
    
    echo -ne "${YELLOW}  Actualizando repositorios...${NC}"
    (apt-get update >/dev/null 2>&1) & spinner
    echo -e " ${GREEN}✓${NC}"
    
    declare -a packages=("python3" "python3-pip" "python3-tk")
    for pkg in "${packages[@]}"; do
        echo -ne "${YELLOW}  Instalando $pkg...${NC}"
        (DEBIAN_FRONTEND=noninteractive apt-get install -y $pkg >/dev/null 2>&1) & spinner
        echo -e " ${GREEN}✓${NC}"
    done
    
    echo -e "${YELLOW}■ Instalando módulos Python...${NC}"
    declare -a py_modules=("pandas" "matplotlib" "seaborn" "Jinja2")
    for module in "${py_modules[@]}"; do
        echo -ne "  ${CYAN}»${NC} Instalando ${WHITE}$module${NC}"
        (pip install --break-system-packages $module >/dev/null 2>&1) & spinner
        echo -e " ${GREEN}✓${NC}"
    done
    
    (python3 -c "
try:
    import pandas, matplotlib, seaborn, jinja2
    print('\n${GREEN}✓ Todos los módulos instalados correctamente${NC}')
except ImportError as e:
    print('\n${RED}✗ Error: ' + str(e) + '${NC}')
    exit(1)
" >/dev/null 2>&1) & spinner
}

create_dirs() {
    echo -e "${BLUE}■ Creando estructura de directorios...${NC}"
    declare -a dirs=("$INSTALL_DIR" "$LOG_DIR" "$INSTALL_DIR/templates" "$INSTALL_DIR/static" "$REPORTS_DIR")
    
    for dir in "${dirs[@]}"; do
        echo -ne "${YELLOW}  Creando $dir...${NC}"
        (mkdir -p "$dir" && chmod 755 "$dir") & spinner
        echo -e " ${GREEN}✓${NC}"
    done
}

copy_files() {
    echo -e "${BLUE}■ Copiando archivos del proyecto...${NC}"
    
    declare -a main_files=("analyzer.py" "gui.py" "main.py" "report_generator.py" "config.py")
    for file in "${main_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}  ✗ Error: Archivo $file no encontrado${NC}"
            exit 1
        fi
        echo -ne "${YELLOW}  Copiando $file...${NC}"
        (cp "$file" "$INSTALL_DIR/") & spinner
        echo -e " ${GREEN}✓${NC}"
    done
    
    declare -a directories=("templates" "static")
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            echo -e "${RED}  ✗ Error: Directorio $dir no encontrado${NC}"
            exit 1
        fi
        echo -ne "${YELLOW}  Copiando $dir...${NC}"
        (cp -r "$dir" "$INSTALL_DIR/" && \
         find "$INSTALL_DIR/$dir" -type d -exec chmod 755 {} \; && \
         find "$INSTALL_DIR/$dir" -type f -exec chmod 644 {} \;) & spinner
        echo -e " ${GREEN}✓${NC}"
    done
    
    echo -e "${BLUE}■ Creando scripts ejecutables...${NC}"
    
    echo -ne "${YELLOW}  Creando slam...${NC}"
    cat > "$BIN_DIR/slam" << 'EOF'
#!/bin/bash
INSTALL_DIR="/etc/slam"
LOG_FILE="/var/log/squid/access.log"
OUTPUT_DIR="/var/www/slam"
LOG_DATE=$(date +"%Y%m%d_%H%M%S")
ANALYSIS_LOG="/var/log/slam/analysis_$LOG_DATE.log"

{
    echo "Iniciando análisis a $(date)"
    cd "$INSTALL_DIR"
    python3 main.py "$LOG_FILE" -o "$OUTPUT_DIR/reporte_$LOG_DATE"
    echo "Análisis completado a $(date)"
} >> "$ANALYSIS_LOG" 2>&1
EOF
    (chmod +x "$BIN_DIR/slam") & spinner
    echo -e " ${GREEN}✓${NC}"
    
    echo -ne "${YELLOW}  Creando slam-gui...${NC}"
    cat > "$BIN_DIR/slam-gui" << 'EOF'
#!/bin/bash
cd /etc/slam
python3 gui.py
EOF
    (chmod +x "$BIN_DIR/slam-gui") & spinner
    echo -e " ${GREEN}✓${NC}"
}

setup_cron() {
    echo -e "${BLUE}■ Configurando cron job...${NC}"
    if ! grep -q "slam" /etc/crontab; then
        echo -ne "${YELLOW}  Añadiendo tarea programada...${NC}"
        (echo "$CRON_JOB" >> /etc/crontab) & spinner
        echo -e " ${GREEN}✓${NC}"
        echo -e "${CYAN}  » Tarea programada cada hora${NC}"
    else
        echo -e "${YELLOW}  ✓ Cron job ya existe${NC}"
    fi
}

setup_logrotate() {
    echo -ne "${BLUE}■ Configurando logrotate...${NC}"
    cat > /etc/logrotate.d/slam << 'EOF'
/var/log/slam/*.log {
    weekly
    missingok
    rotate 4
    compress
    delaycompress
    notifempty
    create 640 root root
}
EOF
    echo -e " ${GREEN}✓${NC}"
}

show_finish() {
    echo
    echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}           INSTALACIÓN COMPLETADA CON ÉXITO${NC}"
    echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN} ${YELLOW}♦ Directorios creados:${NC}                     "
    echo -e "${CYAN} ${WHITE}  • Configuración: ${GREEN}$INSTALL_DIR${NC}     "
    echo -e "${CYAN} ${WHITE}  • Logs: ${GREEN}$LOG_DIR${NC}                  "
    echo -e "${CYAN} ${WHITE}  • Reportes: ${GREEN}$REPORTS_DIR${NC}          "
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN} ${YELLOW}♦ Comandos disponibles:${NC}                    "
    echo -e "${CYAN} ${WHITE}  • ${GREEN}slam${NC} - Ejecuta análisis manual  "
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN} ${YELLOW}♦ Configuración automática:${NC}                "
    echo -e "${CYAN} ${WHITE}  Se ejecutará ${GREEN}cada hora${NC}            "
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo
    if [ "$SQUID_INSTALLED" = false ]; then
        echo -e "${YELLOW}════════════════════ ATENCIÓN ═══════════════════════${NC}"
        echo -e "${RED}  Squid no está instalado o no se pudo verificar${NC}"
        echo -e "${YELLOW}  Para que SLAM funcione completamente, necesitas:${NC}"
        echo -e "${WHITE}  1. Instalar Squid Proxy Server${NC}"
        echo -e "${WHITE}  2. Configurar el formato de log como se mostró${NC}"
        echo -e "${YELLOW}═════════════════════════════════════════════════════${NC}"
        echo
    fi
    echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}            Gracias por usar SLAM - By Maxwell${NC}"
    echo -e "${MAGENTA}════════════════════════════════════════════════════════════${NC}"
    echo
}

clear
show_credits
check_root
check_bc
check_squid

echo -e "${BLUE}■ Iniciando proceso de instalación...${NC}"
progress_bar 1.5

install_packages
create_dirs
copy_files
setup_cron
setup_logrotate

configure_squid

echo -e "${GREEN}■ Proceso de instalación completado${NC}"
progress_bar 1

show_finish

exit 0