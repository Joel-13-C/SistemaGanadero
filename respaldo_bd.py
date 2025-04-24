#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para realizar respaldos automáticos de la base de datos del Sistema Ganadero.
Este script puede ser ejecutado manualmente o programado para ejecución automática.

Autor: Sistema Ganadero
Fecha: Abril 2025
"""

import os
import sys
import datetime
import subprocess
import logging
import shutil
import time
import argparse
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("respaldos_bd.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("respaldo_bd")

# Cargar variables de entorno si existe un archivo .env
load_dotenv()

# Configuración predeterminada (se puede sobrescribir con variables de entorno)
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "1234"),  # Contraseña correcta según la memoria
    "database": os.getenv("MYSQL_DB", "sistema_ganadero"),
    "port": os.getenv("MYSQL_PORT", "3306")
}

# Directorio para almacenar los respaldos
BACKUP_DIR = os.getenv("BACKUP_DIR", os.path.join(os.getcwd(), "respaldos"))

# Número máximo de respaldos a mantener (para rotación)
MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", "10"))

def crear_directorio_respaldo():
    """Crea el directorio de respaldos si no existe."""
    if not os.path.exists(BACKUP_DIR):
        try:
            os.makedirs(BACKUP_DIR)
            logger.info(f"Directorio de respaldos creado: {BACKUP_DIR}")
        except Exception as e:
            logger.error(f"Error al crear directorio de respaldos: {e}")
            sys.exit(1)
    else:
        logger.info(f"Directorio de respaldos existente: {BACKUP_DIR}")

def generar_nombre_archivo():
    """Genera un nombre de archivo para el respaldo basado en la fecha y hora actual."""
    fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"respaldo_{DB_CONFIG['database']}_{fecha}.sql"

def realizar_respaldo(nombre_archivo):
    """
    Realiza el respaldo de la base de datos usando Python y MySQL Connector.
    Esta función no depende de mysqldump, lo que la hace más portable.
    
    Args:
        nombre_archivo: Nombre del archivo donde se guardará el respaldo
        
    Returns:
        bool: True si el respaldo fue exitoso, False en caso contrario
    """
    ruta_completa = os.path.join(BACKUP_DIR, nombre_archivo)
    
    try:
        import mysql.connector
        from mysql.connector import errorcode
        
        logger.info(f"Iniciando respaldo de la base de datos {DB_CONFIG['database']} usando MySQL Connector")
        
        # Conectar a la base de datos
        logger.info(f"Conectando a MySQL en {DB_CONFIG['host']}:{DB_CONFIG['port']} como {DB_CONFIG['user']}")
        
        # Usar directamente las credenciales correctas (de la memoria)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="sistema_ganadero"
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Abrir el archivo para escribir
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            # Escribir encabezado del archivo SQL
            f.write(f"-- Respaldo de la base de datos {DB_CONFIG['database']}\n")
            f.write(f"-- Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-- Sistema Ganadero\n\n")
            
            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            
            # Obtener lista de tablas
            logger.info("Obteniendo lista de tablas...")
            cursor.execute("SHOW TABLES")
            tablas = [list(tabla.values())[0] for tabla in cursor.fetchall()]
            logger.info(f"Tablas encontradas: {len(tablas)}")
            
            # Para cada tabla
            for tabla in tablas:
                logger.info(f"Procesando tabla: {tabla}")
                
                # Obtener estructura de la tabla
                cursor.execute(f"SHOW CREATE TABLE {tabla}")
                estructura = cursor.fetchone()["Create Table"]
                
                # Escribir estructura
                f.write(f"-- Estructura de la tabla `{tabla}`\n")
                f.write(f"DROP TABLE IF EXISTS `{tabla}`;\n")
                f.write(f"{estructura};\n\n")
                
                # Obtener datos
                cursor.execute(f"SELECT * FROM {tabla}")
                filas = cursor.fetchall()
                
                if filas:
                    f.write(f"-- Datos de la tabla `{tabla}`\n")
                    f.write(f"INSERT INTO `{tabla}` VALUES\n")
                    
                    # Procesar cada fila
                    valores_filas = []
                    for fila in filas:
                        valores = []
                        for valor in fila.values():
                            if valor is None:
                                valores.append("NULL")
                            elif isinstance(valor, (int, float)):
                                valores.append(str(valor))
                            elif isinstance(valor, datetime.datetime):
                                valores.append(f"'{valor.strftime('%Y-%m-%d %H:%M:%S')}'")
                            elif isinstance(valor, datetime.date):
                                valores.append(f"'{valor.strftime('%Y-%m-%d')}'")
                            else:
                                # Escapar comillas simples
                                valor_str = str(valor).replace("'", "\\'") 
                                valores.append(f"'{valor_str}'")
                        valores_filas.append(f"({', '.join(valores)})")
                    
                    # Escribir los valores
                    f.write(',\n'.join(valores_filas))
                    f.write(";\n\n")
            
            # Obtener procedimientos almacenados, funciones y triggers
            for objeto_tipo, comando in [
                ("PROCEDURE", "SHOW PROCEDURE STATUS"),
                ("FUNCTION", "SHOW FUNCTION STATUS"),
                ("TRIGGER", "SHOW TRIGGERS")
            ]:
                logger.info(f"Procesando {objeto_tipo}s...")
                cursor.execute(comando)
                objetos = cursor.fetchall()
                
                for obj in objetos:
                    if objeto_tipo in ["PROCEDURE", "FUNCTION"]:
                        nombre = obj["Name"]
                        if obj["Db"] == DB_CONFIG['database']:
                            cursor.execute(f"SHOW CREATE {objeto_tipo} {nombre}")
                            crear = cursor.fetchone()[f"Create {objeto_tipo}"]
                            f.write(f"-- {objeto_tipo} {nombre}\n")
                            f.write(f"DROP {objeto_tipo} IF EXISTS `{nombre}`;\n")
                            f.write(f"DELIMITER ;;\n{crear};;\nDELIMITER ;\n\n")
                    elif objeto_tipo == "TRIGGER":
                        nombre = obj["Trigger"]
                        tabla = obj["Table"]
                        cursor.execute(f"SHOW CREATE TRIGGER {nombre}")
                        crear = cursor.fetchone()["SQL Original Statement"]
                        f.write(f"-- TRIGGER {nombre} en tabla {tabla}\n")
                        f.write(f"DROP TRIGGER IF EXISTS `{nombre}`;\n")
                        f.write(f"DELIMITER ;;\n{crear};;\nDELIMITER ;\n\n")
            
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        
        # Cerrar conexiones
        cursor.close()
        conn.close()
        
        # Verificar que el archivo se creó y tiene contenido
        if os.path.exists(ruta_completa) and os.path.getsize(ruta_completa) > 0:
            logger.info(f"Respaldo creado exitosamente: {ruta_completa}")
            logger.info(f"Tamaño del respaldo: {os.path.getsize(ruta_completa) / (1024*1024):.2f} MB")
            return True
        else:
            logger.error("El archivo de respaldo está vacío o no se creó correctamente")
            return False
            
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Error de acceso: usuario o contraseña incorrectos")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error(f"La base de datos {DB_CONFIG['database']} no existe")
        else:
            logger.error(f"Error de MySQL: {err}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al realizar respaldo: {e}")
        return False

def comprimir_respaldo(nombre_archivo):
    """
    Comprime el archivo de respaldo para ahorrar espacio.
    
    Args:
        nombre_archivo: Nombre del archivo a comprimir
        
    Returns:
        str: Nombre del archivo comprimido o None si hubo error
    """
    ruta_completa = os.path.join(BACKUP_DIR, nombre_archivo)
    archivo_comprimido = f"{ruta_completa}.zip"
    
    try:
        import zipfile
        with zipfile.ZipFile(archivo_comprimido, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(ruta_completa, arcname=nombre_archivo)
        
        # Verificar que la compresión fue exitosa
        if os.path.exists(archivo_comprimido) and os.path.getsize(archivo_comprimido) > 0:
            # Eliminar el archivo original
            os.remove(ruta_completa)
            logger.info(f"Respaldo comprimido exitosamente: {archivo_comprimido}")
            logger.info(f"Tamaño del archivo comprimido: {os.path.getsize(archivo_comprimido) / (1024*1024):.2f} MB")
            return os.path.basename(archivo_comprimido)
        else:
            logger.error("El archivo comprimido está vacío o no se creó correctamente")
            return None
    except Exception as e:
        logger.error(f"Error al comprimir respaldo: {e}")
        return None

def rotar_respaldos():
    """
    Elimina los respaldos más antiguos si se supera el número máximo de respaldos.
    """
    try:
        # Obtener lista de archivos de respaldo
        archivos = [f for f in os.listdir(BACKUP_DIR) if f.startswith("respaldo_") and f.endswith(".zip")]
        
        # Ordenar por fecha de modificación (más antiguo primero)
        archivos.sort(key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)))
        
        # Eliminar los más antiguos si hay demasiados
        if len(archivos) > MAX_BACKUPS:
            exceso = len(archivos) - MAX_BACKUPS
            for i in range(exceso):
                archivo_a_eliminar = os.path.join(BACKUP_DIR, archivos[i])
                os.remove(archivo_a_eliminar)
                logger.info(f"Respaldo antiguo eliminado: {archivo_a_eliminar}")
        
        logger.info(f"Rotación de respaldos completada. Respaldos actuales: {len(archivos) - exceso if len(archivos) > MAX_BACKUPS else len(archivos)}")
    except Exception as e:
        logger.error(f"Error al rotar respaldos: {e}")

def main():
    """Función principal del script de respaldo."""
    parser = argparse.ArgumentParser(description='Realiza respaldos de la base de datos del Sistema Ganadero.')
    parser.add_argument('--no-compress', action='store_true', help='No comprimir el archivo de respaldo')
    parser.add_argument('--no-rotate', action='store_true', help='No realizar rotación de respaldos antiguos')
    args = parser.parse_args()
    
    logger.info("=== INICIANDO PROCESO DE RESPALDO DE BASE DE DATOS ===")
    
    # Crear directorio de respaldos si no existe
    crear_directorio_respaldo()
    
    # Generar nombre de archivo para el respaldo
    nombre_archivo = generar_nombre_archivo()
    
    # Realizar el respaldo
    if realizar_respaldo(nombre_archivo):
        # Comprimir el respaldo (opcional)
        if not args.no_compress:
            nombre_archivo = comprimir_respaldo(nombre_archivo)
            if nombre_archivo is None:
                logger.warning("No se pudo comprimir el respaldo, pero el respaldo original está disponible")
        
        # Rotar respaldos antiguos (opcional)
        if not args.no_rotate:
            rotar_respaldos()
    else:
        logger.error("El proceso de respaldo falló")
        sys.exit(1)
    
    logger.info("=== PROCESO DE RESPALDO FINALIZADO EXITOSAMENTE ===")

if __name__ == "__main__":
    main()
