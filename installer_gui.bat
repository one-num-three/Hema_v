@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Sta -File "%SCRIPT_DIR%installer_gui.ps1"
endlocal
