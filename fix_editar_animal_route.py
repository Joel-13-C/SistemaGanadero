# Script para corregir el problema de la ruta de edición de animales
import re
import os

# Ruta al archivo app.py
app_path = os.path.join(os.getcwd(), 'app.py')

# Leer el contenido del archivo
with open(app_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Buscar la función editar_animal con una expresión regular
pattern = r'@app\.route\(\'/editar-animal/\<int:animal_id\>\', methods=\[\'GET\', \'POST\'\]\)[^@]*?def editar_animal\(animal_id\):[^@]*?flash\(\'Animal no encontrado[^@]*?return redirect\(url_for\(\'animales\'\)\)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # La función original que capturamos con regex
    original_func = match.group(0)
    
    # La nueva función con corrección
    new_func = '''@app.route('/editar-animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener el animal a editar sin verificar el usuario_id
    try:
        # No pasamos el usuario_id para permitir editar cualquier animal
        animal = db_connection.obtener_animal_por_id(animal_id)
        
        if not animal:
            flash('Animal no encontrado', 'error')
            return redirect(url_for('animales'))'''
    
    # Reemplazar la parte problemática de la función
    new_content = content.replace(original_func, new_func)
    
    # Guardar los cambios
    with open(app_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    print("Se ha corregido la función editar_animal en app.py")
else:
    print("No se pudo encontrar la función editar_animal en app.py")

print("Script de corrección completado")
