# Script para corregir el archivo alarmas.py
import os

# Ruta al archivo de alarmas
alarmas_path = os.path.join(os.getcwd(), 'src', 'alarmas.py')

# Leer el contenido del archivo
with open(alarmas_path, 'r', encoding='utf-8') as file:
    content = file.readlines()

# Encontrar dónde termina el método anterior y dónde comienza el nuevo
end_previous = -1
start_new = -1

for i, line in enumerate(content):
    if 'return notificaciones_enviadas' in line and end_previous == -1:
        end_previous = i
    if 'def verificar_vitaminizaciones_pendientes' in line:
        start_new = i
        break

# Verificar que encontramos ambas posiciones
if end_previous != -1 and start_new != -1:
    # La nueva función debe comenzar después del cierre del método anterior
    # y debe estar correctamente indentada
    
    # Texto de la nueva función correctamente formateada
    nueva_funcion = [
        "    def verificar_vitaminizaciones_pendientes(self):\n",
        "        \"\"\"\n",
        "        Verifica si hay vitaminizaciones pendientes y envía notificaciones\n",
        "        \n",
        "        Returns:\n",
        "            int: Número de notificaciones enviadas\n",
        "        \"\"\"\n",
        "        try:\n",
        "            print(\"\\n==== INICIANDO VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES ====\\n\")\n",
        "            \n",
        "            conn = self.db_connection()\n",
        "            if not conn:\n",
        "                logger.error(\"No se pudo conectar a la base de datos para verificar vitaminizaciones pendientes\")\n",
        "                print(\"Error: No se pudo conectar a la base de datos\")\n",
        "                return 0\n",
        "                \n",
        "            cursor = conn.cursor(dictionary=True)\n",
        "            \n",
        "            # Obtener configuraciones de alarmas de vitaminización activas\n",
        "            query_config = \"SELECT * FROM config_alarmas WHERE tipo = 'vitaminizacion' AND activo = TRUE\"\n",
        "            print(f\"Ejecutando consulta: {query_config}\")\n",
        "            \n",
        "            cursor.execute(query_config)\n",
        "            \n",
        "            configuraciones = cursor.fetchall()\n",
        "            print(f\"Configuraciones de alarmas activas encontradas: {len(configuraciones)}\")\n",
        "            \n",
        "            # Si no hay configuraciones, usar una configuración predeterminada con el correo configurado\n",
        "            if not configuraciones:\n",
        "                logger.info(\"No hay configuraciones de alarmas de vitaminización activas, usando configuración predeterminada\")\n",
        "                print(\"No hay configuraciones de alarmas de vitaminización activas. Usando configuración predeterminada.\")\n",
        "                \n",
        "                # Crear una configuración predeterminada\n",
        "                configuraciones = [{\n",
        "                    'usuario_id': 1,  # Usuario administrador por defecto\n",
        "                    'dias_anticipacion': 7,  # 7 días de anticipación\n",
        "                    'email': self.email_config['username']  # Usar el correo configurado\n",
        "                }]\n",
        "            \n",
        "            notificaciones_enviadas = 0\n",
        "            \n",
        "            # Para cada configuración, buscar vitaminizaciones pendientes\n",
        "            for config in configuraciones:\n",
        "                usuario_id = config['usuario_id']\n",
        "                dias_anticipacion = config['dias_anticipacion']\n",
        "                email = config['email']\n",
        "                \n",
        "                # Calcular la fecha límite\n",
        "                fecha_limite = datetime.now() + timedelta(days=dias_anticipacion)\n",
        "                \n",
        "                # Imprimir información de depuración\n",
        "                print(f\"Buscando vitaminizaciones para usuario_id: {usuario_id}, con fecha límite: {fecha_limite.strftime('%Y-%m-%d')}\")\n",
        "                \n",
        "                # Buscar vitaminizaciones pendientes\n",
        "                query = \"\"\"\n",
        "                    SELECT v.*, GROUP_CONCAT(a.id) as animal_ids, \n",
        "                           GROUP_CONCAT(a.nombre) as nombres_animales,\n",
        "                           GROUP_CONCAT(a.numero_arete) as aretes_animales\n",
        "                    FROM vitaminizacion v\n",
        "                    JOIN vitaminizacion_animal va ON v.id = va.vitaminizacion_id\n",
        "                    JOIN animales a ON va.animal_id = a.id\n",
        "                    WHERE v.proxima_aplicacion <= %s\n",
        "                    AND v.proxima_aplicacion >= CURDATE()\n",
        "                    GROUP BY v.id\n",
        "                \"\"\"\n",
        "                \n",
        "                print(f\"Ejecutando consulta: {query}\")\n",
        "                print(f\"Con parámetros: {fecha_limite.strftime('%Y-%m-%d')}\")\n",
        "                \n",
        "                cursor.execute(query, (fecha_limite.strftime('%Y-%m-%d'),))\n",
        "                \n",
        "                vitaminizaciones = cursor.fetchall()\n",
        "                print(f\"Vitaminizaciones pendientes encontradas: {len(vitaminizaciones)}\")\n",
        "                \n",
        "                if vitaminizaciones:\n",
        "                    print(\"\\n==== DETALLES DE VITAMINIZACIONES PENDIENTES ====\\n\")\n",
        "                    for v in vitaminizaciones:\n",
        "                        dias_restantes = (v['proxima_aplicacion'] - datetime.now().date()).days\n",
        "                        print(f\"Vitaminización: ID={v['id']}, Producto={v['producto']}\")\n",
        "                        print(f\"  Fecha próxima aplicación: {v['proxima_aplicacion']}\")\n",
        "                        print(f\"  Días restantes: {dias_restantes}\")\n",
        "                        print(f\"  Animales: {v['nombres_animales']}\")\n",
        "                        print(\"  ----------------------------------------\")\n",
        "                \n",
        "                if vitaminizaciones:\n",
        "                    # Enviar notificaciones para estas vitaminizaciones\n",
        "                    for vitaminizacion in vitaminizaciones:\n",
        "                        # Calcular días restantes\n",
        "                        dias_restantes = (vitaminizacion['proxima_aplicacion'] - datetime.now().date()).days\n",
        "                        \n",
        "                        # Preparar lista de animales\n",
        "                        nombres_animales = vitaminizacion['nombres_animales'].split(',') if vitaminizacion['nombres_animales'] else []\n",
        "                        aretes_animales = vitaminizacion['aretes_animales'].split(',') if vitaminizacion['aretes_animales'] else []\n",
        "                        \n",
        "                        # Crear lista formateada de animales\n",
        "                        lista_animales = \"\"\n",
        "                        for i in range(min(len(nombres_animales), len(aretes_animales))):\n",
        "                            lista_animales += f\"- {nombres_animales[i]} (Arete: {aretes_animales[i]})\\n\"\n",
        "                        \n",
        "                        # Preparar el asunto del correo\n",
        "                        asunto = f\"ALERTA: Vitaminización pendiente - {vitaminizacion['producto']} en {dias_restantes} días\"\n",
        "                        \n",
        "                        # Preparar el mensaje del correo\n",
        "                        mensaje = f\"\"\"\n",
        "                        ALERTA DE VITAMINIZACIÓN PENDIENTE\n",
        "                        \n",
        "                        Hay una vitaminización programada próximamente.\n",
        "                        \n",
        "                        Detalles:\n",
        "                        - Producto: {vitaminizacion['producto']}\n",
        "                        - Fecha de aplicación: {vitaminizacion['proxima_aplicacion'].strftime('%d/%m/%Y')}\n",
        "                        - Días restantes: {dias_restantes}\n",
        "                        \n",
        "                        Animales que requieren vitaminización:\n",
        "                        {lista_animales}\n",
        "                        \n",
        "                        Por favor, prepare todo lo necesario para realizar la vitaminización.\n",
        "                        \"\"\"\n",
        "                        \n",
        "                        # Enviar la notificación\n",
        "                        print(f\"Enviando notificación de vitaminización a {email}:\")\n",
        "                        print(f\"Asunto: {asunto}\")\n",
        "                        print(f\"Mensaje: {mensaje[:100]}...\")\n",
        "                        \n",
        "                        enviado = self._enviar_notificacion_email(email, asunto, mensaje)\n",
        "                        \n",
        "                        if enviado:\n",
        "                            # Registrar la notificación en la base de datos\n",
        "                            cursor.execute(\"\"\"\n",
        "                                INSERT INTO alarmas_enviadas\n",
        "                                (tipo, referencia_id, email, asunto, mensaje, fecha_envio)\n",
        "                                VALUES (%s, %s, %s, %s, %s, NOW())\n",
        "                            \"\"\", (\n",
        "                                'vitaminizacion',\n",
        "                                vitaminizacion['id'],\n",
        "                                email,\n",
        "                                asunto,\n",
        "                                mensaje\n",
        "                            ))\n",
        "                            conn.commit()\n",
        "                            notificaciones_enviadas += 1\n",
        "                            print(f\"Notificación registrada en la base de datos. Total enviadas: {notificaciones_enviadas}\")\n",
        "            \n",
        "            cursor.close()\n",
        "            conn.close()\n",
        "            \n",
        "            print(\"\\n==== VERIFICACIÓN DE VITAMINIZACIONES PENDIENTES FINALIZADA ====\\n\")\n",
        "            print(f\"Total de notificaciones enviadas: {notificaciones_enviadas}\")\n",
        "            \n",
        "            return notificaciones_enviadas\n",
        "            \n",
        "        except Exception as e:\n",
        "            logger.error(f\"Error al verificar vitaminizaciones pendientes: {e}\")\n",
        "            print(f\"Error: {e}\")\n",
        "            return 0\n"
    ]
    
    # Reorganizar el contenido del archivo
    nuevo_contenido = content[:end_previous+1] + nueva_funcion + content[start_new+len(nueva_funcion):]
    
    # Guardar el archivo corregido
    with open(alarmas_path, 'w', encoding='utf-8') as file:
        file.writelines(nuevo_contenido)
    
    print("Se ha corregido el archivo alarmas.py")
    
else:
    print(f"No se pudieron encontrar las posiciones necesarias. end_previous={end_previous}, start_new={start_new}")
