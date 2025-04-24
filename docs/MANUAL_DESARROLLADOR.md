# Manual del Desarrollador - Sistema Ganadero

## Introducción

Este manual está dirigido a desarrolladores que necesiten mantener, modificar o extender el Sistema Ganadero. Proporciona información técnica detallada sobre la arquitectura del sistema, estructura de código, base de datos y procedimientos de desarrollo.

## Índice

1. [Arquitectura del sistema](#arquitectura-del-sistema)
2. [Entorno de desarrollo](#entorno-de-desarrollo)
3. [Estructura del proyecto](#estructura-del-proyecto)
4. [Base de datos](#base-de-datos)
5. [Autenticación y seguridad](#autenticación-y-seguridad)
6. [API y endpoints](#api-y-endpoints)
7. [Sistema de notificaciones](#sistema-de-notificaciones)
8. [Respaldo y restauración](#respaldo-y-restauración)
9. [Pruebas](#pruebas)
10. [Despliegue](#despliegue)
11. [Mantenimiento](#mantenimiento)
12. [Guía de contribución](#guía-de-contribución)

## Arquitectura del sistema

El Sistema Ganadero está desarrollado utilizando las siguientes tecnologías:

- **Backend**: Python con Flask como framework web
- **Base de datos**: MySQL
- **Frontend**: HTML, CSS, JavaScript con Bootstrap
- **Autenticación**: Sistema propio basado en sesiones
- **Programación de tareas**: APScheduler

La arquitectura sigue un patrón MVC (Modelo-Vista-Controlador):
- **Modelos**: Representaciones de las tablas de la base de datos y lógica de negocio
- **Vistas**: Plantillas HTML con Jinja2
- **Controladores**: Rutas y lógica de Flask

## Entorno de desarrollo

### Requisitos previos

- Python 3.6 o superior
- MySQL 5.7 o superior
- Git (para control de versiones)
- Editor de código (recomendado: Visual Studio Code)

### Configuración del entorno

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/usuario/sistema-ganadero.git
   cd sistema-ganadero
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   # En Windows
   venv\Scripts\activate
   # En Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**:
   Cree un archivo `.env` en la raíz del proyecto con el siguiente contenido:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=1234
   MYSQL_DB=sistema_ganadero
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=clave_secreta_para_desarrollo
   ```

5. **Inicializar la base de datos**:
   ```bash
   mysql -u root -p
   # Ingrese su contraseña
   CREATE DATABASE sistema_ganadero CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   exit
   
   # Ejecutar script de inicialización
   python inicializar_bd.py
   ```

6. **Ejecutar la aplicación**:
   ```bash
   flask run
   ```

## Estructura del proyecto

```
sistema_ganadero/
│
├── app.py                  # Punto de entrada principal
├── config.py               # Configuración de la aplicación
├── requirements.txt        # Dependencias
├── inicializar_bd.py       # Script para inicializar la base de datos
├── respaldo_bd.py          # Script para respaldo de base de datos
├── restaurar_respaldo.py   # Script para restaurar respaldos
│
├── src/                    # Código fuente principal
│   ├── database.py         # Conexión a la base de datos
│   ├── models/             # Modelos de datos
│   ├── routes/             # Rutas y controladores
│   ├── services/           # Servicios y lógica de negocio
│   ├── utils/              # Utilidades y funciones auxiliares
│   └── alarmas.py          # Sistema de alarmas y notificaciones
│
├── static/                 # Archivos estáticos
│   ├── css/                # Hojas de estilo
│   ├── js/                 # JavaScript
│   └── img/                # Imágenes
│
├── templates/              # Plantillas HTML
│   ├── layout.html         # Plantilla base
│   ├── auth/               # Plantillas de autenticación
│   ├── animales/           # Plantillas de gestión de animales
│   └── ...                 # Otras secciones
│
├── logs/                   # Archivos de registro
├── respaldos/              # Respaldos de la base de datos
└── docs/                   # Documentación
```

## Base de datos

### Esquema de la base de datos

El sistema utiliza MySQL como gestor de base de datos. El esquema incluye las siguientes tablas principales:

- `usuarios`: Información de usuarios del sistema
- `animales`: Registro de todos los animales
- `categorias_animales`: Categorías de animales
- `eventos_salud`: Registro de eventos de salud
- `vacuna`: Tipos de vacunas disponibles
- `vacuna_animal`: Registro de vacunaciones
- `desparasitacion`: Registro de desparasitaciones
- `vitaminizacion`: Registro de vitaminizaciones
- `gestacion`: Registro de gestaciones
- `reproduccion`: Eventos reproductivos
- `ingresos`: Registro de ingresos financieros
- `gastos`: Registro de gastos
- `inventario`: Inventario de insumos
- `pastizales`: Registro de pastizales
- `alarmas_enviadas`: Registro de notificaciones enviadas

### Diagrama Entidad-Relación

Para ver el diagrama completo, consulte el archivo `docs/diagrama_er.png`.

### Acceso a la base de datos

La conexión a la base de datos se gestiona en el archivo `src/database.py`. Utiliza el patrón Singleton para mantener una única conexión activa:

```python
def get_db_connection():
    """
    Obtiene una conexión a la base de datos.
    Utiliza las credenciales configuradas en variables de entorno.
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "1234"),
            database=os.getenv("MYSQL_DB", "sistema_ganadero")
        )
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Error al conectar a la base de datos: {err}")
        raise
```

## Autenticación y seguridad

### Sistema de autenticación

El sistema utiliza autenticación basada en sesiones con Flask. Las contraseñas se almacenan utilizando SHA-256 (se recomienda migrar a bcrypt o Argon2).

Proceso de autenticación:
1. El usuario ingresa credenciales
2. Se verifica contra la base de datos
3. Se crea una sesión si las credenciales son válidas
4. Se utiliza `@login_required` para proteger rutas

### Mejoras de seguridad recomendadas

- Migrar el sistema de hashing de contraseñas a bcrypt o Argon2
- Implementar HTTPS
- Agregar protección contra CSRF
- Implementar límites de intentos de inicio de sesión
- Mejorar la validación de entradas para prevenir inyección SQL

## API y endpoints

### Rutas principales

- `/`: Página principal y dashboard
- `/login`: Inicio de sesión
- `/logout`: Cierre de sesión
- `/animales`: Gestión de animales
- `/sanidad`: Control sanitario
- `/reproduccion`: Gestión reproductiva
- `/finanzas`: Gestión financiera
- `/informes`: Generación de informes
- `/configuracion`: Configuración del sistema

### Estructura de controladores

Cada módulo tiene su propio archivo de rutas en `src/routes/`. Por ejemplo, para animales:

```python
@app.route('/animales', methods=['GET'])
@login_required
def listar_animales():
    """Muestra la lista de animales registrados"""
    # Lógica para obtener y mostrar animales
    
@app.route('/animales/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_animal():
    """Formulario para registrar un nuevo animal"""
    # Lógica para crear un nuevo animal
```

## Sistema de notificaciones

El sistema de notificaciones está implementado en `src/alarmas.py`. Utiliza APScheduler para ejecutar verificaciones periódicas y enviar alertas por correo electrónico.

### Tipos de alarmas

- Vacunaciones pendientes
- Desparasitaciones pendientes
- Partos próximos
- Eventos sanitarios programados

### Configuración de correo

El envío de correos se configura en `src/utils/email_sender.py`. Utiliza SMTP para enviar notificaciones:

```python
def enviar_correo(destinatario, asunto, contenido):
    """
    Envía un correo electrónico utilizando la configuración SMTP.
    """
    try:
        # Obtener configuración de correo
        config = obtener_config_email()
        
        # Crear mensaje
        mensaje = MIMEMultipart()
        mensaje['From'] = config['email']
        mensaje['To'] = destinatario
        mensaje['Subject'] = asunto
        mensaje.attach(MIMEText(contenido, 'html'))
        
        # Enviar correo
        servidor = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        servidor.starttls()
        servidor.login(config['email'], config['password'])
        servidor.send_message(mensaje)
        servidor.quit()
        
        return True
    except Exception as e:
        logging.error(f"Error al enviar correo: {str(e)}")
        return False
```

## Respaldo y restauración

### Sistema de respaldo

El sistema de respaldo está implementado en `respaldo_bd.py`. Características principales:

- Respaldo completo de la estructura y datos de la base de datos
- Compresión de archivos para optimizar espacio
- Rotación automática de respaldos antiguos
- Registro detallado de operaciones

### Proceso de respaldo

```python
def realizar_respaldo(nombre_archivo):
    """
    Realiza el respaldo de la base de datos usando Python y MySQL Connector.
    Esta función no depende de mysqldump, lo que la hace más portable.
    """
    # Implementación detallada en respaldo_bd.py
```

### Restauración de respaldos

El proceso de restauración está implementado en `restaurar_respaldo.py`:

```python
def restaurar_base_datos(archivo_sql, nombre_bd, crear_bd=False):
    """
    Restaura un archivo SQL en la base de datos.
    """
    # Implementación detallada en restaurar_respaldo.py
```

## Pruebas

### Estructura de pruebas

Las pruebas unitarias y de integración se encuentran en el directorio `tests/`:

```
tests/
├── test_auth.py       # Pruebas de autenticación
├── test_animales.py   # Pruebas del módulo de animales
├── test_sanidad.py    # Pruebas del módulo de sanidad
└── ...
```

### Ejecución de pruebas

Para ejecutar todas las pruebas:

```bash
python -m pytest
```

Para ejecutar pruebas específicas:

```bash
python -m pytest tests/test_auth.py
```

## Despliegue

### Preparación para producción

1. Actualizar `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```

2. Configurar variables de entorno para producción:
   - Deshabilitar modo debug
   - Configurar SECRET_KEY seguro
   - Configurar credenciales de base de datos

3. Configurar servidor WSGI (Gunicorn recomendado):
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

### Opciones de despliegue

- **Servidor dedicado**: Configuración con Nginx + Gunicorn
- **Contenedores**: Dockerfile disponible para despliegue con Docker
- **Servicios en la nube**: Instrucciones para AWS, Azure o Google Cloud

## Mantenimiento

### Tareas periódicas

- Respaldo de base de datos (configurado como tarea programada)
- Verificación de integridad de datos
- Actualización de dependencias
- Monitoreo de logs

### Gestión de logs

Los logs del sistema se almacenan en el directorio `logs/`. Se recomienda revisar periódicamente:

- `app.log`: Logs generales de la aplicación
- `respaldo_bd.log`: Logs del sistema de respaldo
- `alarmas.log`: Logs del sistema de notificaciones

## Guía de contribución

### Flujo de trabajo Git

1. Crear una rama para la nueva característica:
   ```bash
   git checkout -b feature/nueva-caracteristica
   ```

2. Realizar cambios y commits:
   ```bash
   git add .
   git commit -m "Descripción detallada del cambio"
   ```

3. Enviar cambios al repositorio:
   ```bash
   git push origin feature/nueva-caracteristica
   ```

4. Crear Pull Request para revisión

### Estándares de código

- Seguir PEP 8 para código Python
- Documentar todas las funciones con docstrings
- Mantener una cobertura de pruebas adecuada
- Utilizar nombres descriptivos para variables y funciones

---

Para consultas técnicas adicionales, contacte al equipo de desarrollo:
- Correo: desarrollo@sistemaganadero.com
- Repositorio: https://github.com/usuario/sistema-ganadero
