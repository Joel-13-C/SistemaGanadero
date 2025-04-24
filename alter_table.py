from src.database import get_db_connection

def alter_equipos_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si la columna 'tipo' ya existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'equipos' 
            AND column_name = 'tipo'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Añadir columna 'tipo'
            cursor.execute("""
                ALTER TABLE equipos 
                ADD COLUMN tipo VARCHAR(50) NOT NULL DEFAULT 'Otro' 
                AFTER nombre
            """)
            print("Columna 'tipo' añadida correctamente")
        
        # Verificar si la columna 'marca' ya existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'equipos' 
            AND column_name = 'marca'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Añadir columna 'marca'
            cursor.execute("""
                ALTER TABLE equipos 
                ADD COLUMN marca VARCHAR(100) 
                AFTER tipo
            """)
            print("Columna 'marca' añadida correctamente")
        
        # Verificar si la columna 'costo' ya existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'equipos' 
            AND column_name = 'costo'
        """)
        
        if cursor.fetchone()[0] == 0:
            # Añadir columna 'costo'
            cursor.execute("""
                ALTER TABLE equipos 
                ADD COLUMN costo DECIMAL(10,2) DEFAULT 0 
                AFTER fecha_adquisicion
            """)
            print("Columna 'costo' añadida correctamente")
        
        # Renombrar columna 'descripcion' a 'observaciones' si existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'equipos' 
            AND column_name = 'descripcion'
        """)
        
        if cursor.fetchone()[0] > 0:
            # Renombrar columna 'descripcion' a 'observaciones'
            cursor.execute("""
                ALTER TABLE equipos 
                CHANGE COLUMN descripcion observaciones TEXT
            """)
            print("Columna 'descripcion' renombrada a 'observaciones' correctamente")
        
        conn.commit()
        print("Tabla 'equipos' modificada correctamente")
        
        # Verificar la estructura actualizada
        cursor.execute('DESCRIBE equipos')
        result = cursor.fetchall()
        
        print('\nEstructura actualizada de la tabla equipos:')
        for row in result:
            print(row)
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al modificar la tabla: {str(e)}")
        if 'conn' in locals() and conn:
            conn.rollback()

if __name__ == "__main__":
    alter_equipos_table()
