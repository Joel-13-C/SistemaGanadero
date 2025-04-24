# Guía para Pruebas de Restauración de Respaldos

Esta guía explica cómo realizar pruebas de restauración para verificar que los respaldos de la base de datos del Sistema Ganadero funcionan correctamente.

## Importancia de las pruebas de restauración

Realizar pruebas de restauración periódicas es fundamental por las siguientes razones:

1. **Verificar la integridad de los respaldos**: Confirmar que los archivos no están corruptos
2. **Validar el proceso completo**: Asegurar que todo el flujo de respaldo y restauración funciona
3. **Preparación para emergencias**: Familiarizarse con el proceso antes de una emergencia real
4. **Cumplimiento de políticas**: Muchas normativas exigen pruebas periódicas de los sistemas de respaldo

## Requisitos previos

- MySQL Server instalado
- Python 3.6 o superior
- Acceso a los archivos de respaldo
- Permisos para crear bases de datos (para pruebas)

## Procedimiento de prueba

### 1. Crear una base de datos de prueba

Primero, debemos crear una base de datos separada para realizar las pruebas sin afectar el sistema en producción:

```bash
python restaurar_respaldo.py --bd sistema_ganadero_test --crear-bd respaldos/respaldo_sistema_ganadero_XXXXXXXX_XXXXXX.sql.zip
```

Este comando:
- Crea una base de datos llamada `sistema_ganadero_test`
- Restaura el respaldo más reciente en esta base de datos

### 2. Verificar la restauración

Para verificar que la restauración fue exitosa, podemos:

1. **Verificar las tablas**: Comprobar que todas las tablas se han creado correctamente
2. **Verificar los datos**: Asegurarse de que los datos son correctos y completos
3. **Probar la funcionalidad**: Configurar temporalmente la aplicación para usar la base de datos de prueba y verificar su funcionamiento

### 3. Documentar los resultados

Es importante documentar los resultados de cada prueba de restauración:

- Fecha y hora de la prueba
- Versión del respaldo utilizado
- Problemas encontrados
- Tiempo necesario para completar la restauración
- Resultado final (éxito/fracaso)

## Ejemplo de prueba completa

A continuación se muestra un ejemplo de flujo completo de prueba:

```bash
# 1. Listar los respaldos disponibles
dir respaldos

# 2. Seleccionar el respaldo más reciente
# (Supongamos que es respaldo_sistema_ganadero_20250417_130645.sql.zip)

# 3. Restaurar en una base de datos de prueba
python restaurar_respaldo.py --bd sistema_ganadero_test --crear-bd respaldos/respaldo_sistema_ganadero_20250417_130645.sql.zip

# 4. Verificar algunas tablas importantes
mysql -u root -p1234 -e "USE sistema_ganadero_test; SHOW TABLES;"
mysql -u root -p1234 -e "USE sistema_ganadero_test; SELECT COUNT(*) FROM animales;"
mysql -u root -p1234 -e "USE sistema_ganadero_test; SELECT COUNT(*) FROM usuarios;"

# 5. Limpiar después de la prueba (opcional)
mysql -u root -p1234 -e "DROP DATABASE sistema_ganadero_test;"
```

## Frecuencia recomendada

Se recomienda realizar pruebas de restauración:

- Después de implementar cambios importantes en la estructura de la base de datos
- Al menos una vez al mes
- Antes de actualizar el sistema a una nueva versión
- Cuando se cambie el hardware o software relacionado con la base de datos

## Solución de problemas comunes

### Error de permisos

Si aparece un error de permisos:
```
Error de acceso: usuario o contraseña incorrectos
```

Verifica las credenciales utilizadas y asegúrate de que el usuario tenga permisos para crear bases de datos.

### Error de sintaxis SQL

Si aparecen errores de sintaxis SQL durante la restauración:
```
Error al ejecutar comando SQL: ...
```

Esto puede indicar que el respaldo está corrupto o que hay incompatibilidad entre versiones de MySQL. Intenta con un respaldo diferente.

### Espacio insuficiente

Si aparece un error de espacio insuficiente:
```
No space left on device
```

Libera espacio en el disco o utiliza un servidor con más capacidad para las pruebas.

## Conclusión

Las pruebas regulares de restauración son una parte esencial del mantenimiento del sistema. No esperes a tener una emergencia para descubrir que tus respaldos no funcionan correctamente.
