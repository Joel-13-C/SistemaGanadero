#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para restaurar un respaldo de la base de datos del Sistema Ganadero.
Este script permite restaurar un respaldo SQL previamente generado,
ya sea directamente desde un archivo SQL o desde un archivo comprimido ZIP.

Autor: Sistema Ganadero
Fecha: Abril 2025
"""

import os
import sys
import zipfile
import logging
import argparse
import datetime
import tempfile
import mysql.connector
from mysql.connector import errorcode

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/restauracion.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('restauracion')

# Crear directorio de logs si no existe
os.makedirs('logs', exist_ok=True)

# Configuración predeterminada (se puede sobrescribir con variables de entorno)
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "1234"),
    "port": os.getenv("MYSQL_PORT", "3306")
}

def descomprimir_respaldo(archivo_zip):
    """
    Descomprime un archivo ZIP que contiene un respaldo SQL.
    
    Args:
        archivo_zip: Ruta al archivo ZIP
        
    Returns:
        str: Ruta al archivo SQL descomprimido, o None si hubo un error
    """
    try:
        # Crear un directorio temporal
        directorio_temp = tempfile.mkdtemp()
        logger.info(f"Descomprimiendo {archivo_zip} en {directorio_temp}")
        
        with zipfile.ZipFile(archivo_zip, 'r') as zip_ref:
            # Obtener el nombre del archivo SQL dentro del ZIP
            archivos = zip_ref.namelist()
            archivos_sql = [f for f in archivos if f.endswith('.sql')]
            
            if not archivos_sql:
                logger.error("No se encontró ningún archivo SQL dentro del ZIP")
                return None
                
            # Extraer solo el archivo SQL
            archivo_sql = archivos_sql[0]
            zip_ref.extract(archivo_sql, directorio_temp)
            
            ruta_sql = os.path.join(directorio_temp, archivo_sql)
            logger.info(f"Archivo SQL extraído: {ruta_sql}")
            
            return ruta_sql
            
    except Exception as e:
        logger.error(f"Error al descomprimir el archivo: {str(e)}")
        return None

def restaurar_base_datos(archivo_sql, nombre_bd, crear_bd=False):
    """
    Restaura un archivo SQL en la base de datos.
    
    Args:
        archivo_sql: Ruta al archivo SQL
        nombre_bd: Nombre de la base de datos
        crear_bd: Si es True, crea la base de datos si no existe
        
    Returns:
        bool: True si la restauración fue exitosa, False en caso contrario
    """
    try:
        logger.info(f"Conectando a MySQL en {DB_CONFIG['host']}:{DB_CONFIG['port']} como {DB_CONFIG['user']}")
        
        # Primero conectar sin especificar base de datos
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        
        cursor = conn.cursor()
        
        # Crear la base de datos si es necesario
        if crear_bd:
            logger.info(f"Verificando si la base de datos {nombre_bd} existe")
            cursor.execute(f"SHOW DATABASES LIKE '{nombre_bd}'")
            resultado = cursor.fetchone()
            
            if not resultado:
                logger.info(f"Creando base de datos {nombre_bd}")
                cursor.execute(f"CREATE DATABASE `{nombre_bd}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                logger.info(f"Base de datos {nombre_bd} creada")
            else:
                logger.info(f"La base de datos {nombre_bd} ya existe")
        
        # Seleccionar la base de datos
        logger.info(f"Usando base de datos {nombre_bd}")
        cursor.execute(f"USE `{nombre_bd}`")
        
        # Leer el archivo SQL y ejecutarlo
        logger.info(f"Leyendo archivo SQL: {archivo_sql}")
        with open(archivo_sql, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        # Dividir el contenido en sentencias individuales
        logger.info("Ejecutando sentencias SQL...")
        
        # Desactivar restricciones de clave foránea
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        
        # Ejecutar por bloques para manejar archivos grandes
        for comando in contenido.split(';'):
            comando = comando.strip()
            if comando:
                try:
                    cursor.execute(comando + ';')
                except mysql.connector.Error as err:
                    logger.warning(f"Error al ejecutar comando SQL: {err}")
                    # Continuar con el siguiente comando
        
        # Reactivar restricciones de clave foránea
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        
        # Confirmar cambios y cerrar conexión
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Restauración completada exitosamente")
        return True
        
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.error("Error de acceso: usuario o contraseña incorrectos")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.error(f"La base de datos {nombre_bd} no existe")
        else:
            logger.error(f"Error de MySQL: {err}")
        return False
    except Exception as e:
        logger.error(f"Error inesperado al restaurar la base de datos: {str(e)}")
        return False

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(description='Restaura un respaldo de la base de datos')
    parser.add_argument('archivo', type=str, 
                        help='Ruta al archivo de respaldo (.sql o .zip)')
    parser.add_argument('--bd', type=str, default='sistema_ganadero_test',
                        help='Nombre de la base de datos destino (default: sistema_ganadero_test)')
    parser.add_argument('--crear-bd', action='store_true',
                        help='Crear la base de datos si no existe')
    parser.add_argument('--host', type=str, default=DB_CONFIG['host'],
                        help=f'Host de MySQL (default: {DB_CONFIG["host"]})')
    parser.add_argument('--usuario', type=str, default=DB_CONFIG['user'],
                        help=f'Usuario de MySQL (default: {DB_CONFIG["user"]})')
    parser.add_argument('--password', type=str, default=DB_CONFIG['password'],
                        help='Contraseña de MySQL')
    parser.add_argument('--puerto', type=str, default=DB_CONFIG['port'],
                        help=f'Puerto de MySQL (default: {DB_CONFIG["port"]})')
    
    args = parser.parse_args()
    
    # Actualizar configuración
    DB_CONFIG['host'] = args.host
    DB_CONFIG['user'] = args.usuario
    DB_CONFIG['password'] = args.password
    DB_CONFIG['port'] = args.puerto
    
    # Verificar que el archivo existe
    if not os.path.exists(args.archivo):
        logger.error(f"El archivo {args.archivo} no existe")
        sys.exit(1)
    
    logger.info("=== INICIANDO PROCESO DE RESTAURACIÓN DE BASE DE DATOS ===")
    
    archivo_sql = None
    es_temporal = False
    
    # Determinar si es un archivo ZIP o SQL
    if args.archivo.lower().endswith('.zip'):
        archivo_sql = descomprimir_respaldo(args.archivo)
        es_temporal = True
        
        if not archivo_sql:
            logger.error("No se pudo extraer el archivo SQL del ZIP")
            sys.exit(1)
    else:
        archivo_sql = args.archivo
    
    # Restaurar la base de datos
    resultado = restaurar_base_datos(archivo_sql, args.bd, args.crear_bd)
    
    # Limpiar archivos temporales
    if es_temporal and archivo_sql and os.path.exists(archivo_sql):
        directorio_temp = os.path.dirname(archivo_sql)
        logger.info(f"Eliminando archivos temporales en {directorio_temp}")
        try:
            import shutil
            shutil.rmtree(directorio_temp)
        except Exception as e:
            logger.warning(f"No se pudieron eliminar los archivos temporales: {str(e)}")
    
    if resultado:
        logger.info("=== PROCESO DE RESTAURACIÓN FINALIZADO EXITOSAMENTE ===")
    else:
        logger.error("=== EL PROCESO DE RESTAURACIÓN FALLÓ ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
