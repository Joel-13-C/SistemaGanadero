import re

def restore_equipos_function():
    try:
        # Leer el archivo app.py
        with open('app.py', 'r', encoding='utf-8') as file:
            content = file.read()

        # Buscar dónde insertar la función equipos
        # Buscaremos después de la función trazabilidad
        trazabilidad_pattern = r'@app\.route\(\'/trazabilidad\'\)[\s\S]*?def trazabilidad\(\):[\s\S]*?return render_template\(\'trazabilidad\.html\', animales=animales\)'
        
        # Encontrar la posición donde insertar
        match = re.search(trazabilidad_pattern, content)
        if match:
            insert_pos = match.end()
            
            # Función equipos segura para insertar
            equipos_function = """

@app.route('/equipos')
@login_required
def equipos():
    # Versión segura que no accede a la base de datos
    flash('El módulo de equipos está temporalmente deshabilitado por mantenimiento.', 'warning')
    return render_template('mantenimiento.html', 
                          titulo="Módulo en Mantenimiento", 
                          mensaje="El módulo de gestión de equipos está temporalmente deshabilitado por mantenimiento.")
"""
            
            # Insertar la función
            new_content = content[:insert_pos] + equipos_function + content[insert_pos:]
            
            # Escribir el nuevo contenido al archivo
            with open('app.py', 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            print("Función equipos restaurada exitosamente")
            
            # Crear la plantilla de mantenimiento si no existe
            try:
                with open('templates/mantenimiento.html', 'w', encoding='utf-8') as file:
                    file.write("""{% extends "base.html" %}

{% block content %}
<div class="container mt-5">
    <div class="card">
        <div class="card-header bg-warning text-white">
            <h2><i class="fas fa-tools"></i> {{ titulo }}</h2>
        </div>
        <div class="card-body text-center">
            <div class="mb-4">
                <i class="fas fa-cogs" style="font-size: 5rem; color: #ffc107;"></i>
            </div>
            <h3>{{ mensaje }}</h3>
            <p class="lead">Estamos trabajando para solucionar los problemas y mejorar la funcionalidad.</p>
            <p>Por favor, intente acceder más tarde o contacte al administrador del sistema si necesita asistencia inmediata.</p>
            <a href="{{ url_for('dashboard') }}" class="btn btn-primary mt-3">
                <i class="fas fa-home"></i> Volver al Inicio
            </a>
        </div>
    </div>
</div>
{% endblock %}""")
                print("Plantilla de mantenimiento creada exitosamente")
            except Exception as e:
                print(f"Error al crear la plantilla de mantenimiento: {str(e)}")
        else:
            print("No se pudo encontrar un lugar adecuado para insertar la función equipos")
            
    except Exception as e:
        print(f"Error al restaurar la función equipos: {str(e)}")

if __name__ == "__main__":
    restore_equipos_function()
