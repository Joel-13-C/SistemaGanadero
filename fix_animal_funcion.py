# Script para corregir definitivamente la función obtener_animal_por_id
import re
import os

# Ruta al archivo de base de datos
db_path = os.path.join(os.getcwd(), 'src', 'database.py')

# Leer el contenido del archivo
with open(db_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Función corrregida que funciona con la estructura real de la tabla
new_function = '''    def obtener_animal_por_id(self, animal_id, usuario_id=None):
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
                # Consulta simple que no usa JOIN (porque no hay relaciones por ID)
                cursor.execute("SELECT * FROM animales WHERE id = %s", (animal_id,))
                animal = cursor.fetchone()
                
                if animal:
                    # Si el animal tiene referencias a padre o madre por arete, podemos buscar sus nombres
                    if animal.get('padre_arete'):
                        cursor.execute("SELECT nombre FROM animales WHERE numero_arete = %s", 
                                      (animal['padre_arete'],))
                        padre = cursor.fetchone()
                        if padre:
                            animal['nombre_padre'] = padre['nombre']
                    
                    if animal.get('madre_arete'):
                        cursor.execute("SELECT nombre FROM animales WHERE numero_arete = %s", 
                                      (animal['madre_arete'],))
                        madre = cursor.fetchone()
                        if madre:
                            animal['nombre_madre'] = madre['nombre']
                
                return animal
                
        except mysql.connector.Error as err:
            logger.error(f"Error al obtener animal por ID: {err}")
            return None'''

# Usar una expresión regular para buscar y reemplazar la función completa
pattern = r'def obtener_animal_por_id\(self, animal_id.*?return None'
replacement = new_function

# Realizar el reemplazo
new_content = re.sub(pattern, new_function, content, flags=re.DOTALL)

# Guardar el nuevo contenido
with open(db_path, 'w', encoding='utf-8') as file:
    file.write(new_content)

print("Función obtener_animal_por_id corregida con éxito para trabajar con la estructura real de la tabla.")
