# Script para corregir el problema con el registro de carbunco
import sys
import os
sys.path.append(os.getcwd())

from src.database import get_db_connection

def arreglar_carbunco():
    print("\n====== CORRIGIENDO PROBLEMA DE REGISTRO DE CARBUNCO ======\n")
    
    try:
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar la tabla vacuna
        print("Verificando la tabla vacuna...")
        cursor.execute("""
            DESCRIBE vacuna
        """)
        columnas = [col[0] for col in cursor.fetchall()]
        print(f"Columnas actuales: {columnas}")
        
        # Añadir la columna usuario_id si no existe
        if 'usuario_id' not in columnas:
            print("Añadiendo columna usuario_id a la tabla vacuna...")
            cursor.execute("""
                ALTER TABLE vacuna
                ADD COLUMN usuario_id INT DEFAULT 1
            """)
            conn.commit()
            print("Columna usuario_id añadida correctamente")
        else:
            print("La columna usuario_id ya existe en la tabla vacuna")
        
        # Ahora corregiremos el archivo app.py para asegurarnos de que la función registrar_carbunco sea correcta
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
        
        # Modificar la consulta SQL para no incluir usuario_id si no existe
        modified_function = original_function.replace(
            "(fecha_registro, producto, lote, vacunador, aplicacion_general, proxima_aplicacion, usuario_id)",
            "(fecha_registro, producto, lote, vacunador, aplicacion_general, proxima_aplicacion)"
        ).replace(
            ", session['usuario_id'])",
            ")"
        )
        
        # Cambiar la consulta para insertar en la tabla carbunco en lugar de vacuna
        if "INSERT INTO vacuna" in modified_function:
            modified_function = modified_function.replace(
                "INSERT INTO vacuna", 
                "INSERT INTO carbunco"
            )
        
        # Crear un nuevo archivo con la función corregida
        app_new_path = os.path.join(os.getcwd(), 'app_new.py')
        new_content = content.replace(original_function, modified_function)
        
        with open(app_new_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print("\nSe ha creado un nuevo archivo app_new.py con la función corregida")
        print("Para aplicar los cambios:")
        print("1. Detén el servidor web")
        print("2. Reemplaza app.py con app_new.py (cambia el nombre)")
        print("3. Reinicia el servidor web")
        
        print("\n====== CORRECCIÓN COMPLETA ======\n")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    arreglar_carbunco()
