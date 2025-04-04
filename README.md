# 🦑 Squid Log Analyzer (SLAM) 📊  
### *Una solución moderna e inteligente para el análisis de los registros de Squid Proxy*  

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&style=for-the-badge" alt="Python">
  <img src="https://img.shields.io/github/last-commit/MaxCode93/squid-log-analyzer?style=for-the-badge" alt="Último Commit">
  <img src="https://img.shields.io/github/repo-size/MaxCode93/squid-log-analyzer?style=for-the-badge" alt="Tamaño">
</p>

---

## ✨ Características

- **Análisis Detallado**: Examina tus registros de acceso con estadísticas profundas.
- **Visualizaciones**: Grafica datos clave para una interpretación rápida.
- **Filtro Personalizado**: Filtra la información según tus necesidades.
- **Interfaz Intuitiva**: Diseñada para facilitar su uso.

---

## 📥 Instalación

### Prerequisitos

Asegúrate de tener instalado:

- [Python 3.8+](https://www.python.org/downloads/)
- [pip](https://pip.pypa.io/en/stable/)

### Pasos para instalar

1. Clona el repositorio:

   ```bash
   git clone https://github.com/MaxCode93/squid-log-analyzer.git
   cd squid-log-analyzer
   ```

2. Ejecuta el script de instalación:

   ```bash
   bash setup.sh
   ```

3. Directorio básico de salida de los logs generados:

   ```bash
   /var/www/slam/
   ```
   
3. ¡Listo para usar!

---

## 🚀 Uso básico 

Para analizar manualmente el archivo de registro de Squid, utiliza el siguiente comando:

```bash
slam
```

El script se ejecuta automáticamente cada 1h, usted puede cambiar esto modificando: 

```bash
nano /etc/crontab
```

---

## 📝 Notas de uso

1. Uso con Apache(crear un vhost)
   
   ```bash
   <VirtualHost *:80>
    ServerName slam.yourdomain.com
    DocumentRoot /var/www/slam
    ErrorLog ${APACHE_LOG_DIR}/slam_error.log
    CustomLog ${APACHE_LOG_DIR}/slam_access.log combined

    <Directory /var/www/slam>
        Options Indexes FollowSymLinks
        AllowOverride None
        Require all granted
        
        <FilesMatch "\.(log|txt)$">
            Require ip 192.168.1.0/24  # Solo permite IPs locales
        </FilesMatch>
    </Directory>

    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains"
   </VirtualHost>
   ```

2. Uso con Nginx(crear un vhost)

   ```bash
   server {
    listen 80;
    server_name slam.yourdomain.com;
    root /var/www/slam;
    index index.html;

    access_log /var/log/nginx/slam_access.log;
    error_log /var/log/nginx/slam_error.log;

    location / {
        try_files $uri $uri/ =404;
        autoindex on;
        
        allow 192.168.1.0/24;
        deny all;
    }

    location ~ \.log$ {
        return 403;
    }
   }
   ```

---

## 🛠️ Contribuciones

¡Las contribuciones son bienvenidas! Si quieres ayudar a mejorar **SLAM**, sigue estos pasos:

1. Haz un fork del proyecto.
2. Crea tu característica o corregir un error (`git checkout -b feature/nueva-caracteristica`).
3. Realiza tus cambios y haz un commit (`git commit -m 'Agregando nueva característica'`).
4. Envía un pull request.

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.

---

## 📫 Contacto

Si tienes alguna duda o sugerencia, no dudes en contactarme:

- **Maxwell** - [GitHub](https://github.com/MaxCode93)
- Correo: [carlosmaxwell93@gmail.com](mailto:carlosmaxwell93@gmail.com)

---

¡Gracias por visitar el proyecto **🦑 Squid Log Analyzer (SLAM)**! Espero que encuentres esta herramienta útil y fácil de usar. 😊
