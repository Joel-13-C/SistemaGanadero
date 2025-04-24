#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script para crear la tabla vacuna_animal que falta en la base de datos.
"""

from src.database import get_db_connection
import sys

def main():
    """
    Función principal que crea la tabla vacuna_animal
    """
    print("\n===== CREANDO TABLA VACUNA_ANIMAL =====\n")
    
    try:
        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Crear la tabla vacuna_animal si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vacuna_animal (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vacuna_id INT NOT NULL,
                animal_id INT NOT NULL,
                fecha_aplicacion DATE,
                FOREIGN KEY (vacuna_id) REFERENCES vacuna(id),
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        conn.commit()
        print("Tabla vacuna_animal creada exitosamente")
        
        # Verificar la estructura de la tabla vacuna
        cursor.execute("DESCRIBE vacuna")
        columnas_vacuna = cursor.fetchall()
        print("\nEstructura de la tabla vacuna:")
        for columna in columnas_vacuna:
            print(f"- {columna[0]}: {columna[1]}")
        
        return 0  # Éxito
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        return 1  # Error
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
