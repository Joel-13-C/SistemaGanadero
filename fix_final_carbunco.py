# Script para corregir definitivamente el problema con el registro de carbunco
import sys
import os
import re
sys.path.append(os.getcwd())

from src.database import get_db_connection

def arreglar_carbunco_final():
    print("\n====== CORRECCIÓN FINAL DEL REGISTRO DE CARBUNCO ======\n")
    
    try:
        # Obtener el archivo app.py
        app_path = os.path.join(os.getcwd(), 'app.py')
        
        # Leer el contenido del archivo
        with open(app_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Buscar la función registrar_carbunco
        start_idx = content.find("def registrar_carbunco()")
        if start_idx == -1:
            print("No se encontró la función registrar_carbunco")
            return
        
        # Encontrar el final de la función
        next_def = content.find("def ", start_idx + 10)
        end_idx = next_def if next_def != -1 else content.find("if __name__ ==", start_idx)
        
        # Extraer la función original
        original_function = content[start_idx:end_idx]
        
        # Crear la nueva función corregida
        corrected_function = """def registrar_carbunco():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        fecha_registro = request.form.get('fecha_registro')
        producto = request.form.get('producto')
        if producto == 'otro':
            producto = request.form.get('otro_producto')
        lote = request.form.get('lote')
        vacunador = request.form.get('vacunador')
        tipo_aplicacion = request.form.get('tipo_aplicacion')
        
        # Calcular próxima aplicación (6 meses después)
        proxima_aplicacion = (datetime.strptime(fecha_registro, '%Y-%m-%d') + timedelta(days=180)).strftime('%Y-%m-%d')
        
        # Consulta corregida sin usuario_id
        cursor.execute(\"\"\"
            INSERT INTO carbunco 
            (fecha_registro, producto, lote, vacunador, aplicacion_general, proxima_aplicacion)
            VALUES (%s, %s, %s, %s, %s, %s)
        \"\"\", (fecha_registro, producto, lote, vacunador, tipo_aplicacion == 'general', proxima_aplicacion))
        
        carbunco_id = cursor.lastrowid
        
        if tipo_aplicacion == 'general':
            cursor.execute(\"INSERT INTO carbunco_animal (carbunco_id, animal_id) SELECT %s, id FROM animales\", (carbunco_id,))
        else:
            for animal_id in request.form.getlist('animales_seleccionados[]'):
                cursor.execute(\"INSERT INTO carbunco_animal (carbunco_id, animal_id) VALUES (%s, %s)\", (carbunco_id, animal_id))
        
        conn.commit()
        flash('Vacunación contra Carbunco registrada exitosamente', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al registrar la vacunación: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('carbunco'))
"""
        
        # Reemplazar la función en el contenido
        pattern = r"def registrar_carbunco\(\):.*?return redirect\(url_for\('carbunco'\)\)"
        updated_content = re.sub(pattern, corrected_function, content, flags=re.DOTALL)
        
        # Crear un nuevo archivo con el contenido actualizado
        app_final_path = os.path.join(os.getcwd(), 'app_final.py')
        with open(app_final_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        print("Se ha creado un nuevo archivo app_final.py con la corrección completa")
        print("Para aplicar los cambios:")
        print("1. Detén el servidor web (Ctrl+C)")
        print("2. Reemplaza app.py con app_final.py:")
        print("   copy app_final.py app.py")
        print("3. Reinicia el servidor web:")
        print("   python app.py")
        
        print("\n====== CORRECCIÓN COMPLETA ======\n")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    arreglar_carbunco_final()
