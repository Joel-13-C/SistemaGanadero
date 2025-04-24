"""
Módulo para gestionar la recuperación de contraseñas en el Sistema Ganadero.
Este módulo implementa las funciones necesarias para:
1. Verificar si un correo existe en la base de datos
2. Generar tokens de recuperación
3. Almacenar y validar tokens
4. Enviar correos electrónicos con instrucciones
"""
import os
import re
import hashlib
import secrets
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.database import get_db_connection

class RecuperacionContrasena:
    def __init__(self, app=None):
        """
        Inicializa el sistema de recuperación de contraseñas.
        
        Args:
            app: Instancia de la aplicación Flask
        """
        self.app = app
        
        # Configuración de correo electrónico
        self.email_sender = "fernando05calero@gmail.com"  # Usar el mismo correo configurado para notificaciones
        self.email_password = "mqsl wlvi usjb kfzl"  # Contraseña de aplicación configurada directamente
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def email_exists(self, email):
        """
        Verifica si un correo electrónico existe en la base de datos.
        
        Args:
            email: Correo electrónico a verificar
            
        Returns:
            dict: Información del usuario si existe, None en caso contrario
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT id, username, email 
                FROM usuarios 
                WHERE email = %s
            """, (email,))
            
            usuario = cursor.fetchone()
            return usuario
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Error al verificar correo: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def generar_token(self, length=32):
        """
        Genera un token seguro para recuperación de contraseña.
        
        Args:
            length: Longitud del token
            
        Returns:
            str: Token generado
        """
        return secrets.token_hex(length)
    
    def guardar_token(self, usuario_id, token, expiracion_horas=24):
        """
        Guarda un token de recuperación en la base de datos.
        
        Args:
            usuario_id: ID del usuario
            token: Token generado
            expiracion_horas: Horas de validez del token
            
        Returns:
            bool: True si se guardó correctamente, False en caso contrario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Verificar si existe la tabla de tokens
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'sistema_ganadero' 
                AND table_name = 'tokens_recuperacion'
            """)
            
            if cursor.fetchone()[0] == 0:
                # Crear la tabla si no existe
                cursor.execute("""
                    CREATE TABLE tokens_recuperacion (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        usuario_id INT NOT NULL,
                        token VARCHAR(100) NOT NULL,
                        fecha_expiracion DATETIME NOT NULL,
                        usado BOOLEAN DEFAULT FALSE,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                    )
                """)
                conn.commit()
            
            # Calcular fecha de expiración
            fecha_expiracion = (datetime.datetime.now() + 
                               datetime.timedelta(hours=expiracion_horas)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Eliminar tokens anteriores del mismo usuario
            cursor.execute("""
                DELETE FROM tokens_recuperacion 
                WHERE usuario_id = %s
            """, (usuario_id,))
            
            # Guardar nuevo token
            cursor.execute("""
                INSERT INTO tokens_recuperacion 
                (usuario_id, token, fecha_expiracion) 
                VALUES (%s, %s, %s)
            """, (usuario_id, token, fecha_expiracion))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            if self.app:
                self.app.logger.error(f"Error al guardar token: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def verificar_token(self, token):
        """
        Verifica si un token es válido y no ha expirado.
        
        Args:
            token: Token a verificar
            
        Returns:
            dict: Información del usuario si el token es válido, None en caso contrario
        """
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT t.id as token_id, t.usuario_id, t.fecha_expiracion, t.usado,
                       u.username, u.email
                FROM tokens_recuperacion t
                JOIN usuarios u ON t.usuario_id = u.id
                WHERE t.token = %s AND t.usado = FALSE
            """, (token,))
            
            resultado = cursor.fetchone()
            
            if not resultado:
                return None
                
            # Verificar si el token ha expirado
            fecha_expiracion = datetime.datetime.strptime(
                resultado['fecha_expiracion'].strftime('%Y-%m-%d %H:%M:%S'), 
                '%Y-%m-%d %H:%M:%S'
            )
            
            if datetime.datetime.now() > fecha_expiracion:
                return None
                
            return resultado
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Error al verificar token: {str(e)}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def marcar_token_usado(self, token_id):
        """
        Marca un token como usado.
        
        Args:
            token_id: ID del token
            
        Returns:
            bool: True si se marcó correctamente, False en caso contrario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE tokens_recuperacion 
                SET usado = TRUE 
                WHERE id = %s
            """, (token_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            if self.app:
                self.app.logger.error(f"Error al marcar token como usado: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def actualizar_contrasena(self, usuario_id, nueva_contrasena):
        """
        Actualiza la contraseña de un usuario.
        
        Args:
            usuario_id: ID del usuario
            nueva_contrasena: Nueva contraseña (sin hashear)
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Hashear la contraseña
            hashed_password = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
            
            cursor.execute("""
                UPDATE usuarios 
                SET password = %s 
                WHERE id = %s
            """, (hashed_password, usuario_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            if self.app:
                self.app.logger.error(f"Error al actualizar contraseña: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def enviar_correo_recuperacion(self, email, username, token, base_url):
        """
        Envía un correo electrónico con instrucciones para recuperar la contraseña.
        
        Args:
            email: Correo electrónico del destinatario
            username: Nombre de usuario
            token: Token de recuperación
            base_url: URL base de la aplicación
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Configurar el mensaje
            mensaje = MIMEMultipart()
            mensaje['From'] = self.email_sender
            mensaje['To'] = email
            mensaje['Subject'] = "Recuperación de contraseña - Sistema Ganadero"
            
            # Construir la URL de recuperación
            url_recuperacion = f"{base_url}/restablecer-contrasena/{token}"
            
            # Cuerpo del mensaje
            cuerpo = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 5px;">
                    <h2 style="color: #4CAF50; text-align: center;">Sistema Ganadero</h2>
                    <h3>Hola {username},</h3>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
                    <p>Para continuar con el proceso, haz clic en el siguiente enlace:</p>
                    <p style="text-align: center;">
                        <a href="{url_recuperacion}" style="display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            Restablecer Contraseña
                        </a>
                    </p>
                    <p>Este enlace expirará en 24 horas.</p>
                    <p>Si no solicitaste restablecer tu contraseña, puedes ignorar este mensaje.</p>
                    <p>Saludos,<br>Equipo de Sistema Ganadero</p>
                </div>
            </body>
            </html>
            """
            
            mensaje.attach(MIMEText(cuerpo, 'html'))
            
            # La contraseña ya está configurada directamente en el constructor
            # pero podemos hacer una verificación adicional
            if not self.email_password:
                # Usar la contraseña de las alarmas como respaldo
                try:
                    from src.alarmas import SistemaAlarmas
                    # Inicializar con None porque no necesitamos la conexión a la BD aquí
                    alarmas = SistemaAlarmas(None)
                    # Obtener la contraseña de la configuración de alarmas
                    self.email_password = alarmas.email_config['password']
                except Exception as e:
                    if self.app:
                        self.app.logger.error(f"Error al obtener contraseña de alarmas: {str(e)}")
                    # Usar la contraseña conocida como último recurso
                    self.email_password = "mqsl wlvi usjb kfzl"
            
            # Imprimir información de depuración (sin mostrar la contraseña completa)
            print(f"Intentando enviar correo de recuperación a: {email}")
            print(f"Usando cuenta de correo: {self.email_sender}")
            print(f"Contraseña configurada: {'Sí' if self.email_password else 'No'}")
            
            # Enviar el correo
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as servidor:
                servidor.starttls()
                servidor.login(self.email_sender, self.email_password)
                servidor.send_message(mensaje)
            
            print(f"Correo de recuperación enviado exitosamente a {email}")
            return True
        except Exception as e:
            print(f"Error al enviar correo de recuperación: {str(e)}")
            if self.app:
                self.app.logger.error(f"Error al enviar correo de recuperación: {str(e)}")
            return False
