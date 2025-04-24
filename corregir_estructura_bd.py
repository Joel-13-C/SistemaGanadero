# Script para corregir la estructura de la base de datos
import sys
import os
sys.path.append(os.getcwd())

from src.database import get_db_connection

def corregir_estructura_base_datos():
    print("\n====== CORRIGIENDO ESTRUCTURA DE LA BASE DE DATOS ======\n")
    
    try:
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Verificar y crear tabla reproducción si no existe
        print("------ Verificando tabla reproduccion ------")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sistema_ganadero' 
            AND table_name = 'reproduccion'
        """)
        tabla_existe = cursor.fetchone()[0] > 0
        print(f"¿Existe la tabla reproduccion?: {tabla_existe}")
        
        if not tabla_existe:
            print("Creando tabla reproduccion...")
            cursor.execute("""
                CREATE TABLE reproduccion (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    animal_id INT NOT NULL,
                    fecha_monta DATE,
                    fecha_parto_estimada DATE,
                    padre_id INT,
                    observaciones TEXT,
                    estado VARCHAR(20) DEFAULT 'Activo',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (animal_id) REFERENCES animales(id),
                    FOREIGN KEY (padre_id) REFERENCES animales(id)
                )
            """)
            conn.commit()
            print("Tabla reproduccion creada correctamente")
        
        # 2. Verificar y añadir ejemplo de reproducción para probar alertas
        print("------ Añadiendo ejemplo de reproducción ------")
        cursor.execute("SELECT * FROM reproduccion LIMIT 1")
        tiene_registros = cursor.fetchone() is not None
        
        if not tiene_registros:
            # Buscar una hembra para el ejemplo
            cursor.execute("SELECT id FROM animales WHERE sexo = 'Hembra' LIMIT 1")
            result = cursor.fetchone()
            if result:
                animal_id = result[0]
                # Añadir registro de reproducción con fecha de parto próxima
                from datetime import datetime, timedelta
                fecha_parto = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
                
                cursor.execute("""
                    INSERT INTO reproduccion 
                    (animal_id, fecha_monta, fecha_parto_estimada, observaciones)
                    VALUES (%s, %s, %s, %s)
                """, (
                    animal_id,
                    (datetime.now() - timedelta(days=275)).strftime('%Y-%m-%d'),  # 275 días atrás (gestación vaca)
                    fecha_parto,
                    'Parto próximo para prueba de alertas automáticas'
                ))
                conn.commit()
                print(f"Ejemplo de reproducción añadido con fecha de parto: {fecha_parto}")
            else:
                print("No se encontraron animales hembra para el ejemplo")
        
        # 3. Verificar estructura de la tabla vacuna
        print("\n------ Verificando tabla vacuna ------")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sistema_ganadero' 
            AND table_name = 'vacuna'
        """)
        tabla_existe = cursor.fetchone()[0] > 0
        print(f"¿Existe la tabla vacuna?: {tabla_existe}")
        
        if tabla_existe:
            # Verificar si tiene la columna proxima_aplicacion
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'sistema_ganadero'
                AND TABLE_NAME = 'vacuna'
                AND COLUMN_NAME = 'proxima_aplicacion'
            """)
            tiene_columna = cursor.fetchone() is not None
            print(f"¿Tiene columna proxima_aplicacion?: {tiene_columna}")
            
            if not tiene_columna:
                print("Añadiendo columna proxima_aplicacion a la tabla vacuna...")
                cursor.execute("""
                    ALTER TABLE vacuna
                    ADD COLUMN proxima_aplicacion DATE AFTER fecha_aplicacion
                """)
                conn.commit()
                print("Columna proxima_aplicacion añadida correctamente")
                
                # Actualizar registros existentes para añadir fecha próxima
                cursor.execute("""
                    UPDATE vacuna
                    SET proxima_aplicacion = DATE_ADD(fecha_aplicacion, INTERVAL 180 DAY)
                    WHERE proxima_aplicacion IS NULL
                """)
                conn.commit()
                print("Fechas próximas de vacunación actualizadas")
        else:
            # Crear la tabla vacuna completa
            print("Creando tabla vacuna...")
            cursor.execute("""
                CREATE TABLE vacuna (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(100) NOT NULL,
                    fecha_aplicacion DATE,
                    proxima_aplicacion DATE,
                    dosis VARCHAR(50),
                    observaciones TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Tabla vacuna creada correctamente")
            
            # Crear tabla de relación vacuna_animal
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vacuna_animal (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    vacuna_id INT NOT NULL,
                    animal_id INT NOT NULL,
                    FOREIGN KEY (vacuna_id) REFERENCES vacuna(id),
                    FOREIGN KEY (animal_id) REFERENCES animales(id)
                )
            """)
            conn.commit()
            print("Tabla vacuna_animal creada correctamente")
            
        # 4. Verificar y añadir ejemplo de vacunación para probar alertas
        print("------ Añadiendo ejemplo de vacunación ------")
        cursor.execute("SELECT * FROM vacuna LIMIT 1")
        tiene_registros = cursor.fetchone() is not None
        
        if not tiene_registros:
            # Añadir vacuna de ejemplo
            from datetime import datetime, timedelta
            fecha_proxima = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT INTO vacuna 
                (nombre, fecha_aplicacion, proxima_aplicacion, dosis, observaciones)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                'Vacuna contra Aftosa',
                (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'),  # 6 meses atrás
                fecha_proxima,
                '5ml subcutáneo',
                'Vacunación semestral para prueba de alertas automáticas'
            ))
            conn.commit()
            vacuna_id = cursor.lastrowid
            
            # Asignar a algunos animales
            cursor.execute("SELECT id FROM animales LIMIT 5")
            animales = cursor.fetchall()
            
            if animales:
                for animal in animales:
                    cursor.execute("""
                        INSERT INTO vacuna_animal (vacuna_id, animal_id)
                        VALUES (%s, %s)
                    """, (vacuna_id, animal[0]))
                
                conn.commit()
                print(f"Ejemplo de vacunación añadido con fecha próxima: {fecha_proxima} para {len(animales)} animales")
            else:
                print("No se encontraron animales para el ejemplo de vacunación")
        
        print("\n====== CORRECCIÓN DE ESTRUCTURA FINALIZADA ======\n")
        
    except Exception as e:
        print(f"Error al corregir estructura de base de datos: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    corregir_estructura_base_datos()
