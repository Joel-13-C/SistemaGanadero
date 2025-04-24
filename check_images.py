import mysql.connector

# Configuración de la conexión
conexion = mysql.connector.connect(
    host='localhost',
    user='root',
    password='1234',
    database='sistema_ganadero'
)

# Crear un cursor
cursor = conexion.cursor(dictionary=True)

# Consulta para obtener los detalles de Lola y Toribio
consulta = "SELECT id, nombre, foto_path FROM animales WHERE nombre IN ('Lola', 'Toribio')"
cursor.execute(consulta)

# Obtener y mostrar resultados
resultados = cursor.fetchall()
for animal in resultados:
    print(f"ID: {animal['id']}, Nombre: {animal['nombre']}, Foto Path: {animal['foto_path']}")

# Cerrar cursor y conexión
cursor.close()
conexion.close()
