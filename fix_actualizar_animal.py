# Script para añadir la función actualizar_animal a la clase DatabaseConnection
import os

# Ruta al archivo de base de datos
db_path = os.path.join(os.getcwd(), 'src', 'database.py')

# Leer todo el contenido del archivo
with open(db_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Buscar la última función de la clase DatabaseConnection para añadir después
last_function_pattern = "    def obtener_animales_por_usuario"
if last_function_pattern in content:
    index = content.find(last_function_pattern)
    # Buscar el final de esta función
    def_index = content.find("    def ", index + len(last_function_pattern))
    if def_index == -1:  # Si no hay más funciones después
        # Buscar el final de la clase
        def_index = content.find("# Función de conexión a la base de datos", index)
    
    # Función actualizar_animal a añadir
    new_function = """
    def actualizar_animal(self, animal_id, datos_animal):
        """
        Actualiza la información de un animal existente en la base de datos.
        
        Args:
            animal_id: ID del animal a actualizar
            datos_animal: Diccionario con los datos actualizados del animal
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                # Construir la consulta SQL de actualización
                update_query = """
                    UPDATE animales 
                    SET nombre = %s,
                        numero_arete = %s,
                        raza = %s,
                        sexo = %s,
                        condicion = %s,
                        foto_path = %s,
                        fecha_nacimiento = %s,
                        propietario = %s,
                        padre_arete = %s,
                        madre_arete = %s
                    WHERE id = %s
                """
                
                # Valores para la consulta
                values = (
                    datos_animal.get('nombre'),
                    datos_animal.get('numero_arete'),
                    datos_animal.get('raza'),
                    datos_animal.get('sexo'),
                    datos_animal.get('condicion'),
                    datos_animal.get('foto_path'),
                    datos_animal.get('fecha_nacimiento'),
                    datos_animal.get('propietario'),
                    datos_animal.get('padre_arete'),
                    datos_animal.get('madre_arete'),
                    animal_id
                )
                
                # Ejecutar la consulta
                cursor.execute(update_query, values)
                connection.commit()
                
                logger.info(f"Animal ID {animal_id} actualizado exitosamente")
                return True
                
        except mysql.connector.Error as err:
            logger.error(f"Error al actualizar animal: {err}")
            if connection:
                connection.rollback()
            return False
"""
    
    # Insertar la nueva función en el contenido
    new_content = content[:def_index] + new_function + content[def_index:]
    
    # Guardar el archivo actualizado
    with open(db_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    print("Se ha añadido la función actualizar_animal a la clase DatabaseConnection")
else:
    print("No se pudo encontrar el patrón de la última función para añadir la nueva función")
