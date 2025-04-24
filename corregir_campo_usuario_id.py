# Script para corregir el campo usuario_id en la tabla alarmas_enviadas
import sys
import os
sys.path.append(os.getcwd())

from src.database import get_db_connection

def corregir_campo_usuario_id():
    print("\n=== CORRIGIENDO CAMPO USUARIO_ID EN TABLA ALARMAS_ENVIADAS ===\n")
    
    try:
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Modificar el campo usuario_id para que permita valores NULL
        cursor.execute("""
            ALTER TABLE alarmas_enviadas
            MODIFY COLUMN usuario_id INT NULL DEFAULT 1
        """)
        
        conn.commit()
        print("Campo usuario_id modificado correctamente para permitir valores NULL y tener valor predeterminado 1")
        
        print("\n=== CORRECCIÓN DE CAMPO USUARIO_ID FINALIZADA ===\n")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    corregir_campo_usuario_id()
