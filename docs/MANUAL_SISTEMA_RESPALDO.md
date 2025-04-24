# Manual del Sistema de Respaldo - Sistema Ganadero

## Introducción

Este manual explica en detalle el sistema de respaldo de la base de datos implementado para el Sistema Ganadero. El sistema permite realizar copias de seguridad automáticas y programadas de la base de datos, así como su restauración en caso de ser necesario.

## Índice

1. [Componentes del sistema](#componentes-del-sistema)
2. [Configuración inicial](#configuración-inicial)
3. [Respaldo manual](#respaldo-manual)
4. [Respaldo automático](#respaldo-automático)
5. [Almacenamiento externo](#almacenamiento-externo)
6. [Restauración de respaldos](#restauración-de-respaldos)
7. [Pruebas de restauración](#pruebas-de-restauración)
8. [Solución de problemas](#solución-de-problemas)

## Componentes del sistema

El sistema de respaldo está compuesto por los siguientes archivos:

- **respaldo_bd.py**: Script principal que realiza el respaldo de la base de datos
- **ejecutar_respaldo.bat**: Archivo batch para ejecutar el respaldo fácilmente en Windows
- **restaurar_respaldo.py**: Script para restaurar un respaldo previamente generado
- **copiar_respaldos_externos.py**: Script para copiar respaldos a ubicaciones externas

## Configuración inicial

### Requisitos previos

- Python 3.6 o superior
- MySQL Server
- Dependencias de Python:
  - mysql-connector-python
  - python-dotenv

### Instalación de dependencias

Asegúrese de tener instaladas todas las dependencias necesarias:

```bash
pip install -r requirements.txt
```

### Configuración de credenciales

El sistema de respaldo utiliza las siguientes credenciales para conectarse a la base de datos:

```
Host: localhost
Usuario: root
Contraseña: 1234
Base de datos: sistema_ganadero
```

Estas credenciales pueden configurarse mediante variables de entorno o en un archivo `.env` en la raíz del proyecto:

```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=sistema_ganadero
```

## Respaldo manual

### Ejecutar respaldo desde la línea de comandos

Para realizar un respaldo manual, ejecute el siguiente comando desde la raíz del proyecto:

```bash
python respaldo_bd.py
```

### Ejecutar respaldo con doble clic

También puede ejecutar el archivo batch `ejecutar_respaldo.bat` haciendo doble clic sobre él en el explorador de Windows.

### Ubicación de los respaldos

Los respaldos se almacenan en la carpeta `respaldos/` dentro del directorio del proyecto. Cada respaldo tiene el siguiente formato de nombre:

```
respaldo_sistema_ganadero_AAAAMMDD_HHMMSS.sql.zip
```

Donde:
- `AAAAMMDD`: Año, mes y día
- `HHMMSS`: Hora, minutos y segundos

### Verificación del respaldo

Después de ejecutar un respaldo, verifique:

1. Que se haya creado el archivo en la carpeta `respaldos/`
2. Que el archivo tenga un tamaño razonable (no esté vacío)
3. Que el registro en `logs/respaldo_bd.log` indique que el proceso finalizó exitosamente

## Respaldo automático

### Configuración de tarea programada en Windows

Para configurar un respaldo automático diario:

1. Abra el Programador de tareas de Windows (taskschd.msc)
2. Cree una nueva tarea básica:
   - Nombre: "Respaldo Sistema Ganadero"
   - Frecuencia: Diaria
   - Hora: 2:00 AM (recomendado)
   - Acción: Iniciar un programa
   - Programa: Ruta completa al archivo `ejecutar_respaldo.bat`
   - Iniciar en: Ruta al directorio del proyecto

3. Configuraciones adicionales:
   - En la pestaña "General", marque "Ejecutar con privilegios más altos"
   - En la pestaña "Condiciones", desmarque "Iniciar la tarea solo si el equipo está conectado a la CA"

Para instrucciones más detalladas, consulte el archivo `CONFIGURAR_TAREA_PROGRAMADA.md`.

### Rotación de respaldos

El sistema mantiene automáticamente un número limitado de respaldos (configurado por defecto en 10) para evitar que ocupen demasiado espacio en disco. Los respaldos más antiguos se eliminan automáticamente cuando se supera este límite.

Para modificar el número de respaldos a mantener, edite la variable `MAX_BACKUPS` en el archivo `respaldo_bd.py`:

```python
# Número máximo de respaldos a mantener
MAX_BACKUPS = 10
```

## Almacenamiento externo

### Configuración de almacenamiento externo

Para mayor seguridad, se recomienda copiar los respaldos a una ubicación externa (disco USB, carpeta de red, etc.). El script `copiar_respaldos_externos.py` facilita esta tarea:

```bash
python copiar_respaldos_externos.py --destino E:\Respaldos_SistemaGanadero
```

Donde `E:\Respaldos_SistemaGanadero` es la ruta de destino donde se copiarán los respaldos.

### Opciones disponibles

- `--origen`: Carpeta de origen con los respaldos (por defecto: `respaldos/`)
- `--destino`: Carpeta de destino para las copias (obligatorio)
- `--max-copias`: Número máximo de copias a mantener (por defecto: 10)

### Automatización de copias externas

Para automatizar también la copia a almacenamiento externo, modifique el archivo `ejecutar_respaldo.bat`:

```batch
@echo off
echo Iniciando respaldo de base de datos...
python respaldo_bd.py
echo Copiando respaldos a almacenamiento externo...
python copiar_respaldos_externos.py --destino E:\Respaldos_SistemaGanadero
echo Proceso completo.
pause
```

## Restauración de respaldos

### Restaurar un respaldo

Para restaurar un respaldo, utilice el script `restaurar_respaldo.py`:

```bash
python restaurar_respaldo.py respaldos/respaldo_sistema_ganadero_20250417_130645.sql.zip --bd sistema_ganadero_test --crear-bd
```

Este comando:
- Restaura el respaldo especificado
- En la base de datos `sistema_ganadero_test`
- Crea la base de datos si no existe

### Opciones disponibles

- `archivo`: Ruta al archivo de respaldo (.sql o .zip)
- `--bd`: Nombre de la base de datos destino (por defecto: `sistema_ganadero_test`)
- `--crear-bd`: Crear la base de datos si no existe
- `--host`: Host de MySQL (por defecto: `localhost`)
- `--usuario`: Usuario de MySQL (por defecto: `root`)
- `--password`: Contraseña de MySQL (por defecto: `1234`)
- `--puerto`: Puerto de MySQL (por defecto: `3306`)

### Restauración en producción

**¡PRECAUCIÓN!** La restauración en la base de datos de producción sobrescribirá todos los datos existentes. Antes de restaurar en producción:

1. Realice una prueba de restauración en una base de datos de prueba
2. Verifique que el respaldo contiene todos los datos necesarios
3. Notifique a los usuarios que el sistema estará temporalmente fuera de servicio
4. Realice un respaldo adicional de la base de datos actual antes de restaurar

## Pruebas de restauración

### Importancia de las pruebas

Es fundamental realizar pruebas periódicas de restauración para:
- Verificar que los respaldos son utilizables
- Familiarizarse con el proceso de restauración
- Detectar posibles problemas antes de una emergencia real

### Procedimiento de prueba recomendado

1. Crear una base de datos de prueba:
   ```bash
   python restaurar_respaldo.py respaldos/respaldo_reciente.sql.zip --bd sistema_ganadero_test --crear-bd
   ```

2. Verificar las tablas y datos:
   ```bash
   mysql -u root -p1234 -e "USE sistema_ganadero_test; SHOW TABLES;"
   mysql -u root -p1234 -e "USE sistema_ganadero_test; SELECT COUNT(*) FROM animales;"
   ```

3. Documentar los resultados de la prueba

### Frecuencia recomendada

Se recomienda realizar pruebas de restauración:
- Mensualmente
- Después de cambios importantes en la estructura de la base de datos
- Antes de actualizaciones del sistema

## Solución de problemas

### Error: "Access denied for user"

**Problema**: Error de acceso a la base de datos.

**Solución**:
- Verifique las credenciales en el archivo `.env` o en las variables de entorno
- Confirme que el usuario tiene permisos suficientes en MySQL
- Intente conectarse manualmente a MySQL para verificar las credenciales

### Error: "No se pudo crear el archivo de respaldo"

**Problema**: No se puede escribir en el directorio de respaldos.

**Solución**:
- Verifique que el usuario tiene permisos de escritura en la carpeta `respaldos/`
- Asegúrese de que hay suficiente espacio en disco
- Compruebe que no hay bloqueos por parte de antivirus u otras aplicaciones

### Error: "No se pudo comprimir el archivo"

**Problema**: Error al crear el archivo ZIP.

**Solución**:
- Verifique que la biblioteca `zipfile` está disponible
- Asegúrese de que el archivo SQL se creó correctamente
- Compruebe los permisos de escritura

### Error: "No se pudo conectar a la base de datos"

**Problema**: No se puede establecer conexión con MySQL.

**Solución**:
- Verifique que el servidor MySQL está en ejecución
- Compruebe la configuración de host y puerto
- Asegúrese de que no hay reglas de firewall bloqueando la conexión

### Registros de error

Para investigar problemas, revise los archivos de registro:
- `logs/respaldo_bd.log`: Logs del sistema de respaldo
- `logs/restauracion.log`: Logs del sistema de restauración
- `logs/copias_externas.log`: Logs de copias a almacenamiento externo

---

Para asistencia técnica adicional, contacte al equipo de soporte:
- Correo: soporte@sistemaganadero.com
- Teléfono: (123) 456-7890
