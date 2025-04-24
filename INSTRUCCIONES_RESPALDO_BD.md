# Instrucciones para el Sistema de Respaldo de Base de Datos

## Introducción

Este documento explica cómo utilizar y configurar el sistema de respaldo automático para la base de datos del Sistema Ganadero. Los respaldos regulares son esenciales para proteger los datos contra pérdidas accidentales, fallos del sistema o corrupción de datos.

## Archivos del Sistema de Respaldo

El sistema de respaldo consta de los siguientes archivos:

1. **respaldo_bd.py**: Script principal que realiza el respaldo de la base de datos.
2. **ejecutar_respaldo.bat**: Archivo batch para ejecutar el respaldo fácilmente en Windows.
3. **respaldos/** (directorio): Carpeta donde se almacenan los archivos de respaldo.
4. **respaldos_bd.log**: Archivo de registro que contiene información sobre los procesos de respaldo.

## Requisitos Previos

Para que el sistema de respaldo funcione correctamente, necesita:

- Python 3.6 o superior instalado
- MySQL instalado
- Herramienta `mysqldump` disponible en el PATH del sistema
- Módulo Python `python-dotenv` instalado (`pip install python-dotenv`)

## Configuración

### Opción 1: Usar Variables de Entorno

Puede configurar el sistema de respaldo creando un archivo `.env` en el directorio raíz del proyecto con el siguiente contenido:

```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=sistema_ganadero
MYSQL_PORT=3306
BACKUP_DIR=C:/ruta/a/respaldos
MAX_BACKUPS=10
```

### Opción 2: Modificar Directamente el Script

Alternativamente, puede editar las variables de configuración directamente en el archivo `respaldo_bd.py`:

```python
# Configuración predeterminada
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "1234"),
    "database": os.getenv("MYSQL_DB", "sistema_ganadero"),
    "port": os.getenv("MYSQL_PORT", "3306")
}

# Directorio para almacenar los respaldos
BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.join(os.getcwd(), "respaldos"))

# Número máximo de respaldos a mantener (para rotación)
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "10"))
```

## Uso Manual

### Ejecutar un Respaldo Manualmente

Para realizar un respaldo manualmente, puede:

1. **Usando el archivo batch**:
   - Haga doble clic en `ejecutar_respaldo.bat`
   - O ejecútelo desde la línea de comandos: `ejecutar_respaldo.bat`

2. **Usando directamente el script Python**:
   - Abra una terminal en el directorio del proyecto
   - Ejecute: `python respaldo_bd.py`

### Opciones Adicionales

El script `respaldo_bd.py` acepta los siguientes parámetros:

- `--no-compress`: No comprimir el archivo de respaldo (lo deja como .sql)
- `--no-rotate`: No eliminar respaldos antiguos

Ejemplo: `python respaldo_bd.py --no-compress`

## Programación de Respaldos Automáticos

### En Windows

1. Abra el Programador de tareas de Windows (Task Scheduler)
2. Seleccione "Crear tarea básica"
3. Asigne un nombre como "Respaldo Sistema Ganadero"
4. Seleccione la frecuencia deseada (diaria, semanal, etc.)
5. Configure la hora de ejecución
6. Seleccione "Iniciar un programa"
7. En "Programa/script", seleccione la ruta completa a `ejecutar_respaldo.bat`
8. En "Iniciar en", ingrese la ruta al directorio del proyecto
9. Complete el asistente

### En Linux/macOS (si se despliega en estos sistemas)

1. Abra una terminal
2. Ejecute `crontab -e` para editar el crontab
3. Agregue una línea como la siguiente para ejecutar el respaldo diariamente a las 2 AM:
   ```
   0 2 * * * cd /ruta/al/proyecto && python respaldo_bd.py >> respaldo_cron.log 2>&1
   ```

## Restauración de Respaldos

Para restaurar un respaldo en caso de emergencia:

1. Descomprima el archivo ZIP del respaldo (si está comprimido)
2. Abra una terminal y ejecute:
   ```
   mysql -u root -p sistema_ganadero < ruta/al/archivo/respaldo.sql
   ```
3. Ingrese la contraseña cuando se solicite

## Solución de Problemas

Si encuentra problemas con el sistema de respaldo:

1. **Verifique los permisos**: Asegúrese de que el usuario que ejecuta el script tenga permisos para:
   - Acceder a la base de datos
   - Escribir en el directorio de respaldos

2. **Revise el archivo de registro**: Consulte `respaldos_bd.log` para obtener información detallada sobre errores.

3. **Problemas comunes**:
   - **Error "Command not found"**: Asegúrese de que `mysqldump` esté instalado y en el PATH
   - **Error de acceso denegado**: Verifique las credenciales de la base de datos
   - **Error de espacio en disco**: Verifique que haya suficiente espacio disponible

## Recomendaciones

- Configure respaldos diarios, preferiblemente en horarios de baja actividad
- Periódicamente, copie los respaldos a una ubicación externa (disco externo, almacenamiento en la nube)
- Pruebe ocasionalmente la restauración de un respaldo para verificar que el proceso funciona correctamente
- Considere implementar respaldos incrementales si la base de datos crece significativamente

## Contacto

Si tiene problemas o preguntas sobre el sistema de respaldo, contacte al administrador del sistema.

---

Documento creado: Abril 2025
