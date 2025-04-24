import os
import shutil
import configparser

def crear_web_config():
    """Crea el archivo web.config necesario para IIS"""
    web_config = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <handlers>
            <add name="PythonHandler" path="*" verb="*" modules="FastCgiModule" 
                 scriptProcessor="c:\\python313\\python.exe|c:\\python313\\lib\\site-packages\\wfastcgi.py" 
                 resourceType="Unspecified" requireAccess="Script" />
        </handlers>
        <fastCgi>
            <application fullPath="c:\\python313\\python.exe" 
                        arguments="c:\\python313\\lib\\site-packages\\wfastcgi.py"
                        maxInstances="4"
                        idleTimeout="300"
                        activityTimeout="30"
                        requestTimeout="90"
                        instanceMaxRequests="10000"
                        protocol="NamedPipe"
                        flushNamedPipe="false">
            </application>
        </fastCgi>
    </system.webServer>
    <appSettings>
        <add key="PYTHONPATH" value="C:\\home\\site\\wwwroot" />
        <add key="WSGI_HANDLER" value="app.app" />
        <add key="WSGI_LOG" value="C:\\home\\LogFiles\\wfastcgi.log" />
    </appSettings>
</configuration>"""
    
    with open('web.config', 'w') as f:
        f.write(web_config)
    print("[OK] Archivo web.config creado exitosamente")

def actualizar_requirements():
    """Actualiza requirements.txt con las dependencias necesarias"""
    requirements = """flask==2.1.0
flask-mysqldb==1.0.1
python-dotenv==0.20.0
werkzeug==2.1.1
wfastcgi==3.0.0
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

def main():
    print("\n=== Preparando el Sistema Ganadero para Hostinger ===\n")
    
    # Crear web.config
    crear_web_config()
    
    # Actualizar requirements.txt
    actualizar_requirements()
    
    # Deshabilitar modo debug
    deshabilitar_debug()
    
    # Crear .env.example
    crear_env_ejemplo()
    
    print("\n=== Sistema preparado exitosamente para Hostinger! ===")
    print("\nProximos pasos:")
    print("1. Sube los archivos a Hostinger")
    print("2. Configura las variables de entorno en el panel de control")
    print("3. Importa la base de datos en phpMyAdmin")
    print("4. Verifica la configuracion de Python")
    print("\nPara mas detalles, consulta GUIA_DESPLIEGUE_HOSTINGER.md")

if __name__ == "__main__":
    main()
