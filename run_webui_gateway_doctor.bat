@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%python_embedded\python.exe" (
    set "PYTHON_EXE=%SCRIPT_DIR%python_embedded\python.exe"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python not found.
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" "%SCRIPT_DIR%scripts\webui_gateway_doctor.py"
if errorlevel 1 exit /b %errorlevel%

echo.
echo [OK] Diagnostic log generated. Send me the printed file path.
exit /b 0
