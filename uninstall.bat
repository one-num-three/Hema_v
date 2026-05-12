@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS1=%SCRIPT_DIR%uninstall.ps1"
set "QUIET="

for %%a in (%*) do (
    if /i "%%~a"=="/quiet" set "QUIET=1"
    if /i "%%~a"=="-quiet" set "QUIET=1"
)

if not exist "%PS1%" (
    echo [ERROR] uninstall.ps1 not found: "%PS1%"
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Uninstall failed with exit code %EXIT_CODE%.
    if not defined QUIET pause
)

endlocal
exit /b %EXIT_CODE%
