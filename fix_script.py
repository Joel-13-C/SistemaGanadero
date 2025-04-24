import re

# Función corregida
fixed_function = '''@app.route('/equipos/agregar', methods=['POST'])
@login_required
def agregar_equipo():
    # Inicializar las variables db y cursor fuera del bloque try
    db = None
    cursor = None
    
    try:
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        marca = request.form.get('marca', '')
        modelo = request.form.get('modelo', '')
        estado = request.form['estado']
        fecha_adquisicion = request.form['fecha_adquisicion']
        costo = request.form.get('costo', 0)
        ubicacion = request.form.get('ubicacion', '')
        observaciones = request.form.get('observaciones', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO equipos (
                nombre, tipo, marca, modelo, estado, 
                fecha_adquisicion, costo, ubicacion, observaciones
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, tipo, marca, modelo, estado, 
              fecha_adquisicion, costo, ubicacion, observaciones))
        
        db.commit()
        flash('Equipo agregado exitosamente', 'success')
        
    except Exception as e:
        if db:
            db.rollback()
        flash(f'Error al agregar el equipo: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
    
    return redirect(url_for('equipos'))'''

# Leer el archivo original
with open('app.py', 'r', encoding='utf-8') as file:
    content = file.read()

# Patrón para encontrar la función agregar_equipo
pattern = r'@app\.route\(\'/equipos/agregar\', methods=\[\'POST\'\]\)\s*@login_required\s*def agregar_equipo\(\):.*?return redirect\(url_for\(\'equipos\'\)\)'
# Usamos re.DOTALL para que el punto coincida con saltos de línea
pattern_compiled = re.compile(pattern, re.DOTALL)

# Reemplazar la función
new_content = pattern_compiled.sub(fixed_function, content)

# Escribir el nuevo contenido al archivo
with open('app.py', 'w', encoding='utf-8') as file:
    file.write(new_content)

print("La función agregar_equipo ha sido corregida exitosamente.")
