#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para copiar respaldos de la base de datos a un almacenamiento externo.
Este script puede ejecutarse después del respaldo principal para asegurar que
las copias de seguridad estén disponibles en múltiples ubicaciones.

Autor: Sistema Ganadero
Fecha: Abril 2025
"""

import os
import shutil
import logging
import datetime
import argparse
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/copias_externas.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('copias_externas')

# Crear directorio de logs si no existe
os.makedirs('logs', exist_ok=True)

def copiar_a_unidad_externa(origen, destino, max_copias=10):
    """
    Copia los archivos de respaldo a una unidad externa o carpeta de red.
    
    Args:
        origen: Ruta de la carpeta de origen con los respaldos
        destino: Ruta de la carpeta de destino
        max_copias: Número máximo de copias a mantener en el destino
    
    Returns:
        bool: True si la copia fue exitosa, False en caso contrario
    """
    try:
        # Verificar que la carpeta de origen existe
        if not os.path.exists(origen):
            logger.error(f"La carpeta de origen {origen} no existe")
            return False
        
        # Crear la carpeta de destino si no existe
        os.makedirs(destino, exist_ok=True)
        
        logger.info(f"Iniciando copia de respaldos desde {origen} hacia {destino}")
        
        # Obtener lista de archivos de respaldo (solo archivos .zip)
        archivos_respaldo = [f for f in os.listdir(origen) if f.endswith('.zip')]
        
        if not archivos_respaldo:
            logger.warning("No se encontraron archivos de respaldo para copiar")
            return False
        
        # Ordenar por fecha (más reciente primero)
        archivos_respaldo.sort(reverse=True)
        
        # Copiar los archivos más recientes
        copiados = 0
        for archivo in archivos_respaldo:
            origen_completo = os.path.join(origen, archivo)
            destino_completo = os.path.join(destino, archivo)
            
            # Verificar si el archivo ya existe en el destino
            if os.path.exists(destino_completo):
                # Verificar si el archivo de origen es más reciente
                tiempo_origen = os.path.getmtime(origen_completo)
                tiempo_destino = os.path.getmtime(destino_completo)
                
                if tiempo_origen <= tiempo_destino:
                    logger.info(f"El archivo {archivo} ya existe en el destino y está actualizado")
                    copiados += 1
                    continue
            
            # Copiar el archivo
            logger.info(f"Copiando {archivo} al destino...")
            shutil.copy2(origen_completo, destino_completo)
            logger.info(f"Archivo {archivo} copiado exitosamente")
            copiados += 1
            
            # Limitar el número de copias
            if copiados >= max_copias:
                break
        
        # Eliminar copias antiguas si hay más del máximo permitido
        todos_destino = [f for f in os.listdir(destino) if f.endswith('.zip')]
        todos_destino.sort(reverse=True)  # Más reciente primero
        
        if len(todos_destino) > max_copias:
            for archivo_antiguo in todos_destino[max_copias:]:
                ruta_completa = os.path.join(destino, archivo_antiguo)
                logger.info(f"Eliminando copia antigua: {archivo_antiguo}")
                os.remove(ruta_completa)
        
        logger.info(f"Proceso de copia finalizado. Se copiaron {copiados} archivos")
        return True
        
    except Exception as e:
        logger.error(f"Error al copiar respaldos: {str(e)}")
        return False

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(description='Copia respaldos a almacenamiento externo')
    parser.add_argument('--origen', type=str, default='respaldos',
                        help='Carpeta de origen con los respaldos (default: respaldos)')
    parser.add_argument('--destino', type=str, required=True,
                        help='Carpeta de destino para las copias (ej: E:\\Respaldos o \\\\servidor\\compartido)')
    parser.add_argument('--max-copias', type=int, default=10,
                        help='Número máximo de copias a mantener (default: 10)')
    
    args = parser.parse_args()
    
    # Convertir rutas relativas a absolutas
    origen = os.path.abspath(args.origen)
    destino = args.destino
    
    logger.info("=== INICIANDO PROCESO DE COPIA DE RESPALDOS ===")
    resultado = copiar_a_unidad_externa(origen, destino, args.max_copias)
    
    if resultado:
        logger.info("=== PROCESO DE COPIA FINALIZADO EXITOSAMENTE ===")
    else:
        logger.error("=== EL PROCESO DE COPIA FALLÓ ===")

if __name__ == "__main__":
    main()
