#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para crear vacunaciones de prueba en el sistema.
"""

from src.database import get_db_connection
import sys
from datetime import datetime, timedelta

def main():
    """
    Función principal que crea vacunaciones de prueba
    """
    print("\n===== CREANDO VACUNACIONES DE PRUEBA =====\n")
    
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener algunos animales para asignarles vacunas
        cursor.execute("SELECT id, nombre, numero_arete FROM animales LIMIT 5")
        animales = cursor.fetchall()
        
        if not animales:
            print("No se encontraron animales en la base de datos")
            return 1
            
        print(f"Animales encontrados: {len(animales)}")
        for animal in animales:
            print(f"- ID: {animal[0]}, Nombre: {animal[1]}, Arete: {animal[2]}")
        
        # Crear algunas vacunas de prueba
        vacunas = [
            {
                'tipo': 'Brucelosis',
                'fecha_aplicacion': datetime.now().date() - timedelta(days=30),
                'fecha_proxima': datetime.now().date() + timedelta(days=5),  # En 5 días
                'dosis': '5ml',
                'aplicada_por': 'Dr. Veterinario',
                'observaciones': 'Vacuna preventiva contra brucelosis',
                'estado': 'Activo',
                'producto': 'Brucella Abortus RB51'
            },
            {
                'tipo': 'Carbunco',
                'fecha_aplicacion': datetime.now().date() - timedelta(days=60),
                'fecha_proxima': datetime.now().date() + timedelta(days=3),  # En 3 días
                'dosis': '3ml',
                'aplicada_por': 'Dr. Veterinario',
                'observaciones': 'Vacuna preventiva contra carbunco',
                'estado': 'Activo',
                'producto': 'Carbuvax'
            }
        ]
        
        # Insertar las vacunas y relacionarlas con los animales
        for i, vacuna in enumerate(vacunas):
            # Insertar la vacuna
            cursor.execute("""
                INSERT INTO vacuna (
                    animal_id, usuario_id, tipo, fecha_aplicacion, fecha_proxima,
                    dosis, aplicada_por, observaciones, estado, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                animales[0][0],  # animal_id (usamos el primer animal para la relación directa)
                1,  # usuario_id (asumimos que el usuario 1 es el administrador)
                vacuna['tipo'],
                vacuna['fecha_aplicacion'],
                vacuna['fecha_proxima'],
                vacuna['dosis'],
                vacuna['aplicada_por'],
                vacuna['observaciones'],
                vacuna['estado']
            ))
            
            # Obtener el ID de la vacuna insertada
            vacuna_id = cursor.lastrowid
            
            # Relacionar la vacuna con varios animales
            for j, animal in enumerate(animales):
                if j <= i+1:  # Asignar la vacuna a algunos animales
                    cursor.execute("""
                        INSERT INTO vacuna_animal (vacuna_id, animal_id, fecha_aplicacion)
                        VALUES (%s, %s, %s)
                    """, (
                        vacuna_id,
                        animal[0],
                        vacuna['fecha_aplicacion']
                    ))
            
            print(f"Vacuna '{vacuna['tipo']}' creada con ID: {vacuna_id}")
        
        conn.commit()
        print("\nVacunaciones de prueba creadas exitosamente")
        
        return 0  # Éxito
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return 1  # Error
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
