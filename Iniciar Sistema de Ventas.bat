@echo off
setlocal
cd /d "%~dp0"

REM --- Python 3.12 confirmado como el que funciona en esta PC ---
set "PY=C:\Program Files\Python312\pythonw.exe"
if not exist "%PY%" set "PY=C:\Program Files\Python312\python.exe"

if not exist "%PY%" (
    echo No se encontro Python en: C:\Program Files\Python312\
    echo Edita este archivo con el boton derecho -^> Modificar,
    echo y corregi la ruta de la variable PY con la correcta.
    pause
    exit /b 1
)

start "" "%PY%" main.py
exit
