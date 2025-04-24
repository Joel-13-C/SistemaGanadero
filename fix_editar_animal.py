# Script para corregir el problema de edición de animales
import os

# Ruta a los archivos
app_path = os.path.join(os.getcwd(), 'app.py')
database_path = os.path.join(os.getcwd(), 'src', 'database.py')

# Corrección para database.py
with open(database_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Reemplazar la función obtener_animal_por_id
func_start = "    def obtener_animal_por_id"
func_end = "            return None"

new_func = '''    def obtener_animal_por_id(self, animal_id, usuario_id=None):
        """
        Obtiene un animal por su ID sin verificar el usuario.
        
        Args:
            animal_id: ID del animal a obtener
            usuario_id: ID del usuario (opcional, ya no se usa)
            
        Returns:
            Diccionario con la información del animal o None si no se encuentra
        """
        try:
            connection = self.get_connection()
            with connection.cursor(dictionary=True) as cursor:
                # Consulta SQL que no verifica el usuario_id
                cursor.execute("""
                    SELECT a.*, 
                           m.nombre as nombre_madre, m.numero_arete as arete_madre,
                           p.nombre as nombre_padre, p.numero_arete as arete_padre
                    FROM animales a
                    LEFT JOIN animales m ON a.madre_id = m.id
                    LEFT JOIN animales p ON a.padre_id = p.id
                    WHERE a.id = %s
                """, (animal_id,))
                
                return cursor.fetchone()
        
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener animal por ID: {err}")
            return None'''

# Buscar el índice de inicio y fin
start_idx = content.find(func_start)
if start_idx != -1:
    # Buscar el final de la función a partir del inicio
    remainder = content[start_idx:]
    end_idx = remainder.find(func_end)
    if end_idx != -1:
        # Ajustar el índice final
        end_idx = start_idx + end_idx + len(func_end)
        # Reemplazar la función
        new_content = content[:start_idx] + new_func + content[end_idx:]
        # Guardar los cambios
        with open(database_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print("Se ha actualizado la función obtener_animal_por_id en database.py")
    else:
        print("No se pudo encontrar el final de la función obtener_animal_por_id")
else:
    print("No se pudo encontrar la función obtener_animal_por_id")

print("Script de corrección completado")
