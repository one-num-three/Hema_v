@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"

:: Load .env first so user vars are available, then set local vars after
:: (so local vars are not accidentally overridden by .env content)
if not exist "%SCRIPT_DIR%.env" goto :env_loaded
for /f "usebackq tokens=1,* delims==" %%a in ("%SCRIPT_DIR%.env") do call :load_env_line "%%a" "%%b"
:env_loaded

:: Local script vars
set "PYTHON_EXE=%SCRIPT_DIR%python_embedded\python.exe"
set "GATEWAY_PORT=8642"
set "GATEWAY_HOST=127.0.0.1"
set "GATEWAY_PID_FILE=%USERPROFILE%\.hermes\gateway.pid"
set "GATEWAY_LOG=%USERPROFILE%\.hermes\gateway.log"

:: Verify Python exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found at %PYTHON_EXE%
    echo         Please run install.bat first.
    exit /b 1
)

:: If gateway already running, exit 0
if exist "%GATEWAY_PID_FILE%" (
    set /p EXISTING_PID=<"%GATEWAY_PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | find "python" >nul
    if !errorlevel! equ 0 (
        echo [OK] Hermes gateway already running (PID: !EXISTING_PID!, port: %GATEWAY_PORT%)
        exit /b 0
    )
    del "%GATEWAY_PID_FILE%" 2>nul
)

:: Env vars for the gateway process
set "PATH=%SCRIPT_DIR%python_embedded;%SCRIPT_DIR%python_embedded\Scripts;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"
set "API_SERVER_PORT=%GATEWAY_PORT%"
set "API_SERVER_HOST=%GATEWAY_HOST%"
set "HERMES_PYTHON=%PYTHON_EXE%"
set "HERMES_ROOT=%SCRIPT_DIR%"

:: Ensure ~/.hermes exists
if not exist "%USERPROFILE%\.hermes" mkdir "%USERPROFILE%\.hermes"

:: Start gateway in background
echo [INFO] Starting Hermes gateway on %GATEWAY_HOST%:%GATEWAY_PORT%...
cd /d "%SCRIPT_DIR%"

start /b "" "%PYTHON_EXE%" -m hermes_cli.main gateway >> "%GATEWAY_LOG%" 2>&1

:: Capture PID after a 1s delay (process needs time to start)
timeout /t 1 /nobreak >nul

:: Find newest python.exe whose command line includes "gateway"
for /f "tokens=2" %%p in ('wmic process where "name='python.exe' and commandline like '%%gateway%%'" get ProcessId /format:value 2^>nul ^| find "="') do (
    if not defined GATEWAY_PID set "GATEWAY_PID=%%p"
)
if defined GATEWAY_PID (
    echo !GATEWAY_PID!>"%GATEWAY_PID_FILE%"
    echo [INFO] Gateway PID: !GATEWAY_PID!
)

:: Poll /health up to 15 seconds
set "MAX_WAIT=15"
set "WAITED=0"
:wait_gateway
timeout /t 1 /nobreak >nul
set /a WAITED+=1
powershell -NoProfile -Command ^
    "try{Invoke-WebRequest 'http://%GATEWAY_HOST%:%GATEWAY_PORT%/health' -TimeoutSec 2 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Hermes gateway ready on port %GATEWAY_PORT%.
    exit /b 0
)
if %WAITED% LSS %MAX_WAIT% goto :wait_gateway

echo [WARN] Gateway did not respond in %MAX_WAIT%s.
echo        Check log: %GATEWAY_LOG%
exit /b 0

:: Subroutine: load one .env line (skip blanks and # comments)
:load_env_line
set "_K=%~1"
if "%_K%"=="" goto :eof
if "%_K:~0,1%"=="#" goto :eof
set "%~1=%~2"
goto :eof
