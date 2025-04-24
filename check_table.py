from src.database import get_db_connection

def check_table_structure():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar la estructura de la tabla equipos
        cursor.execute('DESCRIBE equipos')
        result = cursor.fetchall()
        
        print('Estructura de la tabla equipos:')
        for row in result:
            print(row)
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al verificar la estructura de la tabla: {str(e)}")

if __name__ == "__main__":
    check_table_structure()
