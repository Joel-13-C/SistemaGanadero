import mysql.connector
from mysql.connector import Error

def crear_tabla_vacuna():
    """
    Crea la tabla vacuna en la base de datos sistema_ganadero
    """
    # Configuración de conexión
    conexiones_a_probar = [
        {"host": "localhost", "user": "root", "password": "1234"}
    ]
    
    conn = None
    for config in conexiones_a_probar:
        try:
            print(f"Intentando conectar con: {config}")
            conn = mysql.connector.connect(**config)
            if conn.is_connected():
                print(f"Conexión exitosa con: {config}")
                break
        except Error as e:
            print(f"Error al conectar con: {config}. Error: {e}")
            continue
    
    if not conn or not conn.is_connected():
        print("No se pudo establecer conexión con ninguna configuración")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        cursor.execute("CREATE DATABASE IF NOT EXISTS sistema_ganadero")
        cursor.execute("USE sistema_ganadero")
        
        # Crear tabla vacuna
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacuna (
            id INT AUTO_INCREMENT PRIMARY KEY,
            animal_id INT NOT NULL,
            usuario_id INT NOT NULL,
            tipo VARCHAR(100) NOT NULL,
            fecha_aplicacion DATE,
            fecha_proxima DATE NOT NULL,
            dosis VARCHAR(50),
            aplicada_por VARCHAR(100),
            observaciones TEXT,
            estado VARCHAR(20) DEFAULT 'Activo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_animal (animal_id),
            INDEX idx_usuario (usuario_id),
            INDEX idx_estado (estado),
            INDEX idx_fecha_proxima (fecha_proxima)
        )
        """)
        
        conn.commit()
        print("Tabla vacuna creada exitosamente")
        return True
    
    except Error as e:
        print(f"Error al crear tabla vacuna: {e}")
        return False
    
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    crear_tabla_vacuna()
