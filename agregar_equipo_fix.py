@app.route('/equipos/agregar', methods=['POST'])
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
    
    return redirect(url_for('equipos'))
