@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ==================================================
echo   SISTEMA DE VENTAS - CONFIGURACION DE BASES
echo ==================================================

set "PYTHON_CMD="
where py >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
  where python >nul 2>&1 && set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
  echo [ERROR] No se encontro Python 3.
  echo Instala Python 3 y marca "Add Python to PATH".
  pause
  exit /b 1
)

echo [INFO] Python detectado:
%PYTHON_CMD% --version
if errorlevel 1 goto :error

echo.
echo [1/4] Actualizando pip...
%PYTHON_CMD% -m pip install --upgrade pip
if errorlevel 1 goto :error

echo.
echo [2/4] Instalando dependencias...
%PYTHON_CMD% -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :error

echo.
echo [3/4] Creando/verificando SQLite...
%PYTHON_CMD% "%~dp0database\setup_db.py"
if errorlevel 1 goto :error

echo.
echo [4/4] Creando/verificando PostgreSQL...
if not exist "%~dp0.env" copy /Y "%~dp0.env.example" "%~dp0.env" >nul
findstr /C:"PG_PASSWORD=CAMBIAR_ESTA_CLAVE" "%~dp0.env" >nul 2>&1
if not errorlevel 1 (
  echo.
  echo [ATENCION] Falta colocar la clave real de PostgreSQL en .env
  echo Se abrira el archivo. Cambia PG_PASSWORD, guarda y cierra el Bloc de notas.
  notepad "%~dp0.env"
)
%PYTHON_CMD% "%~dp0database\setup_postgresql.py"
if errorlevel 1 goto :pgerror

echo.
echo ==================================================
echo [OK] SQLite y PostgreSQL quedaron configurados.
echo ==================================================
pause
exit /b 0

:pgerror
echo.
echo [ERROR] SQLite se creo, pero PostgreSQL fallo.
echo Revisa que el servicio PostgreSQL este iniciado y los datos de .env.
echo Si tu PostgreSQL usa otro puerto, cambia PG_PORT en .env.
pause
exit /b 1

:error
echo.
echo [ERROR] El proceso se detuvo por el error mostrado arriba.
pause
exit /b 1
