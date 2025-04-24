import mysql.connector
import sys

def get_db_connection():
    # Intentar diferentes combinaciones de credenciales
    credentials = [
        {'user': 'root', 'password': 'root'},
        {'user': 'root', 'password': ''},
        {'user': 'root', 'password': 'admin'},
        {'user': 'admin', 'password': 'admin'}
    ]
    
    for cred in credentials:
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user=cred['user'],
                password=cred['password'],
                database='sistema_ganadero'
            )
            print(f"Conexión exitosa con usuario: {cred['user']} y contraseña: {cred['password']}")
            return connection
        except mysql.connector.Error as e:
            print(f"Error al conectar con usuario: {cred['user']} y contraseña: {cred['password']}: {e}")
    
    return None

def crear_tabla_auditoria():
    conn = get_db_connection()
    if not conn:
        print("No se pudo conectar a la base de datos.")
        sys.exit(1)
    
    cursor = conn.cursor()
    
    try:
        # Verificar si la tabla ya existe
        cursor.execute("SHOW TABLES LIKE 'auditoria'")
        if cursor.fetchone():
            print("La tabla 'auditoria' ya existe.")
        else:
            # Crear tabla de auditoría
            cursor.execute("""
                CREATE TABLE auditoria (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    usuario_id INT,
                    accion VARCHAR(255) NOT NULL,
                    modulo VARCHAR(100) NOT NULL,
                    descripcion TEXT,
                    fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip VARCHAR(45),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
                )
            """)
            conn.commit()
            print("Tabla 'auditoria' creada exitosamente.")
    except mysql.connector.Error as e:
        print(f"Error al crear la tabla de auditoría: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    crear_tabla_auditoria()
