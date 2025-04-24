# Guía Rápida de Respaldo de Base de Datos - Sistema Ganadero

## Introducción

Esta guía rápida explica cómo utilizar el sistema de respaldo de la base de datos del Sistema Ganadero. Está diseñada para que cualquier usuario, incluso sin conocimientos técnicos avanzados, pueda realizar y restaurar respaldos de forma segura.

## Respaldo Manual

### Paso 1: Ejecutar el respaldo

Simplemente haga doble clic en el archivo `ejecutar_respaldo.bat` ubicado en la carpeta principal del sistema.

![Ejecutar Respaldo](../static/img/docs/ejecutar_respaldo.png)

Se abrirá una ventana de comandos que mostrará el progreso del respaldo.

### Paso 2: Verificar el resultado

Al finalizar, verá un mensaje confirmando que el respaldo se ha completado exitosamente.

Los archivos de respaldo se guardan en la carpeta `respaldos` con un nombre que incluye la fecha y hora:
```
respaldo_sistema_ganadero_20250417_130645.sql.zip
```

## Respaldo Automático

Para no tener que preocuparse por realizar respaldos manualmente, configure una tarea programada:

1. Siga las instrucciones en el archivo `CONFIGURAR_TAREA_PROGRAMADA.md`
2. Recomendamos programar el respaldo diariamente a las 2:00 AM
3. Una vez configurado, el sistema realizará respaldos automáticamente

## Restauración de Respaldos

En caso de necesitar recuperar datos de un respaldo:

### Paso 1: Localizar el archivo de respaldo

Busque en la carpeta `respaldos` el archivo que desea restaurar.

### Paso 2: Ejecutar la restauración

Abra una ventana de comandos (cmd) y ejecute:

```
python restaurar_respaldo.py respaldos/NOMBRE_DEL_ARCHIVO.sql.zip
```

Reemplace `NOMBRE_DEL_ARCHIVO.sql.zip` con el nombre real del archivo de respaldo.

### Paso 3: Verificar la restauración

Una vez completado el proceso, verifique que los datos se han restaurado correctamente accediendo al sistema.

## Preguntas Frecuentes

### ¿Cuántos respaldos se mantienen automáticamente?

El sistema mantiene los 10 respaldos más recientes para optimizar el espacio en disco.

### ¿Qué hago si el respaldo falla?

Revise el archivo `logs/respaldo_bd.log` para identificar el problema. Los errores más comunes son:
- Problemas de conexión a la base de datos
- Falta de espacio en disco
- Permisos insuficientes

### ¿Es seguro restaurar un respaldo en la base de datos principal?

La restauración sobrescribirá todos los datos existentes. Recomendamos:
1. Realizar primero una prueba en una base de datos separada
2. Hacer un respaldo adicional antes de restaurar
3. Notificar a los usuarios que el sistema estará temporalmente fuera de servicio

## Contacto de Soporte

Si necesita ayuda con el sistema de respaldo, contacte a soporte:
- Correo: soporte@sistemaganadero.com
- Teléfono: (123) 456-7890
