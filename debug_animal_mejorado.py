# Script para depurar la función de obtención de animales de forma directa
import sys
from src.database import get_db_connection
import mysql.connector

# ID del animal a buscar (puedes cambiar este valor)
try:
    animal_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
except:
    animal_id = 1

print(f"Intentando obtener el animal con ID: {animal_id}")

# Probar una consulta directa a la base de datos
try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Consulta básica
    cursor.execute("SELECT * FROM animales WHERE id = %s", (animal_id,))
    animal_direct = cursor.fetchone()
    
    if animal_direct:
        print("\nAnimal encontrado con consulta directa:")
        print(f"ID: {animal_direct['id']}")
        print(f"Nombre: {animal_direct['nombre']}")
        print(f"Arete: {animal_direct['numero_arete']}")
        
        # Verificar si hay datos de padre y madre
        if 'padre_id' in animal_direct and animal_direct['padre_id']:
            cursor.execute("SELECT nombre, numero_arete FROM animales WHERE id = %s", 
                          (animal_direct['padre_id'],))
            padre = cursor.fetchone()
            if padre:
                print(f"Padre: {padre['nombre']} (Arete: {padre['numero_arete']})")
        
        if 'madre_id' in animal_direct and animal_direct['madre_id']:
            cursor.execute("SELECT nombre, numero_arete FROM animales WHERE id = %s", 
                          (animal_direct['madre_id'],))
            madre = cursor.fetchone()
            if madre:
                print(f"Madre: {madre['nombre']} (Arete: {madre['numero_arete']})")
    else:
        print("\nAnimal NO encontrado con consulta directa.")
    
    # Consulta completa (la que debería estar usando el sistema)
    print("\nProbando consulta JOIN completa:")
    try:
        cursor.execute("""
            SELECT a.*, 
                   m.nombre as nombre_madre, m.numero_arete as arete_madre,
                   p.nombre as nombre_padre, p.numero_arete as arete_padre
            FROM animales a
            LEFT JOIN animales m ON a.madre_id = m.id
            LEFT JOIN animales p ON a.padre_id = p.id
            WHERE a.id = %s
        """, (animal_id,))
        
        animal_join = cursor.fetchone()
        
        if animal_join:
            print(f"Animal encontrado con JOIN:")
            print(f"ID: {animal_join['id']}")
            print(f"Nombre: {animal_join['nombre']}")
            print(f"Arete: {animal_join['numero_arete']}")
            print(f"Nombre del padre: {animal_join.get('nombre_padre', 'No disponible')}")
            print(f"Nombre de la madre: {animal_join.get('nombre_madre', 'No disponible')}")
        else:
            print("Animal NO encontrado con JOIN.")
    except Exception as e:
        print(f"Error en la consulta JOIN: {e}")
    
    # Listado de todos los animales con ID y nombre
    print("\nListado de todos los animales disponibles:")
    cursor.execute("SELECT id, nombre, numero_arete FROM animales ORDER BY id")
    all_animals = cursor.fetchall()
    
    for a in all_animals:
        print(f"ID: {a['id']}, Nombre: {a['nombre']}, Arete: {a['numero_arete']}")
    
    cursor.close()
    conn.close()
except mysql.connector.Error as e:
    print(f"Error de MySQL: {e}")
except Exception as e:
    print(f"Error general: {e}")

# Información adicional de diagnóstico
print("\nEsta información debe ayudar a identificar por qué no se puede encontrar el animal.")
