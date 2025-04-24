# Script para añadir el método obtener_configuracion_alarmas a la clase SistemaAlarmas
import os

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')

# Leer el contenido del archivo
with open(alarmas_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Método que falta
nuevo_metodo = '''
    def obtener_configuracion_alarmas(self):
        """
        Obtiene la configuración de alarmas del usuario actual
        
        Returns:
            dict: Diccionario con la configuración de alarmas
        """
        try:
            # Obtener el ID del usuario actual
            usuario_id = session.get('usuario_id')
            if not usuario_id:
                logger.info("No hay usuario en sesión para obtener configuración de alarmas")
                return {}
            
            conn = self.db_connection()
            if not conn:
                logger.error("No se pudo conectar a la base de datos para obtener configuración de alarmas")
                return {}
                
            cursor = conn.cursor(dictionary=True)
            
            # Obtener configuraciones de alarmas
            cursor.execute("""
                SELECT * FROM config_alarmas
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            configuraciones = cursor.fetchall()
            
            # Organizar por tipo
            config = {}
            for c in configuraciones:
                config[c['tipo']] = {
                    'activo': c['activo'],
                    'email': c['email'],
                    'dias_anticipacion': c['dias_anticipacion']
                }
            
            cursor.close()
            conn.close()
            
            return config
            
        except Exception as e:
            logger.error(f"Error al obtener configuración de alarmas: {e}")
            return {}
'''

# Buscar la posición adecuada para añadir el método (después del método desactivar_alarma)
pos = content.find("def desactivar_alarma")
if pos != -1:
    # Buscar el final del método
    pos_fin = content.find("def ", pos + 20)
    if pos_fin != -1:
        # Añadir el nuevo método después de desactivar_alarma
        content_nuevo = content[:pos_fin] + nuevo_metodo + content[pos_fin:]
        
        # Guardar el archivo modificado
        with open(alarmas_path, 'w', encoding='utf-8') as file:
            file.write(content_nuevo)
        
        print("Método obtener_configuracion_alarmas añadido a la clase SistemaAlarmas")
    else:
        print("No se pudo encontrar el final del método desactivar_alarma")
else:
    print("No se pudo encontrar el método desactivar_alarma para añadir después")
