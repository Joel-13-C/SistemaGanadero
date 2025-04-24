# Configuración de Tarea Programada para Respaldos Automáticos

Este documento explica cómo configurar una tarea programada en Windows para ejecutar automáticamente el respaldo de la base de datos del Sistema Ganadero.

## Pasos para configurar la tarea programada

1. **Abrir el Programador de tareas**:
   - Presiona `Win + R` para abrir el cuadro de diálogo Ejecutar
   - Escribe `taskschd.msc` y presiona Enter

2. **Crear una tarea nueva**:
   - En el panel derecho, haz clic en "Crear tarea básica"
   - Asigna un nombre como "Respaldo Sistema Ganadero" y una descripción opcional
   - Haz clic en "Siguiente"

3. **Configurar la frecuencia**:
   - Selecciona "Diariamente" y haz clic en "Siguiente"
   - Establece la hora de inicio (recomendado: 2:00 AM) y haz clic en "Siguiente"

4. **Configurar la acción**:
   - Selecciona "Iniciar un programa" y haz clic en "Siguiente"
   - En "Programa o script", navega hasta la ubicación del archivo batch:
     ```
     C:\Users\JOEL\CascadeProjects\SistemaGanadero\ejecutar_respaldo.bat
     ```
   - En "Iniciar en", especifica la carpeta del proyecto:
     ```
     C:\Users\JOEL\CascadeProjects\SistemaGanadero
     ```
   - Haz clic en "Siguiente"

5. **Finalizar la configuración**:
   - Revisa el resumen y marca la casilla "Abrir el diálogo de propiedades para esta tarea cuando haga clic en Finalizar"
   - Haz clic en "Finalizar"

6. **Configuraciones adicionales**:
   - En la pestaña "General", marca "Ejecutar con privilegios más altos"
   - En la pestaña "Condiciones", desmarca "Iniciar la tarea solo si el equipo está conectado a la CA"
   - En la pestaña "Configuración", marca "Ejecutar la tarea lo antes posible después de no haberse iniciado en una programación"
   - Haz clic en "Aceptar" para guardar la tarea

## Verificación

Para verificar que la tarea está correctamente configurada:

1. Localiza la tarea en la lista de tareas programadas
2. Haz clic derecho sobre ella y selecciona "Ejecutar"
3. Verifica que se crea un nuevo archivo de respaldo en la carpeta `respaldos`

## Solución de problemas

Si la tarea no se ejecuta correctamente:

1. Verifica que la ruta al archivo batch sea correcta
2. Asegúrate de que el usuario tenga permisos para ejecutar scripts
3. Revisa el registro de eventos de Windows para ver posibles errores
4. Confirma que MySQL esté en ejecución cuando se intenta realizar el respaldo
