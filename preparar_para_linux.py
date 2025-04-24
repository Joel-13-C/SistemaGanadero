import os
import configparser

def crear_wsgi():
    """Crea el archivo wsgi.py necesario para el despliegue"""
    wsgi_content = """from app import app

if __name__ == "__main__":
    app.run()"""
    
    with open('wsgi.py', 'w') as f:
        f.write(wsgi_content)
    print("[OK] Archivo wsgi.py creado exitosamente")

def actualizar_requirements():
    """Actualiza requirements.txt con las dependencias necesarias"""
    requirements = """flask==2.1.0
flask-mysqldb==1.0.1
python-dotenv==0.20.0
werkzeug==2.1.1
apscheduler==3.9.1
reportlab==4.2.5
gunicorn==20.1.0"""

    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("[OK] Archivo requirements.txt actualizado")

def deshabilitar_debug():
    """Deshabilita el modo debug en app.py"""
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Reemplazar debug=True por debug=False
        content = content.replace('debug=True', 'debug=False')
        
        with open('app.py', 'w') as f:
            f.write(content)
        print("[OK] Modo debug deshabilitado en app.py")
    except Exception as e:
        print(f"[ERROR] Error al modificar app.py: {str(e)}")

def crear_env_ejemplo():
    """Crea un archivo .env.example con la estructura necesaria"""
    env_content = """MYSQL_HOST=tu_host_mysql
MYSQL_USER=tu_usuario
MYSQL_PASSWORD=tu_contraseña
MYSQL_DB=sistema_ganadero"""

    with open('.env.example', 'w') as f:
        f.write(env_content)
    print("[OK] Archivo .env.example creado")

def crear_htaccess():
    """Crea el archivo .htaccess para la configuración de Apache"""
    htaccess_content = """<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^(.*)$ wsgi.py/$1 [QSA,L]
</IfModule>

<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/gif "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
</IfModule>"""

    with open('.htaccess', 'w') as f:
        f.write(htaccess_content)
    print("[OK] Archivo .htaccess creado")

def main():
    print("\n=== Preparando el Sistema Ganadero para Linux Hosting ===\n")
    
    # Crear wsgi.py
    crear_wsgi()
    
    # Actualizar requirements.txt
    actualizar_requirements()
    
    # Deshabilitar modo debug
    deshabilitar_debug()
    
    # Crear .env.example
    crear_env_ejemplo()
    
    # Crear .htaccess
    crear_htaccess()
    
    print("\n=== Sistema preparado exitosamente para Linux Hosting! ===")
    print("\nProximos pasos:")
    print("1. Accede al panel de control de Hostinger")
    print("2. Ve a la sección 'Sitios web' y selecciona tu dominio")
    print("3. Busca 'Administrador de archivos' o 'File Manager'")
    print("4. Sube todos los archivos del proyecto")
    print("5. Configura la base de datos MySQL")
    print("6. Configura Python y las variables de entorno")
    print("\nPara mas detalles, consulta GUIA_DESPLIEGUE_LINUX.md")

if __name__ == "__main__":
    main()
