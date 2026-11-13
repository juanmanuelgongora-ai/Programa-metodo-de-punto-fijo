@echo off
title Metodo de Punto Fijo - Analisis Numerico
chcp 65001 > nul

echo ==============================================================
echo    INICIANDO APLICACION: METODO DE PUNTO FIJO
echo    Solucion de Ecuaciones No Lineales
echo ==============================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se encontro Python en el PATH del sistema.
    echo Por favor asegurese de tener instalado Python 3.
    pause
    exit /b 1
)

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Ocurrio un error al ejecutar la aplicacion.
    pause
)
