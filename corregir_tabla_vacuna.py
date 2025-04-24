# Script para corregir la estructura de la tabla vacuna y asegurar que tenga todos los campos necesarios
import sys
import os
sys.path.append(os.getcwd())

from src.database import get_db_connection
from datetime import datetime, timedelta

def corregir_tabla_vacuna():
    print("\n====== CORRIGIENDO ESTRUCTURA DE LA TABLA VACUNA ======\n")
    
    try:
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar estructura actual de la tabla vacuna
        print("Verificando estructura actual de la tabla vacuna...")
        cursor.execute("""
            DESCRIBE vacuna
        """)
        
        columnas_actuales = [col[0] for col in cursor.fetchall()]
        print(f"Columnas actuales: {columnas_actuales}")
        
        # Verificar si falta la columna "nombre"
        if 'nombre' not in columnas_actuales:
            print("La columna 'nombre' no existe. Añadiéndola...")
            cursor.execute("""
                ALTER TABLE vacuna
                ADD COLUMN nombre VARCHAR(100) NOT NULL AFTER id
            """)
            conn.commit()
            print("Columna 'nombre' añadida correctamente")
            
            # Actualizar los registros existentes para añadir nombres
            cursor.execute("""
                UPDATE vacuna
                SET nombre = 'Vacuna contra Aftosa'
                WHERE nombre IS NULL OR nombre = ''
            """)
            conn.commit()
            print("Registros actualizados con nombre predeterminado")
        
        # Verificar si la tabla tiene registros
        cursor.execute("SELECT COUNT(*) FROM vacuna")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Crear vacunas de ejemplo
            print("No hay vacunas registradas. Creando ejemplos...")
            
            # Primera vacuna - Aftosa (próxima a aplicar)
            fecha_proxima_1 = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO vacuna 
                (nombre, fecha_aplicacion, proxima_aplicacion, dosis, observaciones)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'Vacuna contra Aftosa',
                (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),
                fecha_proxima_1,
                '5ml subcutáneo',
                'Vacunación semestral obligatoria'
            ))
            vacuna_id_1 = cursor.lastrowid
            
            # Segunda vacuna - Brucelosis (próxima a aplicar)
            fecha_proxima_2 = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO vacuna 
                (nombre, fecha_aplicacion, proxima_aplicacion, dosis, observaciones)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'Vacuna contra Brucelosis',
                (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'),
                fecha_proxima_2,
                '3ml intramuscular',
                'Vacunación anual preventiva'
            ))
            vacuna_id_2 = cursor.lastrowid
            
            # Asignar animales a las vacunas
            cursor.execute("SELECT id FROM animales LIMIT 10")
            animales = cursor.fetchall()
            
            if animales:
                # Asignar los primeros 5 animales a la primera vacuna
                for i in range(min(5, len(animales))):
                    cursor.execute("""
                        INSERT INTO vacuna_animal (vacuna_id, animal_id)
                        VALUES (%s, %s)
                    """, (vacuna_id_1, animales[i][0]))
                
                # Asignar los siguientes 5 animales a la segunda vacuna
                for i in range(5, min(10, len(animales))):
                    cursor.execute("""
                        INSERT INTO vacuna_animal (vacuna_id, animal_id)
                        VALUES (%s, %s)
                    """, (vacuna_id_2, animales[i][0]))
                
                conn.commit()
                print(f"Ejemplos de vacunación añadidos con fechas próximas: {fecha_proxima_1} y {fecha_proxima_2}")
            else:
                print("No se encontraron animales para asignar a las vacunas")
        else:
            # Asegurarse de que hay vacunas con fechas próximas
            print("Actualizando fechas de vacunación próxima...")
            cursor.execute("""
                UPDATE vacuna
                SET proxima_aplicacion = %s
                WHERE id = 1
            """, ((datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),))
            
            # Asegurar que las vacunas tienen animales asignados
            cursor.execute("""
                SELECT COUNT(*) FROM vacuna_animal WHERE vacuna_id = 1
            """)
            count_rel = cursor.fetchone()[0]
            
            if count_rel == 0:
                print("No hay animales asignados a las vacunas. Asignando...")
                # Asignar algunos animales a la vacuna
                cursor.execute("SELECT id FROM animales LIMIT 5")
                animales = cursor.fetchall()
                
                if animales:
                    for animal in animales:
                        cursor.execute("""
                            INSERT INTO vacuna_animal (vacuna_id, animal_id)
                            VALUES (1, %s)
                        """, (animal[0],))
                    
                    conn.commit()
                    print("Animales asignados a la vacuna")
                else:
                    print("No se encontraron animales para asignar")
            
            conn.commit()
            print("Fechas de vacunación actualizadas")
        
        # Mostrar las vacunas configuradas
        cursor.execute("""
            SELECT v.id, v.nombre, v.proxima_aplicacion, COUNT(va.animal_id) as num_animales
            FROM vacuna v
            LEFT JOIN vacuna_animal va ON v.id = va.vacuna_id
            GROUP BY v.id
        """)
        
        vacunas = cursor.fetchall()
        print("\nVacunas configuradas:")
        for v in vacunas:
            print(f"ID: {v[0]}, Nombre: {v[1]}, Fecha próxima: {v[2]}, Animales asignados: {v[3]}")
        
        print("\n====== CORRECCIÓN DE TABLA VACUNA FINALIZADA ======\n")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    corregir_tabla_vacuna()
