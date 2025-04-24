@echo off
echo ===== INICIANDO RESPALDO AUTOMATICO DE BASE DE DATOS =====
echo Fecha y hora: %date% %time%
echo.

REM Cambiar al directorio del proyecto
cd /d %~dp0

REM Ejecutar el script de respaldo
python respaldo_bd.py

echo.
echo ===== RESPALDO FINALIZADO =====
echo Presione cualquier tecla para salir...
pause > nul
