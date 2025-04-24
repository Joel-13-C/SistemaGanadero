from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from src.database import DatabaseConnection, get_db_connection
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
import re
from werkzeug.utils import secure_filename
import qrcode
import json
import io
import base64
from functools import wraps
import uuid
import logging
from logging.handlers import RotatingFileHandler
from src.chatbot import GanaderiaChatbot
from src.gestacion import registrar_gestacion, obtener_gestaciones, actualizar_estado_gestacion, obtener_gestaciones_proximas

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)  # Clave secreta para sesiones

# Configuración del sistema de registro
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Iniciando Sistema Ganadero')

# Inicializar conexión de base de datos
try:
    db_connection = DatabaseConnection(app)
except Exception as e:
    app.logger.error(f"Error fatal al inicializar la base de datos: {e}")
    # Podrías mostrar una página de error o salir de la aplicación
    # sys.exit(1)  # Descomentar si quieres salir de la aplicación

# Inicializar chatbot
chatbot = GanaderiaChatbot(db_connection)

# Configuración de carga de archivos
UPLOAD_FOLDER = 'static/uploads/animales'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configuración de carga de imagen de perfil
UPLOAD_FOLDER_PERFIL = 'static/uploads/perfiles'
ALLOWED_EXTENSIONS_PERFIL = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file_perfil(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_PERFIL

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor inicia sesión para acceder a esta página', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def inicio():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    return render_template('inicio.html')

@app.route('/login')
def login():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    return render_template('login.html')

@app.route('/autenticar', methods=['POST'])
def autenticar():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    username = request.form['username']
    password = request.form['password']
    
    user = db_connection.validate_user(username, password)
    if user:
        # Redirigir a la página principal del sistema
        session['username'] = username
        session['usuario_id'] = user['id']  # Guardar el ID de usuario en la sesión
        return redirect(url_for('dashboard'))
    else:
        flash('Credenciales incorrectas', 'error')
        return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validaciones adicionales del lado del servidor
        if len(username) < 3:
            flash('El nombre de usuario debe tener al menos 3 caracteres', 'error')
            return render_template('registro.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Por favor, introduce un correo electrónico válido', 'error')
            return render_template('registro.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('registro.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        if db_connection.register_user(username, email, password):
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error en el registro. El usuario o correo ya existe.', 'error')
    
    return render_template('registro.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Obtener gestaciones próximas al parto
        gestaciones_proximas = obtener_gestaciones_proximas()
        
        # Obtener estadísticas actuales (si las hay)
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Contar total de animales
        cursor.execute("SELECT COUNT(*) as total FROM animales")
        total_animales = cursor.fetchone()['total']
        
        # Contar por sexo
        cursor.execute("""
            SELECT sexo, COUNT(*) as cantidad 
            FROM animales 
            GROUP BY sexo
        """)
        conteo_por_sexo = cursor.fetchall()
        
        # Contar gestaciones activas
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM gestacion 
            WHERE estado = 'En Gestación'
        """)
        gestaciones_activas = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html',
                             gestaciones_proximas=gestaciones_proximas,
                             total_animales=total_animales,
                             conteo_por_sexo=conteo_por_sexo,
                             gestaciones_activas=gestaciones_activas)
    except Exception as e:
        flash(f'Error al cargar el dashboard: {str(e)}', 'error')
        return render_template('dashboard.html')

@app.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    if request.method == 'POST':
        email = request.form['email']
        
        # Validar formato de correo electrónico
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Por favor, introduce un correo electrónico válido', 'error')
            return render_template('recuperar_contrasena.html')
        
        # Verificar si el correo existe en la base de datos
        if db_connection.email_exists(email):
            # Aquí podrías implementar la lógica de envío de correo de recuperación
            # Por ahora, solo mostraremos un mensaje de éxito
            flash('Se ha enviado un correo de recuperación a tu email', 'success')
            return redirect(url_for('login'))
        else:
            flash('No se encontró ninguna cuenta con este correo electrónico', 'error')
    
    return render_template('recuperar_contrasena.html')

@app.route('/animales')
def animales():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener el ID del usuario de la sesión
    usuario_id = session.get('usuario_id')
    
    if not usuario_id:
        flash('No se pudo identificar al usuario', 'error')
        return redirect(url_for('login'))
    
    # Obtener la lista de animales del usuario
    animales = db_connection.obtener_animales(usuario_id)
    
    return render_template('animales.html', animales=animales)

@app.route('/registrar-animal', methods=['GET', 'POST'])
def registrar_animal():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Obtener datos del formulario
        datos_animal = {
            'numero_arete': request.form['numero_arete'],
            'nombre': request.form['nombre'],
            'sexo': request.form['sexo'],
            'raza': request.form['raza'],
            'condicion': request.form['condicion'],
            'fecha_nacimiento': request.form['fecha_nacimiento'],
            'propietario': request.form['propietario'],
            'padre_arete': request.form.get('padre_arete', None),
            'madre_arete': request.form.get('madre_arete', None),
            'usuario_id': session.get('usuario_id')
        }
        
        # Manejar la carga de la foto
        foto = request.files['foto']
        if foto and allowed_file(foto.filename):
            # Generar un nombre de archivo único
            filename = str(uuid.uuid4()) + '.' + foto.filename.rsplit('.', 1)[1].lower()
            
            # Asegurar que el directorio exista
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Guardar el archivo
            foto.save(filepath)
            
            # Ruta para la base de datos
            datos_animal['foto_path'] = f'uploads/animales/{filename}'
        else:
            # Si no se sube imagen, usar imagen de marcador de posición
            datos_animal['foto_path'] = 'images/upload-image-placeholder.svg'
            app.logger.error("No se subió imagen, usando marcador de posición")
        
        # Registrar el animal
        resultado = db_connection.registrar_animal(datos_animal)
        
        if resultado:
            flash('Animal registrado exitosamente', 'success')
            return redirect(url_for('animales'))
        else:
            flash('Error al registrar el animal', 'error')
    
    return render_template('registrar_animal.html')

@app.route('/editar-animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener el animal a editar
    try:
        usuario_id = session.get('usuario_id')
        animal = db_connection.obtener_animal_por_id(animal_id, usuario_id)
        
        if not animal:
            flash('Animal no encontrado o no tienes permiso para editarlo', 'error')
            return redirect(url_for('animales'))
        
        # Normalizar la ruta de la imagen
        if animal['foto_path']:
            # Si la ruta no comienza con 'static/', agregarla
            if not animal['foto_path'].startswith('static/'):
                animal['foto_path'] = f'static/{animal["foto_path"]}'
        else:
            # Usar imagen de marcador de posición
            animal['foto_path'] = 'static/images/upload-image-placeholder.svg'
        
        if request.method == 'POST':
            # Procesar el formulario de edición
            datos_animal = {
                'nombre': request.form.get('nombre'),
                'numero_arete': request.form.get('numero_arete'),
                'raza': request.form.get('raza'),
                'sexo': request.form.get('sexo'),
                'condicion': request.form.get('condicion'),
                'foto_path': animal['foto_path'],
                'fecha_nacimiento': request.form.get('fecha_nacimiento'),
                'propietario': request.form.get('propietario'),
                'padre_arete': request.form.get('padre_arete'),
                'madre_arete': request.form.get('madre_arete')
            }
            
            # Actualizar foto si se proporciona
            foto = request.files.get('foto')
            if foto and allowed_file(foto.filename):
                filename = secure_filename(foto.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                foto.save(filepath)
                datos_animal['foto_path'] = f'static/uploads/animales/{filename}'
            
            # Llamar al método de actualización en la base de datos
            try:
                db_connection.actualizar_animal(animal_id, datos_animal)
                return jsonify({
                    'success': True,
                    'message': 'Animal actualizado exitosamente'
                })
            except Exception as e:
                app.logger.error(f'Error al actualizar el animal: {str(e)}')
                return jsonify({
                    'success': False,
                    'message': f'Error al actualizar el animal: {str(e)}'
                })
        
        return render_template('editar_animal.html', animal=animal)
    
    except Exception as e:
        app.logger.error(f'Error al editar el animal: {str(e)}')
        flash(f'Error al editar el animal: {str(e)}', 'error')
        return redirect(url_for('animales'))

@app.route('/eliminar-animal/<int:animal_id>', methods=['GET'])
def eliminar_animal(animal_id):
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    # Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    try:
        # Obtener el ID de usuario de la sesión
        usuario_id = session.get('usuario_id')
        
        # Eliminar el animal de la base de datos
        db_connection.eliminar_animal(animal_id, usuario_id)
        
        flash('Animal eliminado exitosamente', 'success')
        return redirect(url_for('animales'))
    
    except Exception as e:
        app.logger.error(f'Error al eliminar el animal: {str(e)}')
        flash(f'Error al eliminar el animal: {str(e)}', 'error')
        return redirect(url_for('animales'))

@app.route('/configuracion')
def configuracion():
    app.logger.debug(f'Ruta solicitada: {request.path}, Método: {request.method}')
    
    # Verificar si el usuario está logueado
    if 'username' not in session:
        app.logger.warning(f'Intento de acceso a configuración sin sesión desde {request.path}')
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    # Obtener información del usuario actual
    usuario_id = session.get('usuario_id')
    
    try:
        app.logger.info(f'Accediendo a configuración para usuario {usuario_id} desde {request.path}')
        
        # Obtener información adicional del usuario
        try:
            # Ejemplo de cómo podrías obtener información adicional
            # usuario = db_connection.obtener_informacion_usuario(usuario_id)
            usuario = {
                'id': usuario_id,
                'nombre': session.get('username', 'Usuario'),
                'email': session.get('email', 'Sin correo')
            }
        except Exception as e:
            app.logger.warning(f'No se pudo obtener información adicional del usuario: {e}')
            usuario = {}
        
        return render_template('configuracion.html', usuario=usuario)
    
    except Exception as e:
        # Manejar cualquier error que pueda ocurrir
        app.logger.error(f"Error en la página de configuración: {e}")
        flash('Ocurrió un error al cargar la configuración', 'error')
        return redirect(url_for('dashboard'))

@app.route('/perfil/editar', methods=['GET', 'POST'])
def editar_perfil():
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    usuario_id = session.get('usuario_id')
    
    try:
        # Obtener información actual del usuario desde la base de datos
        usuario = db_connection.obtener_usuario_por_id(usuario_id)
        
        if request.method == 'POST':
            # Procesar formulario de edición de perfil
            nombre = request.form.get('nombre')
            telefono = request.form.get('telefono')
            
            # Manejar carga de imagen de perfil
            foto_perfil = request.files.get('foto_perfil')
            foto_path = None
            
            if foto_perfil and allowed_file_perfil(foto_perfil.filename):
                filename = secure_filename(f"{usuario_id}_{foto_perfil.filename}")
                filepath = os.path.join(app.root_path, UPLOAD_FOLDER_PERFIL, filename)
                
                # Crear directorio si no existe
                os.makedirs(os.path.join(app.root_path, UPLOAD_FOLDER_PERFIL), exist_ok=True)
                
                foto_perfil.save(filepath)
                foto_path = f'/static/uploads/perfiles/{filename}'
                
                # Guardar foto en sesión
                session['foto_perfil'] = foto_path
            
            # Actualizar información en la base de datos
            db_connection.actualizar_perfil_usuario(usuario_id, nombre, telefono, foto_path)
            
            # Actualizar sesión
            session['nombre'] = nombre
            
            flash('Perfil actualizado exitosamente', 'success')
            return redirect(url_for('configuracion'))
        
        # Cargar foto de perfil de la sesión si existe
        usuario['foto_perfil'] = session.get('foto_perfil', '/static/images/default-avatar.png')
        
        return render_template('editar_perfil.html', usuario=usuario)
    
    except Exception as e:
        app.logger.error(f"Error al editar perfil: {e}")
        flash('Ocurrió un error al editar el perfil', 'error')
        return redirect(url_for('configuracion'))

@app.route('/perfil/cambiar-contrasena', methods=['GET', 'POST'])
def cambiar_contrasena():
    if 'username' not in session:
        flash('Debes iniciar sesión primero', 'error')
        return redirect(url_for('login'))
    
    usuario_id = session.get('usuario_id')
    
    try:
        if request.method == 'POST':
            contrasena_actual = request.form.get('contrasena_actual')
            nueva_contrasena = request.form.get('nueva_contrasena')
            confirmar_contrasena = request.form.get('confirmar_contrasena')
            
            # Validar contraseñas
            if nueva_contrasena != confirmar_contrasena:
                flash('Las contraseñas no coinciden', 'error')
                return redirect(url_for('cambiar_contrasena'))
            
            # Verificar contraseña actual
            usuario = db_connection.obtener_usuario_por_id(usuario_id)
            if not db_connection.check_password_hash(usuario['password'], contrasena_actual):
                flash('Contraseña actual incorrecta', 'error')
                return redirect(url_for('cambiar_contrasena'))
            
            # Hashear nueva contraseña
            nueva_contrasena_hash = db_connection.generate_password_hash(nueva_contrasena)
            
            # Actualizar contraseña en la base de datos
            db_connection.actualizar_contrasena_usuario(usuario_id, nueva_contrasena_hash)
            
            flash('Contraseña cambiada exitosamente', 'success')
            return redirect(url_for('configuracion'))
        
        return render_template('cambiar_contrasena.html')
    
    except Exception as e:
        app.logger.error(f"Error al cambiar contraseña: {e}")
        flash('Ocurrió un error al cambiar la contraseña', 'error')
        return redirect(url_for('configuracion'))

@app.route('/generar-qr', methods=['GET', 'POST'])
def generar_qr():
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        if not identificador:
            flash('Por favor, ingresa un identificador de animal', 'error')
            return render_template('generar_qr.html')
        
        # Aquí iría la lógica para buscar el animal
        usuario_id = session.get('usuario_id')
        animal = db_connection.buscar_animal_por_identificador(identificador, usuario_id)
        
        if not animal:
            flash('No se encontró ningún animal con ese identificador', 'error')
            return render_template('generar_qr.html')
        
        # Preparar datos para el código QR
        datos_qr = f"""Información del Animal
Finca: {animal.get('nombre_finca', 'Sin información')}
Propietario: {animal.get('propietario', 'Sin información')}
ID: {animal.get('id', 'N/A')}
Número de Arete: {animal.get('numero_arete', 'N/A')}
Nombre: {animal.get('nombre', 'N/A')}
Sexo: {animal.get('sexo', 'N/A')}
Raza: {animal.get('raza', 'N/A')}
Condición: {animal.get('condicion', 'N/A')}
Fecha de Nacimiento: {animal.get('fecha_nacimiento', 'N/A')}
"""
        
        # Generar código QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(datos_qr)
        qr.make(fit=True)
        
        # Crear imagen del código QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar imagen en un buffer de bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        
        # Convertir a base64 para mostrar en HTML
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return render_template('generar_qr.html', imagen_qr=imagen_base64, animal=animal)
    
    return render_template('generar_qr.html')

@app.route('/gestacion')
@login_required
def gestacion():
    # Obtener solo animales hembra (vacas y vaconas)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, nombre, numero_arete, condicion 
        FROM animales 
        WHERE sexo = 'Hembra' 
        AND condicion IN ('Vaca', 'Vacona')
        ORDER BY nombre
    """)
    animales = cursor.fetchall()
    cursor.close()
    conn.close()

    # Obtener todas las gestaciones
    gestaciones = obtener_gestaciones()
    
    return render_template('gestacion.html', animales=animales, gestaciones=gestaciones)

@app.route('/registrar_gestacion', methods=['POST'])
@login_required
def registrar_gestacion_route():
    animal_id = request.form.get('animal_id')
    fecha_monta = request.form.get('fecha_monta')
    observaciones = request.form.get('observaciones')
    
    success, message = registrar_gestacion(
        animal_id=animal_id,
        fecha_monta=fecha_monta,
        observaciones=observaciones,
        usuario_id=session['usuario_id']
    )
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('gestacion'))

@app.route('/actualizar_estado_gestacion', methods=['POST'])
@login_required
def actualizar_estado_gestacion_route():
    data = request.get_json()
    gestacion_id = data.get('gestacion_id')
    nuevo_estado = data.get('estado')
    observaciones = data.get('observaciones')
    
    success, message = actualizar_estado_gestacion(
        gestacion_id=gestacion_id,
        nuevo_estado=nuevo_estado,
        observaciones=observaciones
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/chatbot', methods=['POST'])
def chatbot_endpoint():
    if 'username' not in session:
        return jsonify({"error": "No autorizado"}), 401
    
    try:
        mensaje = request.json.get('mensaje', '')
        usuario_id = session.get('usuario_id')
        
        if not mensaje:
            return jsonify({"error": "Mensaje vacío"}), 400
        
        respuesta = chatbot.generar_respuesta(mensaje, usuario_id)
        
        return jsonify({
            "respuesta": respuesta
        })
    
    except Exception as e:
        app.logger.error(f'Error al procesar mensaje del chatbot: {str(e)}')
        return jsonify({"error": "Error al procesar mensaje"}), 500

@app.route('/vacunas')
@login_required
def vacunas():
    return render_template('vacunas.html')

@app.route('/desparasitacion')
@login_required
def desparasitacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(d.fecha_registro) 
                    FROM desparasitacion d 
                    JOIN desparasitacion_animal da ON d.id = da.desparasitacion_id 
                    WHERE da.animal_id = a.id) as ultima_desparasitacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de desparasitación
        cursor.execute("""
            SELECT d.*, 
                   (SELECT COUNT(*) 
                    FROM desparasitacion_animal da 
                    WHERE da.desparasitacion_id = d.id) as cantidad_animales
            FROM desparasitacion d
            ORDER BY d.fecha_registro DESC
        """)
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('desparasitacion.html', 
                             animales=animales, 
                             registros=registros,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de desparasitación: {str(e)}')
        flash('Error al cargar la página de desparasitación', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/registrar_desparasitacion', methods=['POST'])
@login_required
def registrar_desparasitacion():
    try:
        fecha_registro = request.form['fecha_registro']
        producto = request.form['producto']
        if producto == 'Otro':
            producto = request.form['otro_producto']
        tipo_aplicacion = request.form['tipo_aplicacion']
        vacunador = request.form['vacunador']
        
        # Calcular próxima aplicación (3 meses después)
        fecha_registro_dt = datetime.strptime(fecha_registro, '%Y-%m-%d')
        proxima_aplicacion = fecha_registro_dt + timedelta(days=90)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertar registro de desparasitación
        cursor.execute("""
            INSERT INTO desparasitacion 
            (fecha_registro, producto, aplicacion_general, vacunador, proxima_aplicacion)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha_registro, producto, tipo_aplicacion == 'general', vacunador, proxima_aplicacion.strftime('%Y-%m-%d')))
        
        desparasitacion_id = cursor.lastrowid
        
        # Relacionar con animales
        if tipo_aplicacion == 'general':
            # Aplicar a todos los animales
            cursor.execute("""
                INSERT INTO desparasitacion_animal (desparasitacion_id, animal_id)
                SELECT %s, id FROM animales
            """, (desparasitacion_id,))
        else:
            # Aplicar solo a los animales seleccionados
            animales_seleccionados = request.form.getlist('animales_seleccionados[]')
            for animal_id in animales_seleccionados:
                cursor.execute("""
                    INSERT INTO desparasitacion_animal (desparasitacion_id, animal_id)
                    VALUES (%s, %s)
                """, (desparasitacion_id, animal_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Registro de desparasitación guardado exitosamente', 'success')
        return redirect(url_for('desparasitacion'))
    except Exception as e:
        cursor.close()
        conn.close()
        app.logger.error(f'Error al registrar desparasitación: {str(e)}')
        flash('Error al registrar la desparasitación', 'danger')
        return redirect(url_for('desparasitacion'))

@app.route('/desparasitacion/detalles/<int:id>')
@login_required
def detalles_desparasitacion(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener detalles del registro
        cursor.execute("""
            SELECT d.*, 
                   DATE_FORMAT(d.fecha_registro, '%d/%m/%Y') as fecha_registro_formato,
                   DATE_FORMAT(d.proxima_aplicacion, '%d/%m/%Y') as proxima_aplicacion_formato
            FROM desparasitacion d
            WHERE d.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        # Formatear fechas
        registro['fecha_registro'] = registro['fecha_registro_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        # Obtener animales relacionados
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN desparasitacion_animal da ON a.id = da.animal_id
            WHERE da.desparasitacion_id = %s
        """, (id,))
        animales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(registro)
        
    except Exception as e:
        app.logger.error(f'Error al obtener detalles de desparasitación: {str(e)}')
        return jsonify({'error': 'Error al obtener detalles'}), 500

@app.route('/menu')
def menu():
    return render_template('menu.html')

@app.route('/menu/desparasitacion')
@login_required
def menu_desparasitacion():
    return render_template('menu_desparasitacion.html')

@app.route('/obtener_cantones/<int:provincia_id>')
def obtener_cantones(provincia_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si la provincia existe
        cursor.execute("SELECT id FROM provincias WHERE id = %s", (provincia_id,))
        provincia = cursor.fetchone()
        
        if not provincia:
            app.logger.error(f'Provincia no encontrada: {provincia_id}')
            return jsonify({'error': 'Provincia no encontrada'}), 404
        
        # Obtener cantones
        cursor.execute("""
            SELECT id, nombre 
            FROM cantones 
            WHERE provincia_id = %s 
            ORDER BY nombre
        """, (provincia_id,))
        cantones = cursor.fetchall()
        app.logger.info(f'Cantones encontrados para provincia {provincia_id}: {cantones}')
        
        cursor.close()
        conn.close()
        
        return jsonify(cantones)
    
    except Exception as e:
        app.logger.error(f'Error al obtener cantones: {str(e)}')
        return jsonify({'error': 'Error al obtener cantones'}), 500

@app.route('/obtener_parroquias/<int:canton_id>')
def obtener_parroquias(canton_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el cantón existe
        cursor.execute("SELECT id FROM cantones WHERE id = %s", (canton_id,))
        canton = cursor.fetchone()
        
        if not canton:
            app.logger.error(f'Cantón no encontrado: {canton_id}')
            return jsonify({'error': 'Cantón no encontrado'}), 404
        
        # Obtener parroquias
        cursor.execute("""
            SELECT id, nombre 
            FROM parroquias 
            WHERE canton_id = %s 
            ORDER BY nombre
        """, (canton_id,))
        parroquias = cursor.fetchall()
        app.logger.info(f'Parroquias encontradas para cantón {canton_id}: {parroquias}')
        
        cursor.close()
        conn.close()
        
        return jsonify(parroquias)
    
    except Exception as e:
        app.logger.error(f'Error al obtener parroquias: {str(e)}')
        return jsonify({'error': 'Error al obtener parroquias'}), 500

@app.route('/registrar_fiebre_aftosa', methods=['POST'])
@login_required
def registrar_fiebre_aftosa():
    conn = None
    cursor = None
    try:
        # Obtener datos del formulario
        fecha_registro = request.form['fecha_registro']
        numero_certificado = request.form['numero_certificado']
        nombre_propietario = request.form['propietario_nombre']
        identificacion = request.form['propietario_documento']
        nombre_predio = request.form['nombre_predio']
        provincia_id = request.form['provincia_id']
        canton_id = request.form['canton_id']
        parroquia_id = request.form['parroquia_id']
        tipo_explotacion = request.form['tipo_explotacion']
        vacunador_nombre = request.form['vacunador_nombre']
        vacunador_cedula = request.form['vacunador_cedula']
        tipo_aplicacion = request.form['tipo_aplicacion']
        
        app.logger.info(f'Datos recibidos: fecha={fecha_registro}, cert={numero_certificado}, prop={nombre_propietario}')
        
        # Calcular próxima aplicación (6 meses después)
        fecha_registro_obj = datetime.strptime(fecha_registro, '%Y-%m-%d')
        proxima_aplicacion = fecha_registro_obj + relativedelta(months=6)
        
        app.logger.info(f'Próxima aplicación calculada: {proxima_aplicacion}')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Insertar registro de fiebre aftosa
            insert_query = """
                INSERT INTO fiebre_aftosa (
                    fecha_registro, numero_certificado, nombre_propietario,
                    identificacion, nombre_predio, provincia_id, canton_id,
                    parroquia_id, tipo_explotacion, nombre_vacunador,
                    cedula_vacunador, fecha_proxima_aplicacion,
                    usuario_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                fecha_registro, numero_certificado, nombre_propietario,
                identificacion, nombre_predio, provincia_id, canton_id,
                parroquia_id, tipo_explotacion, vacunador_nombre,
                vacunador_cedula, proxima_aplicacion, session['usuario_id']
            )
            
            app.logger.info(f'Ejecutando query: {insert_query}')
            app.logger.info(f'Con valores: {values}')
            
            cursor.execute(insert_query, values)
            fiebre_aftosa_id = cursor.lastrowid
            
            app.logger.info(f'Registro insertado con ID: {fiebre_aftosa_id}')

            # Registrar animales vacunados
            if tipo_aplicacion == 'general':
                app.logger.info('Aplicando vacunación general')
                # Aplicar a todos los animales
                cursor.execute("""
                    INSERT INTO fiebre_aftosa_animal (fiebre_aftosa_id, animal_id)
                    SELECT %s, id FROM animales
                """, (fiebre_aftosa_id,))
            else:
                app.logger.info('Aplicando vacunación específica')
                # Aplicar solo a los animales seleccionados
                animales_seleccionados = request.form.getlist('animales_seleccionados[]')
                app.logger.info(f'Animales seleccionados: {animales_seleccionados}')
                for animal_id in animales_seleccionados:
                    cursor.execute("""
                        INSERT INTO fiebre_aftosa_animal (fiebre_aftosa_id, animal_id)
                        VALUES (%s, %s)
                    """, (fiebre_aftosa_id, animal_id))
        
            conn.commit()
            app.logger.info('Transacción completada exitosamente')
            flash('Vacunación registrada exitosamente', 'success')
            return redirect(url_for('fiebre_aftosa'))
        
        except Exception as e:
            if conn:
                conn.rollback()
            app.logger.error(f'Error al guardar el registro: {str(e)}')
            app.logger.error(f'Tipo de error: {type(e).__name__}')
            flash(f'Error al guardar el registro: {str(e)}', 'danger')
            return redirect(url_for('fiebre_aftosa'))

    except Exception as e:
        app.logger.error(f'Error al registrar vacunación: {str(e)}')
        app.logger.error(f'Tipo de error: {type(e).__name__}')
        flash(f'Error al registrar la vacunación: {str(e)}', 'danger')
        return redirect(url_for('fiebre_aftosa'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/detalles_fiebre_aftosa/<int:id>')
@login_required
def detalles_fiebre_aftosa(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener detalles de la vacunación
        cursor.execute("""
            SELECT fa.*, 
                   p.nombre as provincia,
                   c.nombre as canton,
                   pa.nombre as parroquia
            FROM fiebre_aftosa fa
            JOIN provincias p ON fa.provincia_id = p.id
            JOIN cantones c ON fa.canton_id = c.id
            JOIN parroquias pa ON fa.parroquia_id = pa.id
            WHERE fa.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            flash('Registro no encontrado', 'danger')
            return redirect(url_for('fiebre_aftosa'))
        
        # Obtener animales vacunados
        cursor.execute("""
            SELECT a.numero_arete, a.nombre, a.condicion
            FROM animales a
            JOIN fiebre_aftosa_animal faa ON a.id = faa.animal_id
            WHERE faa.fiebre_aftosa_id = %s
            ORDER BY a.numero_arete
        """, (id,))
        animales = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('ver_registro_fiebre_aftosa.html', registro=registro, animales=animales)
        
    except Exception as e:
        app.logger.error(f'Error al obtener detalles de vacunación: {str(e)}')
        flash(f'Error al obtener detalles: {str(e)}', 'danger')
        return redirect(url_for('fiebre_aftosa'))

@app.route('/pastizales')
@login_required
def pastizales():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener todos los pastizales del usuario
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
            WHERE p.usuario_id = %s
            GROUP BY p.id
        """, (session['usuario_id'],))
        
        pastizales = cursor.fetchall()
        
        return render_template('pastizales.html', pastizales=pastizales)
    
    except Exception as e:
        flash(f'Error al cargar los pastizales: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/registrar_pastizal', methods=['POST'])
@login_required
def registrar_pastizal():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        nombre = request.form['nombre']
        dimension = float(request.form['dimension'])
        tipo_hierba = request.form['tipo_hierba']
        
        cursor.execute("""
            INSERT INTO pastizales (
                nombre, dimension, tipo_hierba, estado, usuario_id
            ) VALUES (%s, %s, %s, 'Disponible', %s)
        """, (nombre, dimension, tipo_hierba, session['usuario_id']))
        
        conn.commit()
        flash('Pastizal registrado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al registrar el pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/obtener_animales_disponibles/<int:pastizal_id>')
@login_required
def obtener_animales_disponibles(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener información del pastizal
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            return jsonify({'error': 'Pastizal no encontrado'}), 404
        
        # Obtener animales disponibles
        cursor.execute("""
            SELECT a.id, a.nombre, a.categoria, a.estado
            FROM animales a
            LEFT JOIN pastizales_animales pa ON a.id = pa.animal_id
            WHERE pa.id IS NULL
                AND a.usuario_id = %s
                AND a.estado = 'Activo'
            ORDER BY a.nombre
        """, (session['usuario_id'],))
        animales = cursor.fetchall()
        
        return jsonify({
            'capacidad_maxima': pastizal['capacidad_maxima'],
            'animales_actuales': pastizal['animales_actuales'] or 0,
            'animales': animales
        })
        
    except Exception as e:
        app.logger.error(f"Error al obtener datos del pastizal: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/asignar_animales/<int:pastizal_id>', methods=['POST'])
@login_required
def asignar_animales(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        animales = request.form.getlist('animales[]')
        fecha_actual = datetime.now().date()
        
        # Verificar capacidad y animales actuales
        cursor.execute("""
            SELECT p.capacidad_maxima,
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id, p.capacidad_maxima
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            flash('Pastizal no encontrado', 'danger')
            return redirect(url_for('pastizales'))
        
        capacidad_maxima = pastizal[0]
        animales_actuales = pastizal[1] or 0
        
        if len(animales) + animales_actuales > capacidad_maxima:
            flash(f'No se pueden asignar más de {capacidad_maxima} animales a este pastizal', 'danger')
            return redirect(url_for('pastizales'))
        
        # Actualizar estado del pastizal
        cursor.execute("""
            UPDATE pastizales 
            SET estado = 'En uso',
                fecha_ultimo_uso = %s
            WHERE id = %s AND usuario_id = %s
        """, (fecha_actual, pastizal_id, session['usuario_id']))
        
        # Registrar animales en el pastizal
        for animal_id in animales:
            cursor.execute("""
                INSERT INTO pastizales_animales (
                    pastizal_id, animal_id, fecha_ingreso
                ) VALUES (%s, %s, %s)
            """, (pastizal_id, animal_id, fecha_actual))
            
            # Actualizar estado del animal
            cursor.execute("""
                UPDATE animales
                SET estado = 'En pastizal'
                WHERE id = %s AND usuario_id = %s
            """, (animal_id, session['usuario_id']))
        
        conn.commit()
        flash(f'Se han asignado {len(animales)} animales al pastizal exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al asignar animales: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('pastizales'))

@app.route('/inseminaciones')
@login_required
def inseminaciones():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener todas las inseminaciones con detalles del animal
        cursor.execute("""
            SELECT i.*, a.nombre as nombre_animal, a.numero_arete as arete_animal, a.condicion as condicion_animal
            FROM inseminaciones i 
            JOIN animales a ON i.animal_id = a.id 
            ORDER BY i.fecha_inseminacion DESC
        """)
        inseminaciones = cursor.fetchall()
        
        # Obtener animales hembras disponibles para inseminación
        cursor.execute("""
            SELECT id, nombre, numero_arete, condicion
            FROM animales 
            WHERE sexo = 'Hembra'
            AND condicion IN ('Vaca', 'Vacona')
            ORDER BY nombre
        """)
        animales = cursor.fetchall()
        
        return render_template('inseminaciones.html', 
                             inseminaciones=inseminaciones,
                             animales=animales)
    
    except Exception as e:
        flash(f'Error al cargar las inseminaciones: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/agregar_inseminacion', methods=['POST'])
@login_required
def agregar_inseminacion():
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha_inseminacion']
        tipo = request.form['tipo']
        semental = request.form.get('semental', '')
        raza_semental = request.form.get('raza_semental', '')
        codigo_pajuela = request.form.get('codigo_pajuela', '')
        inseminador = request.form['inseminador']
        exitosa = bool(int(request.form.get('exitosa', 0)))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO inseminaciones (
                animal_id, fecha_inseminacion, tipo, semental, 
                raza_semental, codigo_pajuela, inseminador, exitosa
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (animal_id, fecha, tipo, semental, raza_semental,
              codigo_pajuela, inseminador, exitosa))
        
        db.commit()
        flash('Inseminación registrada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar la inseminación: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('inseminaciones'))

@app.route('/eliminar_inseminacion/<int:id>', methods=['DELETE'])
@login_required
def eliminar_inseminacion(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que la inseminación existe
        cursor.execute("SELECT id FROM inseminaciones WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("La inseminación no existe")
        
        cursor.execute("DELETE FROM inseminaciones WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Inseminación eliminada correctamente'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({
            'success': False, 
            'message': f'Error al eliminar la inseminación: {str(e)}'
        }), 500
        
    finally:
        cursor.close()
        db.close()

@app.route('/editar_inseminacion/<int:id>', methods=['POST'])
@login_required
def editar_inseminacion(id):
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha_inseminacion']
        tipo = request.form['tipo']
        semental = request.form.get('semental', '')
        raza_semental = request.form.get('raza_semental', '')
        codigo_pajuela = request.form.get('codigo_pajuela', '')
        inseminador = request.form['inseminador']
        exitosa = bool(int(request.form.get('exitosa', 0)))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que la inseminación existe
        cursor.execute("SELECT id FROM inseminaciones WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("La inseminación no existe")
        
        # Verificar que el animal existe y es válido
        cursor.execute("""
            SELECT id FROM animales 
            WHERE id = %s AND sexo = 'Hembra' 
            AND condicion IN ('Vaca', 'Vacona')
        """, (animal_id,))
        if not cursor.fetchone():
            raise Exception("El animal seleccionado no es válido")
        
        cursor.execute("""
            UPDATE inseminaciones 
            SET animal_id = %s, fecha_inseminacion = %s, tipo = %s,
                semental = %s, raza_semental = %s, codigo_pajuela = %s,
                inseminador = %s, exitosa = %s
            WHERE id = %s
        """, (animal_id, fecha, tipo, semental, raza_semental,
              codigo_pajuela, inseminador, exitosa, id))
        
        db.commit()
        flash('Inseminación actualizada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar la inseminación: {str(e)}', 'danger')
        
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('inseminaciones'))

@app.route('/genealogia')
@login_required
def genealogia():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener registros genealógicos con nombres de animales
        cursor.execute("""
            SELECT g.*, 
                   a.nombre as nombre_animal,
                   p.nombre as padre_nombre,
                   m.nombre as madre_nombre
            FROM genealogia g
            JOIN animales a ON g.animal_id = a.id
            LEFT JOIN animales p ON g.padre_id = p.id
            LEFT JOIN animales m ON g.madre_id = m.id
            ORDER BY a.nombre
        """)
        genealogia = cursor.fetchall()
        
        # Obtener lista de animales para los selectores
        cursor.execute("SELECT id, nombre, numero_arete FROM animales ORDER BY nombre")
        animales = cursor.fetchall()
        
        return render_template('genealogia.html', 
                             genealogia=genealogia,
                             animales=animales)
    
    except Exception as e:
        flash(f'Error al cargar los registros genealógicos: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/agregar_genealogia', methods=['POST'])
@login_required
def agregar_genealogia():
    try:
        animal_id = request.form['animal_id']
        padre_id = request.form['padre_id'] or None
        madre_id = request.form['madre_id'] or None
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO genealogia (animal_id, padre_id, madre_id)
            VALUES (%s, %s, %s)
        """, (animal_id, padre_id, madre_id))
        
        db.commit()
        flash('Registro genealógico agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el registro genealógico: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('genealogia'))

@app.route('/obtener_genealogia/<int:id>')
@login_required
def obtener_genealogia(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT g.*, 
                   a.nombre as nombre_animal,
                   p.nombre as padre_nombre,
                   m.nombre as madre_nombre
            FROM genealogia g
            JOIN animales a ON g.animal_id = a.id
            LEFT JOIN animales p ON g.padre_id = p.id
            LEFT JOIN animales m ON g.madre_id = m.id
            WHERE g.id = %s
        """, (id,))
        genealogia = cursor.fetchone()
        
        if not genealogia:
            return jsonify({'error': 'Registro genealógico no encontrado'}), 404
            
        return jsonify(genealogia)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404

@app.route('/editar_genealogia/<int:id>', methods=['POST'])
@login_required
def editar_genealogia(id):
    try:
        animal_id = request.form['animal_id']
        padre_id = request.form['padre_id'] or None
        madre_id = request.form['madre_id'] or None
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que el registro existe
        cursor.execute("SELECT id FROM genealogia WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("Registro genealógico no encontrado")
        
        # Verificar que el animal existe
        cursor.execute("SELECT id FROM animales WHERE id = %s", (animal_id,))
        if not cursor.fetchone():
            raise Exception("Animal no encontrado")
        
        # Si se especifica un padre, verificar que existe
        if padre_id:
            cursor.execute("SELECT id FROM animales WHERE id = %s", (padre_id,))
            if not cursor.fetchone():
                raise Exception("Padre no encontrado")
        
        # Si se especifica una madre, verificar que existe
        if madre_id:
            cursor.execute("SELECT id FROM animales WHERE id = %s", (madre_id,))
            if not cursor.fetchone():
                raise Exception("Madre no encontrada")
        
        cursor.execute("""
            UPDATE genealogia 
            SET animal_id = %s, padre_id = %s, madre_id = %s
            WHERE id = %s
        """, (animal_id, padre_id, madre_id, id))
        
        db.commit()
        flash('Registro genealógico actualizado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar el registro genealógico: {str(e)}', 'danger')
        
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('genealogia'))

@app.route('/eliminar_genealogia/<int:id>', methods=['DELETE'])
@login_required
def eliminar_genealogia(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Verificar que el registro existe
        cursor.execute("SELECT id FROM genealogia WHERE id = %s", (id,))
        if not cursor.fetchone():
            raise Exception("Registro genealógico no encontrado")
        
        cursor.execute("DELETE FROM genealogia WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Registro genealógico eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
        
    finally:
        cursor.close()
        db.close()

@app.route('/registro_leche')
@login_required
def registro_leche():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        animal_id = request.args.get('animal')
        
        # Construir consulta base
        query = """
            SELECT p.*, a.nombre as nombre_animal
            FROM produccion_leche p
            JOIN animales a ON p.animal_id = a.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(p.fecha) = %s"
            params.append(fecha)
        if animal_id:
            query += " AND p.animal_id = %s"
            params.append(animal_id)
            
        query += " ORDER BY p.fecha DESC"
        
        cursor.execute(query, params)
        registros = cursor.fetchall()
        
        # Obtener lista de animales para el selector
        cursor.execute("""
            SELECT id, nombre, numero_arete 
            FROM animales 
            WHERE sexo = 'Hembra'
            AND condicion IN ('Vaca', 'Vacona')
            ORDER BY nombre
        """)
        animales = cursor.fetchall()
        
        return render_template('registro_leche.html', 
                             registros=registros,
                             animales=animales)
    
    except Exception as e:
        flash(f'Error al cargar los registros: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/registro_leche/agregar', methods=['POST'])
@login_required
def agregar_registro_leche():
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha']
        cantidad_manana = request.form['cantidad_manana']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO produccion_leche (
                animal_id, fecha, cantidad_manana, cantidad_tarde
            ) VALUES (%s, %s, %s, %s)
        """, (animal_id, fecha, cantidad_manana, 0))
        
        db.commit()
        flash('Registro de producción agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el registro: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('registro_leche'))

@app.route('/registro_leche/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_registro_leche(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM produccion_leche WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Registro eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/registro_leche/obtener/<int:id>')
@login_required
def obtener_registro_leche(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT p.*, a.nombre as nombre_animal,
                   DATE_FORMAT(p.fecha, '%Y-%m-%d') as fecha_formato
            FROM produccion_leche p
            JOIN animales a ON p.animal_id = a.id
            WHERE p.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if registro:
            return jsonify({'success': True, 'registro': registro})
        else:
            return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/registro_leche/editar/<int:id>', methods=['POST'])
@login_required
def editar_registro_leche(id):
    try:
        animal_id = request.form['animal_id']
        fecha = request.form['fecha']
        cantidad_manana = request.form['cantidad_manana']
        
        # Validar que la fecha no esté vacía
        if not fecha:
            raise ValueError('La fecha es requerida')
            
        # Convertir la fecha al formato correcto para MySQL
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_mysql = fecha_obj.strftime('%Y-%m-%d')
        except ValueError as e:
            raise ValueError('Formato de fecha inválido. Use YYYY-MM-DD')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE produccion_leche
            SET animal_id = %s,
                fecha = %s,
                cantidad_manana = %s,
                cantidad_tarde = 0
            WHERE id = %s
        """, (animal_id, fecha_mysql, cantidad_manana, id))
        
        db.commit()
        flash('Registro de producción actualizado exitosamente', 'success')
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'danger')
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar el registro: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('registro_leche'))

@app.route('/ventas_leche')
@login_required
def ventas_leche():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        estado = request.args.get('estado')
        
        # Construir consulta base
        query = """
            SELECT *
            FROM ventas_leche
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(fecha) = %s"
            params.append(fecha)
        if estado:
            query += " AND estado_pago = %s"
            params.append(estado)
            
        query += " ORDER BY fecha DESC"
        
        cursor.execute(query, params)
        ventas = cursor.fetchall()
        
        # Calcular totales para hoy
        cursor.execute("""
            SELECT SUM(cantidad_litros) as total_litros,
                   SUM(total_venta) as total_ingresos
            FROM ventas_leche 
            WHERE DATE(fecha) = CURDATE()
        """)
        totales_hoy = cursor.fetchone()
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(cantidad_litros) as total_litros,
                   SUM(total_venta) as total_ingresos
            FROM ventas_leche 
            WHERE YEAR(fecha) = YEAR(CURDATE()) 
            AND MONTH(fecha) = MONTH(CURDATE())
        """)
        totales_mes = cursor.fetchone()
        
        return render_template('ventas_leche.html',
                             ventas=ventas,
                             total_hoy=totales_hoy['total_litros'] or 0,
                             ingresos_hoy=totales_hoy['total_ingresos'] or 0,
                             total_mes=totales_mes['total_litros'] or 0,
                             ingresos_mes=totales_mes['total_ingresos'] or 0)
    
    except Exception as e:
        flash(f'Error al cargar las ventas: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/ventas_leche/agregar', methods=['POST'])
@login_required
def agregar_venta_leche():
    try:
        fecha = request.form['fecha']
        cantidad_litros = float(request.form['cantidad_litros'])
        precio_litro = float(request.form['precio_litro'])
        comprador = request.form['comprador']
        forma_pago = request.form['forma_pago']
        estado_pago = request.form['estado_pago']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO ventas_leche (
                fecha, cantidad_litros, precio_litro,
                comprador, forma_pago, estado_pago
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (fecha, cantidad_litros, precio_litro,
              comprador, forma_pago, estado_pago))
        
        db.commit()
        flash('Venta registrada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar la venta: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ventas_leche'))

@app.route('/ventas_leche/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_venta_leche(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM ventas_leche WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Venta eliminada correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/ventas_leche/obtener/<int:id>')
@login_required
def obtener_venta_leche(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM ventas_leche WHERE id = %s", (id,))
        venta = cursor.fetchone()
        
        if venta:
            return jsonify({'success': True, 'venta': venta})
        else:
            return jsonify({'success': False, 'message': 'Venta no encontrada'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/ventas_leche/editar/<int:id>', methods=['POST'])
@login_required
def editar_venta_leche(id):
    try:
        fecha = request.form['fecha']
        cantidad_litros = float(request.form['cantidad_litros'])
        precio_litro = float(request.form['precio_litro'])
        comprador = request.form['comprador']
        forma_pago = request.form['forma_pago']
        estado_pago = request.form['estado_pago']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            UPDATE ventas_leche 
            SET fecha = %s,
                cantidad_litros = %s,
                precio_litro = %s,
                comprador = %s,
                forma_pago = %s,
                estado_pago = %s
            WHERE id = %s
        """, (fecha, cantidad_litros, precio_litro, 
              comprador, forma_pago, estado_pago, id))
        
        db.commit()
        flash('Venta actualizada exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al actualizar la venta: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ventas_leche'))

@app.route('/ingresos')
@login_required
def ingresos():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        categoria_id = request.args.get('categoria')
        
        # Construir consulta base
        query = """
            SELECT i.*, c.nombre as categoria_nombre
            FROM ingresos i
            JOIN categorias_ingreso c ON i.categoria_id = c.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(i.fecha) = %s"
            params.append(fecha)
        if categoria_id:
            query += " AND i.categoria_id = %s"
            params.append(categoria_id)
            
        query += " ORDER BY i.fecha DESC"
        
        cursor.execute(query, params)
        ingresos = cursor.fetchall()
        
        # Obtener categorías para el selector
        cursor.execute("SELECT * FROM categorias_ingreso ORDER BY nombre")
        categorias = cursor.fetchall()
        
        # Calcular totales para hoy
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE DATE(fecha) = CURDATE()
        """)
        total_hoy = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE YEAR(fecha) = YEAR(CURDATE()) 
            AND MONTH(fecha) = MONTH(CURDATE())
        """)
        total_mes = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el año actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM ingresos 
            WHERE YEAR(fecha) = YEAR(CURDATE())
        """)
        total_anio = cursor.fetchone()['total'] or 0
        
        return render_template('ingresos.html',
                             ingresos=ingresos,
                             categorias=categorias,
                             total_hoy=total_hoy,
                             total_mes=total_mes,
                             total_anio=total_anio)
    
    except Exception as e:
        flash(f'Error al cargar los ingresos: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/ingresos/agregar', methods=['POST'])
@login_required
def agregar_ingreso():
    try:
        fecha = request.form['fecha']
        categoria_id = request.form['categoria_id']
        monto = float(request.form['monto'])
        descripcion = request.form.get('descripcion', '')
        
        # Manejar el archivo de comprobante
        comprobante = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename:
                # Generar un nombre seguro para el archivo
                filename = secure_filename(file.filename)
                # Asegurarse de que el directorio existe
                os.makedirs('uploads/comprobantes', exist_ok=True)
                # Guardar el archivo
                filepath = os.path.join('uploads/comprobantes', filename)
                file.save(filepath)
                comprobante = filepath
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO ingresos (
                fecha, categoria_id, monto, descripcion, comprobante
            ) VALUES (%s, %s, %s, %s, %s)
        """, (fecha, categoria_id, monto, descripcion, comprobante))
        
        db.commit()
        flash('Ingreso registrado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar el ingreso: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('ingresos'))

@app.route('/ingresos/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_ingreso(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Primero obtenemos la información del ingreso para eliminar el comprobante si existe
        cursor.execute("SELECT comprobante FROM ingresos WHERE id = %s", (id,))
        ingreso = cursor.fetchone()
        
        if ingreso and ingreso['comprobante']:
            try:
                os.remove(ingreso['comprobante'])
            except OSError:
                # Si el archivo no existe o no se puede eliminar, continuamos
                pass
        
        cursor.execute("DELETE FROM ingresos WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Ingreso eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/gastos')
@login_required
def gastos():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener filtros
        fecha = request.args.get('fecha')
        categoria_id = request.args.get('categoria')
        
        # Construir consulta base
        query = """
            SELECT g.*, c.nombre as categoria_nombre
            FROM gastos g
            JOIN categorias_gasto c ON g.categoria_id = c.id
            WHERE 1=1
        """
        params = []
        
        # Agregar filtros si existen
        if fecha:
            query += " AND DATE(g.fecha) = %s"
            params.append(fecha)
        if categoria_id:
            query += " AND g.categoria_id = %s"
            params.append(categoria_id)
            
        query += " ORDER BY g.fecha DESC"
        
        cursor.execute(query, params)
        gastos = cursor.fetchall()
        
        # Obtener categorías para el selector
        cursor.execute("SELECT * FROM categorias_gasto ORDER BY nombre")
        categorias = cursor.fetchall()
        
        # Calcular totales para hoy
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE DATE(fecha) = CURDATE()
        """)
        total_hoy = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el mes actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE YEAR(fecha) = YEAR(CURDATE()) 
            AND MONTH(fecha) = MONTH(CURDATE())
        """)
        total_mes = cursor.fetchone()['total'] or 0
        
        # Calcular totales para el año actual
        cursor.execute("""
            SELECT SUM(monto) as total
            FROM gastos 
            WHERE YEAR(fecha) = YEAR(CURDATE())
        """)
        total_anio = cursor.fetchone()['total'] or 0
        
        return render_template('gastos.html',
                             gastos=gastos,
                             categorias=categorias,
                             total_hoy=total_hoy,
                             total_mes=total_mes,
                             total_anio=total_anio)
    
    except Exception as e:
        flash(f'Error al cargar los gastos: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/gastos/agregar', methods=['POST'])
@login_required
def agregar_gasto():
    try:
        fecha = request.form['fecha']
        categoria_id = request.form['categoria_id']
        monto = float(request.form['monto'])
        descripcion = request.form.get('descripcion', '')
        
        # Manejar el archivo de comprobante
        comprobante = None
        if 'comprobante' in request.files:
            file = request.files['comprobante']
            if file and file.filename:
                # Generar un nombre seguro para el archivo
                filename = secure_filename(file.filename)
                # Asegurarse de que el directorio existe
                os.makedirs('uploads/comprobantes', exist_ok=True)
                # Guardar el archivo
                filepath = os.path.join('uploads/comprobantes', filename)
                file.save(filepath)
                comprobante = filepath
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO gastos (
                fecha, categoria_id, monto, descripcion, comprobante
            ) VALUES (%s, %s, %s, %s, %s)
        """, (fecha, categoria_id, monto, descripcion, comprobante))
        
        db.commit()
        flash('Gasto registrado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar el gasto: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('gastos'))

@app.route('/gastos/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_gasto(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Primero obtenemos la información del gasto para eliminar el comprobante si existe
        cursor.execute("SELECT comprobante FROM gastos WHERE id = %s", (id,))
        gasto = cursor.fetchone()
        
        if gasto and gasto['comprobante']:
            try:
                os.remove(gasto['comprobante'])
            except OSError:
                # Si el archivo no existe o no se puede eliminar, continuamos
                pass
        
        cursor.execute("DELETE FROM gastos WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Gasto eliminado correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/reportes_financieros')
@login_required
def reportes_financieros():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # Obtener el año y mes actual
        fecha_actual = datetime.now()
        año_actual = fecha_actual.year
        mes_actual = fecha_actual.month
        
        # Obtener ingresos mensuales del año actual
        cursor.execute("""
            SELECT 
                MONTH(fecha) as mes,
                COALESCE(SUM(monto), 0) as total_ingresos
            FROM ingresos 
            WHERE YEAR(fecha) = %s
            GROUP BY MONTH(fecha)
            ORDER BY MONTH(fecha)
        """, (año_actual,))
        ingresos_mensuales = cursor.fetchall()
        
        # Obtener gastos mensuales del año actual
        cursor.execute("""
            SELECT 
                MONTH(fecha) as mes,
                COALESCE(SUM(monto), 0) as total_gastos
            FROM gastos 
            WHERE YEAR(fecha) = %s
            GROUP BY MONTH(fecha)
            ORDER BY MONTH(fecha)
        """, (año_actual,))
        gastos_mensuales = cursor.fetchall()
        
        # Obtener ingresos por categoría del mes actual
        cursor.execute("""
            SELECT 
                c.nombre as categoria,
                COALESCE(SUM(i.monto), 0) as total
            FROM categorias_ingreso c
            LEFT JOIN ingresos i ON c.id = i.categoria_id 
                AND YEAR(i.fecha) = %s 
                AND MONTH(i.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año_actual, mes_actual))
        ingresos_por_categoria = cursor.fetchall()
        
        # Obtener gastos por categoría del mes actual
        cursor.execute("""
            SELECT 
                c.nombre as categoria,
                COALESCE(SUM(g.monto), 0) as total
            FROM categorias_gasto c
            LEFT JOIN gastos g ON c.id = g.categoria_id 
                AND YEAR(g.fecha) = %s 
                AND MONTH(g.fecha) = %s
            GROUP BY c.id, c.nombre
            ORDER BY total DESC
        """, (año_actual, mes_actual))
        gastos_por_categoria = cursor.fetchall()
        
        # Calcular totales generales
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM ingresos 
            WHERE YEAR(fecha) = %s
        """, (año_actual,))
        total_ingresos_anual = float(cursor.fetchone()['total'])
        
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM gastos 
            WHERE YEAR(fecha) = %s
        """, (año_actual,))
        total_gastos_anual = float(cursor.fetchone()['total'])
        
        balance_anual = total_ingresos_anual - total_gastos_anual
        
        # Preparar datos para las gráficas
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        datos_ingresos = [0] * 12
        datos_gastos = [0] * 12
        
        for ingreso in ingresos_mensuales:
            datos_ingresos[ingreso['mes'] - 1] = float(ingreso['total_ingresos'])
        
        for gasto in gastos_mensuales:
            datos_gastos[gasto['mes'] - 1] = float(gasto['total_gastos'])
        
        return render_template('reportes_financieros.html',
                             año_actual=año_actual,
                             mes_actual=meses[mes_actual - 1],
                             meses=meses,
                             datos_ingresos=datos_ingresos,
                             datos_gastos=datos_gastos,
                             ingresos_por_categoria=ingresos_por_categoria,
                             gastos_por_categoria=gastos_por_categoria,
                             total_ingresos_anual="{:,.2f}".format(total_ingresos_anual),
                             total_gastos_anual="{:,.2f}".format(total_gastos_anual),
                             balance_anual="{:,.2f}".format(balance_anual))
                             
    except Exception as e:
        flash(f'Error al generar el reporte financiero: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        db.close()

@app.route('/planes_alimentacion')
@login_required
def planes_alimentacion():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM planes_alimentacion")
    planes = cursor.fetchall()
    return render_template('planes_alimentacion.html', planes=planes)

@app.route('/planes_alimentacion/agregar', methods=['POST'])
@login_required
def agregar_plan_alimentacion():
    try:
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO planes_alimentacion (nombre, descripcion)
            VALUES (%s, %s)
        """, (nombre, descripcion))
        
        db.commit()
        flash('Plan de alimentación agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el plan de alimentación: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('planes_alimentacion'))

@app.route('/registro_alimentacion')
@login_required
def registro_alimentacion():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT ra.*, a.nombre as nombre_animal, pa.nombre as plan_nombre 
        FROM registro_alimentacion ra 
        JOIN animales a ON ra.animal_id = a.id 
        JOIN planes_alimentacion pa ON ra.plan_id = pa.id 
        ORDER BY ra.fecha DESC
    """)
    registros = cursor.fetchall()
    return render_template('registro_alimentacion.html', registros=registros)

@app.route('/registro_alimentacion/agregar', methods=['POST'])
@login_required
def agregar_registro_alimentacion():
    try:
        animal_id = request.form['animal_id']
        plan_id = request.form['plan_id']
        fecha = request.form['fecha']
        cantidad = request.form['cantidad']
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO registro_alimentacion (
                animal_id, plan_id, fecha, cantidad
            ) VALUES (%s, %s, %s, %s)
        """, (animal_id, plan_id, fecha, cantidad))
        
        db.commit()
        flash('Registro de alimentación agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el registro de alimentación: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('registro_alimentacion'))

@app.route('/equipos')
@login_required
def equipos():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM equipos")
    equipos = cursor.fetchall()
    return render_template('equipos.html', equipos=equipos)

@app.route('/equipos/agregar', methods=['POST'])
@login_required
def agregar_equipo():
    try:
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        marca = request.form.get('marca', '')
        modelo = request.form.get('modelo', '')
        estado = request.form['estado']
        fecha_adquisicion = request.form['fecha_adquisicion']
        costo = request.form.get('costo', 0)
        ubicacion = request.form.get('ubicacion', '')
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO equipos (
                nombre, tipo, marca, modelo, estado, 
                fecha_adquisicion, costo, ubicacion
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (nombre, tipo, marca, modelo, estado, 
              fecha_adquisicion, costo, ubicacion))
        
        db.commit()
        flash('Equipo agregado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al agregar el equipo: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('equipos'))

@app.route('/mantenimientos')
@login_required
def mantenimientos():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT m.*, e.nombre as equipo_nombre 
        FROM mantenimientos m 
        JOIN equipos e ON m.equipo_id = e.id 
        ORDER BY m.fecha_programada
    """)
    mantenimientos = cursor.fetchall()
    return render_template('mantenimientos.html', mantenimientos=mantenimientos)

@app.route('/mantenimientos/agregar', methods=['POST'])
@login_required
def agregar_mantenimiento():
    try:
        equipo_id = request.form['equipo_id']
        tipo_mantenimiento = request.form['tipo_mantenimiento']
        fecha = request.form['fecha']
        descripcion = request.form['descripcion']
        costo = request.form.get('costo', 0)
        responsable = request.form.get('responsable', '')
        estado = request.form['estado']
        proxima_fecha = request.form.get('proxima_fecha', None)
        
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO mantenimientos (
                equipo_id, tipo_mantenimiento, fecha, descripcion,
                costo, responsable, estado, proxima_fecha
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (equipo_id, tipo_mantenimiento, fecha, descripcion,
              costo, responsable, estado, proxima_fecha))
        
        db.commit()
        flash('Mantenimiento registrado exitosamente', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Error al registrar el mantenimiento: {str(e)}', 'danger')
    finally:
        cursor.close()
        db.close()
    
    return redirect(url_for('mantenimientos'))

@app.route('/empleados')
@login_required
def empleados():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, nombre, apellido, cedula, telefono, cargo, 
                       fecha_contratacion, salario, estado
                FROM empleados
                ORDER BY nombre, apellido
            """)
            empleados = cursor.fetchall()
            return render_template('empleados.html', empleados=empleados)
    except Exception as e:
        app.logger.error(f"Error en empleados: {e}")
        flash('Error al cargar los empleados', 'error')
        return redirect(url_for('dashboard'))

@app.route('/agregar_empleado', methods=['POST'])
@login_required
def agregar_empleado():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO empleados (nombre, apellido, cedula, telefono, direccion, 
                                     cargo, fecha_contratacion, salario, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form['nombre'],
                request.form['apellido'],
                request.form['cedula'],
                request.form['telefono'],
                request.form['direccion'],
                request.form['cargo'],
                request.form['fecha_contratacion'],
                request.form['salario'],
                request.form['estado'] == '1'
            ))
            conn.commit()
            flash('Empleado agregado exitosamente', 'success')
    except Exception as e:
        app.logger.error(f"Error al agregar empleado: {e}")
        flash('Error al agregar el empleado', 'error')
    return redirect(url_for('empleados'))

@app.route('/obtener_empleado/<int:id>')
@login_required
def obtener_empleado(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, nombre, apellido, cedula, telefono, direccion,
                       cargo, fecha_contratacion, salario, estado
                FROM empleados WHERE id = %s
            """, (id,))
            empleado = cursor.fetchone()
            if empleado:
                empleado['fecha_contratacion'] = empleado['fecha_contratacion'].strftime('%Y-%m-%d')
                return jsonify(empleado)
            return jsonify({'error': 'Empleado no encontrado'}), 404
    except Exception as e:
        app.logger.error(f"Error al obtener empleado: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/editar_empleado/<int:id>', methods=['POST'])
@login_required
def editar_empleado(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE empleados 
                SET nombre = %s, apellido = %s, cedula = %s, telefono = %s,
                    direccion = %s, cargo = %s, fecha_contratacion = %s,
                    salario = %s, estado = %s
                WHERE id = %s
            """, (
                request.form['nombre'],
                request.form['apellido'],
                request.form['cedula'],
                request.form['telefono'],
                request.form['direccion'],
                request.form['cargo'],
                request.form['fecha_contratacion'],
                request.form['salario'],
                request.form['estado'] == '1',
                id
            ))
            conn.commit()
            flash('Empleado actualizado exitosamente', 'success')
    except Exception as e:
        app.logger.error(f"Error al editar empleado: {e}")
        flash('Error al actualizar el empleado', 'error')
    return redirect(url_for('empleados'))

@app.route('/eliminar_empleado/<int:id>', methods=['POST'])
@login_required
def eliminar_empleado(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM empleados WHERE id = %s", (id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error al eliminar empleado: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/asistencias')
@login_required
def asistencias():
    try:
        fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener empleados activos para el formulario
            cursor.execute("SELECT id, nombre, apellido FROM empleados WHERE estado = 1")
            empleados = cursor.fetchall()
            
            # Obtener asistencias del día
            cursor.execute("""
                SELECT a.*, CONCAT(e.nombre, ' ', e.apellido) as nombre_empleado
                FROM asistencias a
                JOIN empleados e ON a.empleado_id = e.id
                WHERE DATE(a.fecha) = %s
                ORDER BY a.hora_entrada DESC
            """, (fecha,))
            asistencias = cursor.fetchall()
            
            return render_template('asistencias.html', 
                                 asistencias=asistencias, 
                                 empleados=empleados,
                                 fecha_actual=fecha)
    except Exception as e:
        app.logger.error(f"Error en asistencias: {e}")
        flash('Error al cargar las asistencias', 'error')
        return redirect(url_for('dashboard'))

@app.route('/tareas')
@login_required
def tareas():
    try:
        estado = request.args.get('estado', '')
        prioridad = request.args.get('prioridad', '')
        
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            
            # Obtener empleados activos para el formulario
            cursor.execute("SELECT id, nombre, apellido FROM empleados WHERE estado = 1")
            empleados = cursor.fetchall()
            
            # Construir consulta base
            query = """
                SELECT t.*, CONCAT(e.nombre, ' ', e.apellido) as nombre_empleado
                FROM tareas t
                JOIN empleados e ON t.empleado_id = e.id
                WHERE 1=1
            """
            params = []
            
            # Agregar filtros si están presentes
            if estado:
                query += " AND t.estado = %s"
                params.append(estado)
            if prioridad:
                query += " AND t.prioridad = %s"
                params.append(prioridad)
                
            query += " ORDER BY t.fecha_asignacion DESC"
            
            cursor.execute(query, params)
            tareas = cursor.fetchall()
            
            # Formatear fechas para mostrar
            for tarea in tareas:
                tarea['fecha_asignacion'] = tarea['fecha_asignacion'].strftime('%Y-%m-%d %H:%M')
                tarea['fecha_vencimiento'] = tarea['fecha_vencimiento'].strftime('%Y-%m-%d %H:%M')
            
            return render_template('tareas.html', 
                                 tareas=tareas, 
                                 empleados=empleados)
    except Exception as e:
        app.logger.error(f"Error en tareas: {e}")
        flash('Error al cargar las tareas', 'error')
        return redirect(url_for('dashboard'))

@app.route('/agregar_tarea', methods=['POST'])
@login_required
def agregar_tarea():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tareas (titulo, descripcion, empleado_id, fecha_asignacion,
                                  fecha_vencimiento, estado, prioridad)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form['titulo'],
                request.form['descripcion'],
                request.form['empleado_id'],
                request.form['fecha_asignacion'],
                request.form['fecha_vencimiento'],
                request.form['estado'],
                request.form['prioridad']
            ))
            conn.commit()
            flash('Tarea agregada exitosamente', 'success')
    except Exception as e:
        app.logger.error(f"Error al agregar tarea: {e}")
        flash('Error al agregar la tarea', 'error')
    return redirect(url_for('tareas'))

@app.route('/obtener_tarea/<int:id>')
@login_required
def obtener_tarea(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.*, CONCAT(e.nombre, ' ', e.apellido) as nombre_empleado
                FROM tareas t
                JOIN empleados e ON t.empleado_id = e.id
                WHERE t.id = %s
            """, (id,))
            tarea = cursor.fetchone()
            if tarea:
                tarea['fecha_asignacion'] = tarea['fecha_asignacion'].strftime('%Y-%m-%d %H:%M')
                tarea['fecha_vencimiento'] = tarea['fecha_vencimiento'].strftime('%Y-%m-%d %H:%M')
                return jsonify(tarea)
            return jsonify({'error': 'Tarea no encontrada'}), 404
    except Exception as e:
        app.logger.error(f"Error al obtener tarea: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/actualizar_estado_tarea/<int:id>', methods=['POST'])
@login_required
def actualizar_estado_tarea(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            # Obtener estado actual
            cursor.execute("SELECT estado FROM tareas WHERE id = %s", (id,))
            tarea = cursor.fetchone()
            
            if not tarea:
                return jsonify({'success': False, 'error': 'Tarea no encontrada'})
            
            # Determinar siguiente estado
            nuevo_estado = {
                'pendiente': 'en_proceso',
                'en_proceso': 'completada',
                'completada': 'pendiente'
            }.get(tarea['estado'], 'pendiente')
            
            # Actualizar estado
            cursor.execute("""
                UPDATE tareas SET estado = %s WHERE id = %s
            """, (nuevo_estado, id))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error al actualizar estado de tarea: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/eliminar_tarea/<int:id>', methods=['POST'])
@login_required
def eliminar_tarea(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tareas WHERE id = %s", (id,))
            conn.commit()
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error al eliminar tarea: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clima')
@login_required
def clima():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM registros_clima ORDER BY fecha DESC LIMIT 30")
    registros = cursor.fetchall()
    return render_template('clima.html', registros=registros)

@app.route('/trazabilidad')
@login_required
def trazabilidad():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""
        SELECT e.*, a.nombre as nombre_animal 
        FROM eventos_animal e 
        JOIN animales a ON e.animal_id = a.id 
        ORDER BY e.fecha DESC
    """)
    eventos = cursor.fetchall()
    return render_template('trazabilidad.html', eventos=eventos)

@app.route('/asistencias/registrar', methods=['POST'])
@login_required
def registrar_asistencia():
    try:
        empleado_id = request.form['empleado_id']
        fecha = request.form['fecha']
        hora_entrada = request.form['hora_entrada']
        estado = request.form['estado']
        observaciones = request.form.get('observaciones', '')
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar si ya existe una asistencia para este empleado en esta fecha
            cursor.execute("""
                SELECT id FROM asistencias 
                WHERE empleado_id = %s AND fecha = %s
            """, (empleado_id, fecha))
            
            existe = cursor.fetchone()
            if existe:
                flash('Ya existe un registro de asistencia para este empleado en esta fecha', 'error')
                return redirect(url_for('asistencias'))
            
            # Insertar la nueva asistencia
            cursor.execute("""
                INSERT INTO asistencias (
                    empleado_id, fecha, hora_entrada, estado, observaciones
                ) VALUES (%s, %s, %s, %s, %s)
            """, (empleado_id, fecha, hora_entrada, estado, observaciones))
            
            conn.commit()
            flash('Asistencia registrada exitosamente', 'success')
            
    except Exception as e:
        app.logger.error(f"Error al registrar asistencia: {e}")
        flash('Error al registrar la asistencia', 'error')
        
    return redirect(url_for('asistencias'))

@app.route('/asistencias/salida/<int:id>', methods=['POST'])
@login_required
def registrar_salida(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtener la hora actual
        hora_salida = datetime.now().strftime('%H:%M')
        
        cursor.execute("""
            UPDATE asistencias 
            SET hora_salida = %s 
            WHERE id = %s
        """, (hora_salida, id))
        
        db.commit()
        return jsonify({'success': True, 'message': 'Salida registrada correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/asistencias/eliminar/<int:id>', methods=['DELETE'])
@login_required
def eliminar_asistencia(id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute("DELETE FROM asistencias WHERE id = %s", (id,))
        db.commit()
        
        return jsonify({'success': True, 'message': 'Asistencia eliminada correctamente'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route('/editar_pastizal/<int:pastizal_id>', methods=['POST'])
@login_required
def editar_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        nombre = request.form['nombre']
        dimension = float(request.form['dimension'])
        tipo_hierba = request.form['tipo_hierba']
        
        cursor.execute("""
            UPDATE pastizales 
            SET nombre = %s, dimension = %s, tipo_hierba = %s 
            WHERE id = %s AND usuario_id = %s
        """, (nombre, dimension, tipo_hierba, pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Pastizal actualizado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar el pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/eliminar_pastizal/<int:pastizal_id>', methods=['POST'])
@login_required
def eliminar_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar si hay animales en el pastizal
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pastizales_animales 
            WHERE pastizal_id = %s
        """, (pastizal_id,))
        
        count = cursor.fetchone()[0]  # Acceder al primer elemento de la tupla
        
        if count > 0:
            flash('No se puede eliminar el pastizal porque tiene animales asignados', 'danger')
            return redirect(url_for('pastizales'))
        
        # Eliminar el pastizal
        cursor.execute("""
            DELETE FROM pastizales 
            WHERE id = %s AND usuario_id = %s
        """, (pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Pastizal eliminado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al eliminar el pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/cambiar_estado_pastizal/<int:pastizal_id>', methods=['POST'])
@login_required
def cambiar_estado_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        nuevo_estado = request.form['estado']
        fecha_disponible = None
        
        if nuevo_estado == 'En regeneración':
            # Si pasa a regeneración, calcular fecha disponible (30 días después)
            fecha_disponible = (datetime.now() + timedelta(days=30)).date()
        
        cursor.execute("""
            UPDATE pastizales 
            SET estado = %s, 
                fecha_ultimo_uso = CASE 
                    WHEN %s = 'En regeneración' THEN CURRENT_DATE 
                    ELSE fecha_ultimo_uso 
                END,
                fecha_disponible = %s
            WHERE id = %s AND usuario_id = %s
        """, (nuevo_estado, nuevo_estado, fecha_disponible, pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Estado del pastizal actualizado exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar el estado del pastizal: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/retirar_animales/<int:pastizal_id>', methods=['POST'])
@login_required
def retirar_animales(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Eliminar todas las asignaciones de animales para este pastizal
        cursor.execute("""
            DELETE FROM pastizales_animales 
            WHERE pastizal_id = %s
        """, (pastizal_id,))
        
        # Actualizar el estado del pastizal a "En regeneración"
        fecha_disponible = (datetime.now() + timedelta(days=30)).date()
        cursor.execute("""
            UPDATE pastizales 
            SET estado = 'En regeneración',
                fecha_ultimo_uso = CURRENT_DATE,
                fecha_disponible = %s
            WHERE id = %s AND usuario_id = %s
        """, (fecha_disponible, pastizal_id, session['usuario_id']))
        
        conn.commit()
        flash('Animales retirados exitosamente. El pastizal ha entrado en período de regeneración.', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error al retirar los animales: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('pastizales'))

@app.route('/detalles_pastizal/<int:pastizal_id>')
@login_required
def detalles_pastizal(pastizal_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Obtener detalles del pastizal
        cursor.execute("""
            SELECT p.*, 
                   COUNT(DISTINCT pa.animal_id) as animales_actuales
            FROM pastizales p
            LEFT JOIN pastizales_animales pa ON p.id = pa.pastizal_id
            WHERE p.id = %s AND p.usuario_id = %s
            GROUP BY p.id
        """, (pastizal_id, session['usuario_id']))
        
        pastizal = cursor.fetchone()
        
        if not pastizal:
            flash('Pastizal no encontrado', 'danger')
            return redirect(url_for('pastizales'))
        
        # Obtener lista de animales en el pastizal
        cursor.execute("""
            SELECT a.*, pa.fecha_ingreso
            FROM animales a
            JOIN pastizales_animales pa ON a.id = pa.animal_id
            WHERE pa.pastizal_id = %s
            ORDER BY pa.fecha_ingreso DESC
        """, (pastizal_id,))
        
        animales = cursor.fetchall()
        
        return render_template('detalles_pastizal.html', pastizal=pastizal, animales=animales)
        
    except Exception as e:
        flash(f'Error al cargar los detalles del pastizal: {str(e)}', 'danger')
        return redirect(url_for('pastizales'))
    finally:
        cursor.close()
        conn.close()

@app.route('/obtener_inseminacion/<int:id>')
@login_required
def obtener_inseminacion(id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT i.*, a.nombre as nombre_animal, a.numero_arete as arete_animal
            FROM inseminaciones i 
            JOIN animales a ON i.animal_id = a.id 
            WHERE i.id = %s
        """, (id,))
        
        inseminacion = cursor.fetchone()
        if not inseminacion:
            raise Exception("Inseminación no encontrada")
            
        cursor.close()
        db.close()
        return jsonify(inseminacion)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404

@app.route('/registrar_inseminacion', methods=['POST'])
@login_required
def registrar_inseminacion():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        animal_id = request.form.get('animal_id')
        fecha_inseminacion = request.form.get('fecha_inseminacion')
        tipo_inseminacion = request.form.get('tipo_inseminacion')
        semental = request.form.get('semental')
        exitosa = bool(int(request.form.get('exitosa', 0)))
        
        cursor.execute("""
            INSERT INTO inseminaciones (
                animal_id, fecha_inseminacion, tipo_inseminacion, 
                semental, exitosa
            ) VALUES (%s, %s, %s, %s, %s)
        """, (animal_id, fecha_inseminacion, tipo_inseminacion, semental, exitosa))
        
        conn.commit()
        flash('Inseminación registrada exitosamente', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(str(e), 'danger')
    finally:
        cursor.close()
        conn.close()
        
    return redirect(url_for('inseminaciones'))

@app.route('/actualizar_estado_inseminacion', methods=['POST'])
@login_required
def actualizar_estado_inseminacion():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        datos = request.get_json()
        inseminacion_id = datos.get('inseminacion_id')
        nuevo_estado = datos.get('estado')
        
        # Verificar si la inseminación existe
        cursor.execute("""
            SELECT i.*, a.usuario_id, i.tipo_inseminacion 
            FROM inseminaciones i
            JOIN animales a ON i.animal_id = a.id
            WHERE i.id = %s
        """, (inseminacion_id,))
        
        inseminacion = cursor.fetchone()
        if not inseminacion or inseminacion['usuario_id'] != session['usuario_id']:
            raise Exception("Inseminación no encontrada")
        
        # Actualizar estado
        cursor.execute("""
            UPDATE inseminaciones 
            SET estado = %s
            WHERE id = %s
        """, (nuevo_estado, inseminacion_id))
        
        # Si la inseminación es exitosa, crear registro de gestación
        if nuevo_estado == 'Exitosa':
            cursor.execute("""
                INSERT INTO gestaciones (
                    animal_id, fecha_monta, estado
                ) VALUES (%s, %s, 'En Gestación')
            """, (inseminacion['animal_id'], inseminacion['fecha_inseminacion']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Estado actualizado correctamente'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/vitaminizacion')
@login_required
def vitaminizacion():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(v.fecha_registro) 
                    FROM vitaminizacion v 
                    JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id 
                    WHERE va.animal_id = a.id) as ultima_vitaminizacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de vitaminización
        cursor.execute("""
            SELECT v.*, 
                   (SELECT COUNT(*) 
                    FROM vitaminizacion_animal va 
                    WHERE va.vitaminizacion_id = v.id) as cantidad_animales
            FROM vitaminizacion v
            ORDER BY v.fecha_registro DESC
        """)
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('vitaminizacion.html', 
                             animales=animales, 
                             registros=registros,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de vitaminización: {str(e)}')
        flash('Error al cargar la página de vitaminización', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/registrar_vitaminizacion', methods=['POST'])
@login_required
def registrar_vitaminizacion():
    conn = None
    cursor = None
    try:
        fecha_registro = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        aplicador = request.form.get('aplicador')
        proxima_aplicacion = (datetime.strptime(fecha_registro, '%Y-%m-%d') + timedelta(days=90)).strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vitaminizacion 
            (fecha_registro, producto, aplicacion_general, aplicador, proxima_aplicacion)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha_registro, producto, tipo_aplicacion == 'general', aplicador, proxima_aplicacion))
        
        vitaminizacion_id = cursor.lastrowid
        
        if tipo_aplicacion == 'general':
            cursor.execute("INSERT INTO vitaminizacion_animal (vitaminizacion_id, animal_id) SELECT %s, id FROM animales", (vitaminizacion_id,))
        else:
            for animal_id in request.form.getlist('animales_seleccionados[]'):
                cursor.execute("INSERT INTO vitaminizacion_animal (vitaminizacion_id, animal_id) VALUES (%s, %s)", (vitaminizacion_id, animal_id))
        
        conn.commit()
        flash('Vitaminización registrada exitosamente', 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        app.logger.error(f'Error al registrar vitaminización: {str(e)}')
        flash(f'Error al registrar la vitaminización: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect(url_for('vitaminizacion'))

@app.route('/vitaminizacion/detalles/<int:id>')
@login_required
def detalles_vitaminizacion(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT v.*, DATE_FORMAT(v.fecha_registro, '%d/%m/%Y') as fecha_registro_formato,
                   DATE_FORMAT(v.proxima_aplicacion, '%d/%m/%Y') as proxima_aplicacion_formato
            FROM vitaminizacion v
            WHERE v.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        registro['fecha_registro'] = registro['fecha_registro_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN vitaminizacion_animal va ON a.id = va.animal_id
            WHERE va.vitaminizacion_id = %s
        """, (id,))
        registro['animales'] = cursor.fetchall()
        
        return jsonify(registro)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/fiebre_aftosa')
@login_required
def fiebre_aftosa():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(f.fecha_registro) 
                    FROM fiebre_aftosa f 
                    JOIN fiebre_aftosa_animal fa ON f.id = fa.fiebre_aftosa_id 
                    WHERE fa.animal_id = a.id) as ultima_vacunacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de fiebre aftosa
        cursor.execute("""
            SELECT f.*, 
                   (SELECT COUNT(*) 
                    FROM fiebre_aftosa_animal fa 
                    WHERE fa.fiebre_aftosa_id = f.id) as cantidad_animales
            FROM fiebre_aftosa f
            ORDER BY f.fecha_registro DESC
        """)
        registros = cursor.fetchall()
        
        # Obtener provincias para el formulario
        cursor.execute("SELECT * FROM provincias ORDER BY nombre")
        provincias = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('fiebre_aftosa.html', 
                             animales=animales, 
                             registros=registros,
                             provincias=provincias,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de fiebre aftosa: {str(e)}')
        flash('Error al cargar la página de fiebre aftosa', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/carbunco')
@login_required
def carbunco():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener todos los animales
        cursor.execute("""
            SELECT a.*, 
                   (SELECT MAX(c.fecha_registro) 
                    FROM carbunco c 
                    JOIN carbunco_animal ca ON c.id = ca.carbunco_id 
                    WHERE ca.animal_id = a.id) as ultima_vacunacion
            FROM animales a
            ORDER BY a.id DESC
        """)
        animales = cursor.fetchall()
        
        # Obtener registros de carbunco
        cursor.execute("""
            SELECT c.*, 
                   (SELECT COUNT(*) 
                    FROM carbunco_animal ca 
                    WHERE ca.carbunco_id = c.id) as cantidad_animales
            FROM carbunco c
            ORDER BY c.fecha_registro DESC
        """)
        registros = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('carbunco.html', 
                             animales=animales, 
                             registros=registros,
                             hoy=datetime.now().date())
    except Exception as e:
        app.logger.error(f'Error en la página de carbunco: {str(e)}')
        flash('Error al cargar la página de carbunco', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/registrar_carbunco', methods=['POST'])
@login_required
def registrar_carbunco():
    conn = None
    cursor = None
    try:
        fecha_registro = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        vacunador = request.form.get('vacunador')
        lote = request.form.get('lote')
        proxima_aplicacion = (datetime.strptime(fecha_registro, '%Y-%m-%d') + timedelta(days=180)).strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO carbunco 
            (fecha_registro, producto, aplicacion_general, vacunador, lote, proxima_aplicacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (fecha_registro, producto, tipo_aplicacion == 'general', vacunador, lote, proxima_aplicacion))
        
        carbunco_id = cursor.lastrowid
        
        if tipo_aplicacion == 'general':
            cursor.execute("INSERT INTO carbunco_animal (carbunco_id, animal_id) SELECT %s, id FROM animales", (carbunco_id,))
        else:
            for animal_id in request.form.getlist('animales_seleccionados[]'):
                cursor.execute("INSERT INTO carbunco_animal (carbunco_id, animal_id) VALUES (%s, %s)", (carbunco_id, animal_id))
        
        conn.commit()
        flash('Vacunación contra carbunco registrada exitosamente', 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        app.logger.error(f'Error al registrar vacunación de carbunco: {str(e)}')
        flash(f'Error al registrar la vacunación: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect(url_for('carbunco'))

@app.route('/carbunco/detalles/<int:id>')
@login_required
def detalles_carbunco(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT c.*, DATE_FORMAT(c.fecha_registro, '%d/%m/%Y') as fecha_registro_formato,
                   DATE_FORMAT(c.proxima_aplicacion, '%d/%m/%Y') as proxima_aplicacion_formato
            FROM carbunco c
            WHERE c.id = %s
        """, (id,))
        registro = cursor.fetchone()
        
        if not registro:
            return jsonify({'error': 'Registro no encontrado'}), 404
            
        registro['fecha_registro'] = registro['fecha_registro_formato']
        registro['proxima_aplicacion'] = registro['proxima_aplicacion_formato']
        
        cursor.execute("""
            SELECT a.* 
            FROM animales a
            JOIN carbunco_animal ca ON a.id = ca.animal_id
            WHERE ca.carbunco_id = %s
        """, (id,))
        registro['animales'] = cursor.fetchall()
        
        return jsonify(registro)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Se comentó esta ruta duplicada para evitar el error
# @app.route('/editar_empleado/<int:id>', methods=['POST'])
# @login_required
# def editar_empleado_duplicado(id):
#     try:
#         # Validar datos de entrada
#         nombre = request.form.get('nombre', '').strip()
#         apellido = request.form.get('apellido', '').strip()
#         cedula = request.form.get('cedula', '').strip()
#         telefono = request.form.get('telefono', '').strip()
#         direccion = request.form.get('direccion', '').strip()
#         cargo = request.form.get('cargo', '').strip()
#         fecha_contratacion = request.form.get('fecha_contratacion', '')
#         salario = request.form.get('salario', '')
#         estado = request.form.get('estado') == '1'
#         
#         # Validaciones
#         if not nombre or not apellido or not cedula or not cargo or not fecha_contratacion or not salario:
#             flash('Todos los campos obligatorios deben estar completos', 'error')
#             return redirect(url_for('empleados'))
#            
#         # Validar formato de cédula (10 dígitos)
#         if not cedula.isdigit() or len(cedula) != 10:
#             flash('La cédula debe tener 10 dígitos', 'error')
#             return redirect(url_for('empleados'))
#            
#         # Validar que el salario sea un número positivo
#         try:
#             salario_float = float(salario)
#             if salario_float <= 0:
#                 flash('El salario debe ser un valor positivo', 'error')
#                 return redirect(url_for('empleados'))
#         except ValueError:
#             flash('El salario debe ser un valor numérico', 'error')
#             return redirect(url_for('empleados'))
#            
#         with get_db_connection() as conn:
#             cursor = conn.cursor(dictionary=True)
#            
#             # Verificar si ya existe otro empleado con la misma cédula
#             cursor.execute("""
#                 SELECT id FROM empleados 
#                 WHERE cedula = %s AND id != %s
#             """, (cedula, id))
#            
#             if cursor.fetchone():
#                 flash('Ya existe otro empleado con esta cédula', 'error')
#                 return redirect(url_for('empleados'))
#                
#             # Realizar la actualización
#             cursor.execute("""
#                 UPDATE empleados 
#                 SET nombre = %s, apellido = %s, cedula = %s, telefono = %s,
#                     direccion = %s, cargo = %s, fecha_contratacion = %s,
#                     salario = %s, estado = %s
#                 WHERE id = %s
#             """, (
#                 nombre,
#                 apellido,
#                 cedula,
#                 telefono,
#                 direccion,
#                 cargo,
#                 fecha_contratacion,
#                 salario,
#                 estado,
#                 id
#             ))
#            
#             conn.commit()
#            
#             # Registrar la actualización en un log
#             app.logger.info(f"Empleado ID {id} actualizado por usuario {session.get('username')}")
#            
#             flash('Empleado actualizado exitosamente', 'success')
#     except Exception as e:
#         app.logger.error(f"Error al editar empleado: {e}")
#         flash('Error al actualizar el empleado: ' + str(e), 'error')
#        
#     return redirect(url_for('empleados'))

# @app.route('/eliminar_empleado/<int:id>', methods=['POST'])
# @login_required
# def eliminar_empleado_duplicado(id):
#     try:
#         with get_db_connection() as conn:
#             cursor = conn.cursor(dictionary=True)
#             
#             # Verificar si el empleado existe
#             cursor.execute("SELECT id, nombre, apellido FROM empleados WHERE id = %s", (id,))
#             empleado = cursor.fetchone()
#             
#             if not empleado:
#                 return jsonify({'success': False, 'error': 'Empleado no encontrado'})
#                 
#             # Verificar si hay asistencias asociadas
#             cursor.execute("SELECT COUNT(*) as total FROM asistencias WHERE empleado_id = %s", (id,))
#             asistencias = cursor.fetchone()['total']
#             
#             # Verificar si hay tareas asociadas
#             cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE empleado_id = %s", (id,))
#             tareas = cursor.fetchone()['total']
#             
#             # Si hay registros asociados, permitir eliminarlos o cancelar
#             if asistencias > 0 or tareas > 0:
#                 return jsonify({
#                     'success': False, 
#                     'error': 'No se puede eliminar el empleado porque tiene registros asociados',
#                     'asistencias': asistencias,
#                     'tareas': tareas,
#                     'requireConfirmation': True,
#                     'empleado': f"{empleado['nombre']} {empleado['apellido']}"
#                 })
#             
#             # Eliminar el empleado
#             cursor.execute("DELETE FROM empleados WHERE id = %s", (id,))
#             conn.commit()
#             
#             # Registrar la eliminación en un log
#             app.logger.info(f"Empleado ID {id} eliminado por usuario {session.get('username')}")
#             
#             return jsonify({'success': True})
#     except Exception as e:
#         app.logger.error(f"Error al eliminar empleado: {e}")
#         return jsonify({'success': False, 'error': str(e)})

@app.route('/eliminar_empleado_confirmado/<int:id>', methods=['POST'])
@login_required
def eliminar_empleado_confirmado(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Eliminar registros relacionados
            cursor.execute("DELETE FROM asistencias WHERE empleado_id = %s", (id,))
            cursor.execute("DELETE FROM tareas WHERE empleado_id = %s", (id,))
            
            # Finalmente eliminar el empleado
            cursor.execute("DELETE FROM empleados WHERE id = %s", (id,))
            conn.commit()
            
            # Registrar la eliminación en un log
            app.logger.info(f"Empleado ID {id} y sus registros asociados eliminados por usuario {session.get('username')}")
            
            return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error al eliminar empleado y sus registros: {e}")
        return jsonify({'success': False, 'error': str(e)})

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Crear tabla de inseminaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inseminaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha_inseminacion DATE NOT NULL,
                tipo_inseminacion VARCHAR(50) NOT NULL,
                semental VARCHAR(100) NOT NULL,
                exitosa BOOLEAN NOT NULL DEFAULT FALSE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Lista de columnas a verificar y agregar si no existen
        columnas = [
            ("tipo_inseminacion", "VARCHAR(50) NOT NULL", "fecha_inseminacion"),
            ("semental", "VARCHAR(100) NOT NULL", "tipo_inseminacion"),
            ("exitosa", "BOOLEAN NOT NULL DEFAULT FALSE", "semental")
        ]
        
        for columna, definicion, after in columnas:
            # Verificar si la columna existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'inseminaciones' 
                AND column_name = %s
            """, (columna,))
            
            if cursor.fetchone()[0] == 0:
                # Agregar columna si no existe
                cursor.execute(f"""
                    ALTER TABLE inseminaciones 
                    ADD COLUMN {columna} {definicion} 
                    AFTER {after}
                """)
        
        conn.commit()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
    try:
        # Crear tabla de inseminaciones si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inseminaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                animal_id INT NOT NULL,
                fecha_inseminacion DATE NOT NULL,
                tipo_inseminacion VARCHAR(50) NOT NULL,
                semental VARCHAR(100) NOT NULL,
                exitosa BOOLEAN NOT NULL DEFAULT FALSE,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animales(id)
            )
        """)
        
        # Lista de columnas a verificar y agregar si no existen
        columnas = [
            ("tipo_inseminacion", "VARCHAR(50) NOT NULL", "fecha_inseminacion"),
            ("semental", "VARCHAR(100) NOT NULL", "tipo_inseminacion"),
            ("exitosa", "BOOLEAN NOT NULL DEFAULT FALSE", "semental")
        ]
        
        for columna, definicion, after in columnas:
            # Verificar si la columna existe
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'inseminaciones' 
                AND column_name = %s
            """, (columna,))
            
            if cursor.fetchone()[0] == 0:
                # Agregar columna si no existe
                cursor.execute(f"""
                    ALTER TABLE inseminaciones 
                    ADD COLUMN {columna} {definicion} 
                    AFTER {after}
                """)
        
        conn.commit()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
