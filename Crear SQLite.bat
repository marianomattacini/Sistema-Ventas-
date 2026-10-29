@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHON_CMD="
where py >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD where python >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD (echo [ERROR] No se encontro Python 3.& pause & exit /b 1)
%PYTHON_CMD% -m pip install python-dotenv bcrypt
if errorlevel 1 (pause & exit /b 1)
%PYTHON_CMD% "%~dp0database\setup_db.py"
echo.
if errorlevel 1 (echo [ERROR] SQLite no pudo crearse.) else (echo [OK] SQLite creado/verificado.)
pause
