# Script para depurar la función de obtención de animales
import sys
import os
from src.database import get_db_connection, DatabaseConnection

# Inicializar la conexión
db_connection = DatabaseConnection()

# ID del animal a buscar (puedes cambiar este valor)
try:
    animal_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
except:
    animal_id = 1

print(f"Intentando obtener el animal con ID: {animal_id}")

# Probar la función actual
try:
    animal = db_connection.obtener_animal_por_id(animal_id)
    if animal:
        print("Animal encontrado con la función actual:")
        print(f"ID: {animal['id']}")
        print(f"Nombre: {animal['nombre']}")
        print(f"Arete: {animal['numero_arete']}")
    else:
        print("Animal NO encontrado con la función actual.")
except Exception as e:
    print(f"Error con la función actual: {e}")

# Probar una consulta directa a la base de datos
try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM animales WHERE id = %s", (animal_id,))
    animal_direct = cursor.fetchone()
    
    if animal_direct:
        print("\nAnimal encontrado con consulta directa:")
        print(f"ID: {animal_direct['id']}")
        print(f"Nombre: {animal_direct['nombre']}")
        print(f"Arete: {animal_direct['numero_arete']}")
    else:
        print("\nAnimal NO encontrado con consulta directa.")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error con consulta directa: {e}")

# Función corregida para obtener animal por ID
def obtener_animal_por_id_corregido(animal_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Consulta simple para obtener el animal
        cursor.execute("""
            SELECT * FROM animales WHERE id = %s
        """, (animal_id,))
        
        animal = cursor.fetchone()
        
        # Si encontramos el animal, intentamos obtener datos del padre y madre
        if animal:
            # Buscar datos del padre si existe un ID de padre
            if animal.get('padre_id'):
                cursor.execute("SELECT nombre, numero_arete FROM animales WHERE id = %s", 
                              (animal['padre_id'],))
                padre = cursor.fetchone()
                if padre:
                    animal['nombre_padre'] = padre['nombre']
                    animal['arete_padre'] = padre['numero_arete']
            
            # Buscar datos de la madre si existe un ID de madre
            if animal.get('madre_id'):
                cursor.execute("SELECT nombre, numero_arete FROM animales WHERE id = %s", 
                              (animal['madre_id'],))
                madre = cursor.fetchone()
                if madre:
                    animal['nombre_madre'] = madre['nombre']
                    animal['arete_madre'] = madre['numero_arete']
        
        cursor.close()
        conn.close()
        return animal
    except Exception as e:
        print(f"Error en función corregida: {e}")
        return None

# Probar la función corregida
try:
    animal_corrected = obtener_animal_por_id_corregido(animal_id)
    if animal_corrected:
        print("\nAnimal encontrado con la función corregida:")
        print(f"ID: {animal_corrected['id']}")
        print(f"Nombre: {animal_corrected['nombre']}")
        print(f"Arete: {animal_corrected['numero_arete']}")
    else:
        print("\nAnimal NO encontrado con la función corregida.")
except Exception as e:
    print(f"Error con la función corregida: {e}")

# Listado de todos los animales con ID y nombre
try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, nombre, numero_arete FROM animales ORDER BY id")
    all_animals = cursor.fetchall()
    
    print("\nListado de todos los animales disponibles:")
    for a in all_animals:
        print(f"ID: {a['id']}, Nombre: {a['nombre']}, Arete: {a['numero_arete']}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error al listar animales: {e}")
