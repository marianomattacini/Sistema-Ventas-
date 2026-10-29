@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHON_CMD="
where py >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (echo [ERROR] No se encontro Python 3.& pause & exit /b 1)
%PYTHON_CMD% -m pip install psycopg2-binary python-dotenv
if errorlevel 1 (pause & exit /b 1)
if not exist "%~dp0.env" copy /Y "%~dp0.env.example" "%~dp0.env" >nul
findstr /C:"PG_PASSWORD=CAMBIAR_ESTA_CLAVE" "%~dp0.env" >nul 2>&1
if not errorlevel 1 (
 echo [ATENCION] Configura PG_PASSWORD en .env. Se abrira ahora.
 notepad "%~dp0.env"
)
%PYTHON_CMD% "%~dp0database\setup_postgresql.py"
echo.
if errorlevel 1 (echo [ERROR] PostgreSQL no pudo configurarse.) else (echo [OK] PostgreSQL creado/verificado.)
pause
