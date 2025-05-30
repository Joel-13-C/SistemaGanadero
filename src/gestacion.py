from datetime import datetime, timedelta
from src.database import get_db_connection
from flask import flash

def registrar_gestacion(animal_id, fecha_monta, observaciones):
    try:
        # Validar que el animal existe y es hembra
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, sexo, condicion 
            FROM animales 
            WHERE id = %s
        """, (animal_id,))
        animal = cursor.fetchone()
        
        if not animal:
            return False, "Animal no encontrado"
        
        if animal['sexo'] != 'Hembra':
            return False, "Solo se puede registrar gestación para animales hembra"
            
        if animal['condicion'] not in ['Vaca', 'Vacona']:
            return False, "Solo se puede registrar gestación para vacas o vaconas"
        
        # Calcular fecha probable de parto (283 días después de la monta)
        fecha_monta_obj = datetime.strptime(fecha_monta, '%Y-%m-%d')
        fecha_probable_parto = fecha_monta_obj + timedelta(days=283)
        
        # Verificar si ya existe una gestación activa
        cursor.execute("""
            SELECT id FROM gestaciones 
            WHERE animal_id = %s AND estado = 'En Gestación'
        """, (animal_id,))
        
        if cursor.fetchone():
            return False, "Este animal ya tiene una gestación activa registrada"
        
        # Insertar el registro de gestación
        cursor.execute("""
            INSERT INTO gestaciones (animal_id, fecha_inseminacion, tipo_inseminacion, 
                                semental, observaciones, estado)
            VALUES (%s, %s, 'Natural', 'No especificado', %s, 'En Gestación')
        """, (animal_id, fecha_monta, observaciones))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Gestación registrada exitosamente"
        
    except Exception as e:
        return False, f"Error al registrar la gestación: {str(e)}"

def obtener_gestaciones():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT g.*, a.numero_arete, a.nombre, a.condicion
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            ORDER BY g.fecha_actualizacion DESC
        """)
        
        gestaciones = cursor.fetchall()
        
        # Calcular días restantes para cada gestación y actualizar estado si es necesario
        for g in gestaciones:
            if g['estado'] == 'En Gestación':
                # Calcular fecha probable de parto (283 días después de la inseminación)
                fecha_probable_parto = g['fecha_inseminacion'] + timedelta(days=283)
                dias_restantes = (fecha_probable_parto - datetime.now().date()).days
                g['dias_restantes'] = max(0, dias_restantes)
                # Agregar la fecha probable de parto al diccionario para usarla en la plantilla
                g['fecha_probable_parto'] = fecha_probable_parto
                
                # Si los días restantes son 0 y el estado aún es 'En Gestación', actualizarlo
                if g['dias_restantes'] == 0:
                    observacion = f"\n[{datetime.now().strftime('%Y-%m-%d')}] Parto detectado automáticamente por el sistema."
                    cursor.execute("""
                        UPDATE gestaciones 
                        SET estado = 'Finalizado',
                            observaciones = CONCAT(IFNULL(observaciones, ''), %s)
                        WHERE id = %s AND estado = 'En Gestación'
                    """, (observacion, g['id']))
                    conn.commit()
                    g['estado'] = 'Finalizado'
                    g['observaciones'] = (g['observaciones'] or '') + observacion
            else:
                g['dias_restantes'] = 0
        
        cursor.close()
        conn.close()
        
        return gestaciones
        
    except Exception as e:
        print(f"Error al obtener gestaciones: {str(e)}")
        return []

def obtener_gestaciones_proximas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Obtener gestaciones que están a 7 días o menos del parto y aún están activas
        cursor.execute("""
            SELECT g.*, a.numero_arete, a.nombre, a.condicion,
                   DATEDIFF(DATE_ADD(g.fecha_inseminacion, INTERVAL 283 DAY), CURDATE()) as dias_restantes
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.estado = 'En Gestación'
            AND DATEDIFF(DATE_ADD(g.fecha_inseminacion, INTERVAL 283 DAY), CURDATE()) BETWEEN 0 AND 7
            ORDER BY g.fecha_inseminacion ASC
        """)
        
        gestaciones_proximas = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return gestaciones_proximas
        
    except Exception as e:
        print(f"Error al obtener gestaciones próximas: {str(e)}")
        return []

def actualizar_estado_gestacion(gestacion_id, nuevo_estado, observaciones=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_query = """
            UPDATE gestaciones 
            SET estado = %s, observaciones = CONCAT(IFNULL(observaciones, ''), '\n', %s)
            WHERE id = %s
        """
        
        observacion_estado = f"\n[{datetime.now().strftime('%Y-%m-%d')}] Cambio de estado a: {nuevo_estado}"
        if observaciones:
            observacion_estado += f" - {observaciones}"
            
        cursor.execute(update_query, (nuevo_estado, observacion_estado, gestacion_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Estado de gestación actualizado correctamente"
        
    except Exception as e:
        return False, f"Error al actualizar el estado: {str(e)}"

def obtener_gestacion_por_id(gestacion_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT g.*, a.numero_arete, a.nombre, a.condicion
            FROM gestaciones g
            JOIN animales a ON g.animal_id = a.id
            WHERE g.id = %s
        """, (gestacion_id,))
        
        gestacion = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if gestacion:
            # Calcular fecha probable de parto (283 días después de la inseminación)
            if gestacion['fecha_inseminacion']:
                fecha_probable_parto = gestacion['fecha_inseminacion'] + timedelta(days=283)
                gestacion['fecha_probable_parto'] = fecha_probable_parto
                
            return True, gestacion
        else:
            return False, "Gestación no encontrada"
        
    except Exception as e:
        return False, f"Error al obtener la gestación: {str(e)}"

def editar_gestacion(gestacion_id, fecha_inseminacion, observaciones):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que la gestación existe
        cursor.execute("SELECT id FROM gestaciones WHERE id = %s", (gestacion_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Gestación no encontrada"
        
        # Actualizar la gestación
        update_query = """
            UPDATE gestaciones 
            SET fecha_inseminacion = %s, 
                observaciones = CONCAT(IFNULL(observaciones, ''), '\n', %s)
            WHERE id = %s
        """
        
        observacion_edicion = f"\n[{datetime.now().strftime('%Y-%m-%d')}] Fecha de inseminación actualizada a: {fecha_inseminacion}"
        if observaciones:
            observacion_edicion += f"\nObservaciones adicionales: {observaciones}"
            
        cursor.execute(update_query, (fecha_inseminacion, observacion_edicion, gestacion_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Gestación actualizada correctamente"
        
    except Exception as e:
        return False, f"Error al actualizar la gestación: {str(e)}"

def eliminar_gestacion(gestacion_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que la gestación existe
        cursor.execute("SELECT id FROM gestaciones WHERE id = %s", (gestacion_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Gestación no encontrada"
        
        # Eliminar la gestación
        cursor.execute("DELETE FROM gestaciones WHERE id = %s", (gestacion_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, "Gestación eliminada correctamente"
        
    except Exception as e:
        return False, f"Error al eliminar la gestación: {str(e)}"
