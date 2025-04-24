# Instrucciones para Configurar Almacenamiento Externo de Respaldos

Este documento explica cómo configurar y utilizar el script `copiar_respaldos_externos.py` para mantener copias de seguridad en ubicaciones externas.

## Requisitos

- Acceso a una unidad externa (USB, disco duro externo) o carpeta de red
- Python 3.6 o superior instalado
- Permisos de escritura en la ubicación de destino

## Opciones de almacenamiento recomendadas

1. **Disco duro externo**: 
   - Opción más segura para respaldos locales
   - Debe conectarse regularmente al servidor

2. **Unidad USB**: 
   - Solución económica pero menos robusta
   - Ideal para empresas pequeñas

3. **Carpeta de red**: 
   - Permite almacenar respaldos en otro servidor
   - Requiere configuración de red adecuada

4. **Servicio en la nube**: 
   - Opción más segura contra desastres físicos
   - Requiere conexión a internet

## Uso del script

### Ejemplo básico

Para copiar los respaldos a una unidad USB (por ejemplo, E:):

```bash
python copiar_respaldos_externos.py --destino E:\Respaldos_SistemaGanadero
```

### Ejemplo con carpeta de red

Para copiar a una carpeta compartida en la red:

```bash
python copiar_respaldos_externos.py --destino \\servidor\respaldos\SistemaGanadero
```

### Opciones avanzadas

Especificar una carpeta de origen diferente y limitar el número de copias:

```bash
python copiar_respaldos_externos.py --origen C:\OtraCarpeta\respaldos --destino E:\Respaldos --max-copias 5
```

## Automatización

Para automatizar este proceso, puedes modificar el archivo `ejecutar_respaldo.bat` para que también ejecute este script después de realizar el respaldo:

```batch
@echo off
echo Iniciando respaldo de base de datos...
python respaldo_bd.py
echo Copiando respaldos a almacenamiento externo...
python copiar_respaldos_externos.py --destino E:\Respaldos_SistemaGanadero
echo Proceso completo.
pause
```

## Verificación de respaldos

Es importante verificar regularmente que:

1. Los respaldos se están copiando correctamente
2. Los archivos no están corruptos
3. El espacio en la unidad de destino es suficiente

Revisa el archivo de registro `logs/copias_externas.log` para verificar el estado de las copias.

## Solución de problemas

### El script no puede acceder a la unidad de destino

- Verifica que la unidad esté conectada y accesible
- Comprueba los permisos de escritura
- Asegúrate de que la ruta sea correcta

### Error de espacio insuficiente

- Libera espacio en la unidad de destino
- Reduce el número de copias con la opción `--max-copias`

### Problemas con carpetas de red

- Verifica las credenciales de red
- Comprueba que la carpeta compartida esté disponible
- Asegúrate de que el firewall no esté bloqueando la conexión
