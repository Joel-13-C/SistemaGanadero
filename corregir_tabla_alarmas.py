# Script para corregir la estructura de la tabla alarmas_enviadas
import sys
import os
sys.path.append(os.getcwd())

from src.database import get_db_connection

def corregir_tabla_alarmas_enviadas():
    print("\n=== CORRIGIENDO ESTRUCTURA DE TABLA ALARMAS_ENVIADAS ===\n")
    
    try:
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la tabla alarmas_enviadas existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'sistema_ganadero' 
            AND table_name = 'alarmas_enviadas'
        """)
        tabla_existe = cursor.fetchone()[0] > 0
        print(f"¿Existe la tabla alarmas_enviadas?: {tabla_existe}")
        
        if tabla_existe:
            # Verificar la estructura de la tabla
            cursor.execute("""
                SHOW COLUMNS FROM alarmas_enviadas
            """)
            columnas = [col[0] for col in cursor.fetchall()]
            print(f"Columnas actuales: {columnas}")
            
            # Verificar si la columna mensaje existe
            if 'mensaje' not in columnas:
                print("La columna 'mensaje' no existe. Añadiéndola...")
                cursor.execute("""
                    ALTER TABLE alarmas_enviadas
                    ADD COLUMN mensaje TEXT AFTER email
                """)
                conn.commit()
                print("Columna 'mensaje' añadida correctamente")
            else:
                print("La columna 'mensaje' ya existe")
        else:
            # Crear la tabla si no existe
            print("La tabla no existe. Creándola...")
            cursor.execute("""
                CREATE TABLE alarmas_enviadas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    tipo VARCHAR(50) NOT NULL,
                    referencia_id INT,
                    email VARCHAR(100) NOT NULL,
                    mensaje TEXT,
                    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Tabla alarmas_enviadas creada correctamente")
        
        print("\n=== CORRECCIÓN DE TABLA FINALIZADA ===\n")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    corregir_tabla_alarmas_enviadas()
