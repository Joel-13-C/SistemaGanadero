# Script para corregir completamente el archivo database.py
import os

# Ruta al archivo de base de datos
db_path = os.path.join(os.getcwd(), 'src', 'database.py')

# Leer todo el contenido del archivo
with open(db_path, 'r', encoding='utf-8') as file:
    content = file.readlines()

# Buscar la línea donde comienza la función obtener_animal_por_id
start_line = -1
for i, line in enumerate(content):
    if "def obtener_animal_por_id" in line:
        start_line = i
        break

if start_line >= 0:
    # Reemplazar todo el bloque de la función con la versión corregida
    new_function = [
        "    def obtener_animal_por_id(self, animal_id, usuario_id=None):\n",
        "        \"\"\"\n",
        "        Obtiene un animal por su ID sin verificar el usuario.\n",
        "        \n",
        "        Args:\n",
        "            animal_id: ID del animal a obtener\n",
        "            usuario_id: ID del usuario (opcional, ya no se usa)\n",
        "            \n",
        "        Returns:\n",
        "            Diccionario con la información del animal o None si no se encuentra\n",
        "        \"\"\"\n",
        "        try:\n",
        "            connection = self.get_connection()\n",
        "            with connection.cursor(dictionary=True) as cursor:\n",
        "                # Consulta simple que no usa JOIN (porque no hay relaciones por ID)\n",
        "                cursor.execute(\"SELECT * FROM animales WHERE id = %s\", (animal_id,))\n",
        "                animal = cursor.fetchone()\n",
        "                \n",
        "                if animal:\n",
        "                    # Si el animal tiene referencias a padre o madre por arete, podemos buscar sus nombres\n",
        "                    if animal.get('padre_arete'):\n",
        "                        cursor.execute(\"SELECT nombre FROM animales WHERE numero_arete = %s\", \n",
        "                                      (animal['padre_arete'],))\n",
        "                        padre = cursor.fetchone()\n",
        "                        if padre:\n",
        "                            animal['nombre_padre'] = padre['nombre']\n",
        "                    \n",
        "                    if animal.get('madre_arete'):\n",
        "                        cursor.execute(\"SELECT nombre FROM animales WHERE numero_arete = %s\", \n",
        "                                      (animal['madre_arete'],))\n",
        "                        madre = cursor.fetchone()\n",
        "                        if madre:\n",
        "                            animal['nombre_madre'] = madre['nombre']\n",
        "                \n",
        "                return animal\n",
        "                \n",
        "        except mysql.connector.Error as err:\n",
        "            logger.error(f\"Error al obtener animal por ID: {err}\")\n",
        "            return None\n"
    ]
    
    # Encontrar el final de la función actual
    end_line = start_line + 1
    bracket_count = 0
    in_function = True
    
    # Saltamos manualmente hasta la siguiente función o método
    while end_line < len(content) and in_function:
        line = content[end_line]
        if "def " in line and line.strip().startswith("def "):
            in_function = False
            break
        end_line += 1
    
    # Reemplazar las líneas del archivo
    new_content = content[:start_line] + new_function + content[end_line:]
    
    # Guardar el archivo corregido
    with open(db_path, 'w', encoding='utf-8') as file:
        file.writelines(new_content)
    
    print(f"Se ha corregido la función obtener_animal_por_id en {db_path}")
else:
    print("No se encontró la función obtener_animal_por_id en el archivo database.py")
