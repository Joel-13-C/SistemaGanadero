# Guía de Despliegue en Hostinger Linux

## 1. Preparación del Sistema

### 1.1 Ejecutar Script de Preparación
```bash
python preparar_para_linux.py
```
Este script preparará todos los archivos necesarios para el despliegue en Linux.

## 2. Configuración en Hostinger

### 2.1 Acceder al Panel de Control
1. Inicia sesión en Hostinger
2. Ve a "Sitios web"
3. Selecciona tu dominio

### 2.2 Configurar Python
1. En el panel lateral, busca "Configuración de Software" o "Python"
2. Selecciona Python 3.13.1 como versión
3. Guarda los cambios

### 2.3 Crear Base de Datos MySQL
1. En el panel lateral, busca "Bases de datos MySQL"
2. Haz clic en "Nueva Base de Datos"
3. Completa la información:
   - Nombre de la base de datos
   - Usuario
   - Contraseña
4. Guarda las credenciales de manera segura

### 2.4 Subir Archivos
1. Ve a "Administrador de archivos" o "File Manager"
2. Navega a la carpeta `public_html`
3. Sube todos los archivos del proyecto
4. Asegúrate de que wsgi.py tenga permisos 755

### 2.5 Configurar Variables de Entorno
1. Crea/edita el archivo .env con las credenciales de la base de datos:
   ```
   MYSQL_HOST=tu_host_mysql
   MYSQL_USER=tu_usuario
   MYSQL_PASSWORD=tu_contraseña
   MYSQL_DB=sistema_ganadero
   ```

### 2.6 Importar Base de Datos
1. Ve a phpMyAdmin
2. Selecciona tu base de datos
3. Importa el archivo database_hostinger.sql

## 3. Configuración del Dominio

### 3.1 DNS y SSL
1. En "Dominios", configura los registros DNS
2. Activa el SSL gratuito
3. Espera la propagación (puede tomar hasta 24 horas)

### 3.2 Verificar Configuración
1. Asegúrate de que el dominio apunte a tu hosting
2. Verifica que el certificado SSL esté activo

## 4. Verificación Final

### 4.1 Pruebas del Sistema
1. Accede a tu sitio web usando el dominio
2. Intenta iniciar sesión
3. Verifica todas las funcionalidades:
   - Registro de animales
   - Gestión de vacunas
   - Control de gestaciones
   - Reportes PDF
   - etc.

### 4.2 Solución de Problemas Comunes

#### Error 500
1. Verifica los permisos de los archivos
2. Revisa los logs de error
3. Confirma que las dependencias estén instaladas

#### Error de Base de Datos
1. Verifica las credenciales en .env
2. Confirma que la base de datos esté importada
3. Prueba la conexión desde phpMyAdmin

#### Problemas de Sesión
1. Verifica la configuración de PHP
2. Asegúrate de que las cookies funcionen
3. Limpia la caché del navegador

## 5. Mantenimiento

### 5.1 Copias de Seguridad
1. Configura copias de seguridad automáticas:
   - Base de datos: Diaria
   - Archivos: Semanal
2. Verifica regularmente las copias de seguridad

### 5.2 Actualizaciones
1. Mantén actualizado:
   - Python y sus dependencias
   - Sistema operativo
   - Certificados SSL

## 6. Soporte

### 6.1 Recursos de Ayuda
- Soporte de Hostinger 24/7
- Documentación oficial de Flask
- Guías de Python en Hostinger

### 6.2 Contactos Importantes
- Soporte Hostinger: support@hostinger.com
- Panel de control: hpanel.hostinger.com
