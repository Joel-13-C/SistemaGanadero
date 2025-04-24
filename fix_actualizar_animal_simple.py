# Script simplificado para añadir la función actualizar_animal
import os

# Ruta al archivo de base de datos
db_path = os.path.join(os.getcwd(), 'src', 'database.py')

# Leer todo el contenido del archivo
with open(db_path, 'r', encoding='utf-8') as file:
    content = file.readlines()

# Buscar la posición donde insertar la función
insert_pos = -1
for i, line in enumerate(content):
    if line.strip().startswith("# Función de conexión a la base de datos"):
        insert_pos = i
        break

if insert_pos == -1:
    # Si no encuentra el comentario, buscar el final de la clase
    for i, line in enumerate(content):
        if line.strip() == "":
            next_line = content[i+1].strip() if i+1 < len(content) else ""
            if next_line.startswith("def get_db_connection"):
                insert_pos = i
                break

if insert_pos != -1:
    # Función actualizar_animal a añadir
    new_function = [
        "    def actualizar_animal(self, animal_id, datos_animal):\n",
        "        \"\"\"\n",
        "        Actualiza la información de un animal existente en la base de datos.\n",
        "        \n",
        "        Args:\n",
        "            animal_id: ID del animal a actualizar\n",
        "            datos_animal: Diccionario con los datos actualizados del animal\n",
        "            \n",
        "        Returns:\n",
        "            bool: True si la actualización fue exitosa, False en caso contrario\n",
        "        \"\"\"\n",
        "        try:\n",
        "            connection = self.get_connection()\n",
        "            with connection.cursor() as cursor:\n",
        "                # Construir la consulta SQL de actualización\n",
        "                update_query = \"\"\"\n",
        "                    UPDATE animales \n",
        "                    SET nombre = %s,\n",
        "                        numero_arete = %s,\n",
        "                        raza = %s,\n",
        "                        sexo = %s,\n",
        "                        condicion = %s,\n",
        "                        foto_path = %s,\n",
        "                        fecha_nacimiento = %s,\n",
        "                        propietario = %s,\n",
        "                        padre_arete = %s,\n",
        "                        madre_arete = %s\n",
        "                    WHERE id = %s\n",
        "                \"\"\"\n",
        "                \n",
        "                # Valores para la consulta\n",
        "                values = (\n",
        "                    datos_animal.get('nombre'),\n",
        "                    datos_animal.get('numero_arete'),\n",
        "                    datos_animal.get('raza'),\n",
        "                    datos_animal.get('sexo'),\n",
        "                    datos_animal.get('condicion'),\n",
        "                    datos_animal.get('foto_path'),\n",
        "                    datos_animal.get('fecha_nacimiento'),\n",
        "                    datos_animal.get('propietario'),\n",
        "                    datos_animal.get('padre_arete'),\n",
        "                    datos_animal.get('madre_arete'),\n",
        "                    animal_id\n",
        "                )\n",
        "                \n",
        "                # Ejecutar la consulta\n",
        "                cursor.execute(update_query, values)\n",
        "                connection.commit()\n",
        "                \n",
        "                logger.info(f\"Animal ID {animal_id} actualizado exitosamente\")\n",
        "                return True\n",
        "                \n",
        "        except mysql.connector.Error as err:\n",
        "            logger.error(f\"Error al actualizar animal: {err}\")\n",
        "            if connection:\n",
        "                connection.rollback()\n",
        "            return False\n",
        "\n"
    ]
    
    # Insertar la nueva función en el contenido
    new_content = content[:insert_pos] + new_function + content[insert_pos:]
    
    # Guardar el archivo actualizado
    with open(db_path, 'w', encoding='utf-8') as file:
        file.writelines(new_content)
    
    print("Se ha añadido la función actualizar_animal a la clase DatabaseConnection")
else:
    print("No se pudo encontrar la posición adecuada para añadir la función")
