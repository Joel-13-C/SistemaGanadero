# Guía de Despliegue en Hostinger

## 1. Preparación del Sistema

### 1.1 Plan Recomendado
- **Plan**: Premium Windows Hosting
- **Características necesarias**:
  - Soporte Python 3.x
  - MySQL Database
  - SSL gratuito
  - Dominio gratuito (primer año)

### 1.2 Preparación Local
1. Ejecutar el script de preparación:
   ```bash
   python preparar_para_hostinger.py
   ```
   Este script:
   - Deshabilita el modo debug
   - Actualiza las credenciales de la base de datos
   - Crea el archivo web.config
   - Añade wfastcgi a requirements.txt

2. Verificar que requirements.txt incluya:
   ```
   flask==2.1.0
   flask-mysqldb==1.0.1
   python-dotenv==0.20.0
   werkzeug==2.1.1
   wfastcgi==3.0.0
   ```

## 2. Proceso de Despliegue

### 2.1 Compra y Configuración Inicial
1. Ir a [Hostinger](https://www.hostinger.es)
2. Seleccionar "Premium Windows Hosting"
3. Elegir un dominio gratuito o usar uno existente
4. Completar la compra

### 2.2 Configuración del Hosting
1. Acceder al panel de control de Hostinger
2. Ir a "Hosting" → Tu dominio → "Administrar"
3. En "Bases de datos":
   - Crear nueva base de datos MySQL
   - Anotar: nombre_bd, usuario, contraseña, host

### 2.3 Subida de Archivos
1. Acceder a File Manager o usar FTP
2. Subir todos los archivos del proyecto
3. Verificar que web.config esté en la raíz

### 2.4 Configuración de la Base de Datos
1. Acceder a phpMyAdmin
2. Importar el archivo SQL de la base de datos
3. Actualizar .env con las nuevas credenciales:
   ```
   MYSQL_HOST=tu_host
   MYSQL_USER=tu_usuario
   MYSQL_PASSWORD=tu_contraseña
   MYSQL_DB=tu_base_de_datos
   ```

### 2.5 Configuración de Python
1. En el panel de control:
   - Ir a "Python"
   - Seleccionar Python 3.13.1
   - Activar wfastcgi

### 2.6 Configuración del Dominio
1. En "Dominios":
   - Configurar los registros DNS
   - Activar SSL gratuito
   - Esperar propagación (24-48 horas)

## 3. Verificación

### 3.1 Pruebas Post-Despliegue
1. Acceder al sitio web mediante el dominio
2. Verificar:
   - Inicio de sesión
   - Conexión con la base de datos
   - Todas las funcionalidades del sistema

### 3.2 Solución de Problemas Comunes
1. Error 500:
   - Verificar web.config
   - Revisar logs de error
2. Error de conexión a BD:
   - Verificar credenciales en .env
   - Confirmar IP permitida
3. Errores de Python:
   - Verificar versión de Python
   - Revisar requirements.txt

## 4. Mantenimiento

### 4.1 Copias de Seguridad
1. Configurar copias automáticas:
   - Base de datos: Diaria
   - Archivos: Semanal

### 4.2 Actualizaciones
1. Mantener actualizado:
   - Certificado SSL
   - Dependencias de Python
   - Sistema operativo del servidor

## 5. Soporte

### 5.1 Contacto Hostinger
- Soporte 24/7 en español
- Chat en vivo
- Base de conocimientos

### 5.2 Recursos Adicionales
- [Documentación de Hostinger](https://www.hostinger.es/tutoriales)
- [Guía de Python en Hostinger](https://www.hostinger.es/tutoriales/python-hosting)
