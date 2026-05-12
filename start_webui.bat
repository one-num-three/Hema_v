@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "NODE_DIR=%SCRIPT_DIR%node_embedded"
set "NODE_EXE=%NODE_DIR%\node.exe"
set "WEBUI_DIR=%SCRIPT_DIR%webui"
set "WEBUI_SERVER=%WEBUI_DIR%\dist\server\index.js"
set "WEBUI_PORT=8648"
set "GATEWAY_PORT=8642"
set "WEBUI_PID_FILE=%USERPROFILE%\.hermes-web-ui\server.pid"
set "WEBUI_TOKEN_FILE=%USERPROFILE%\.hermes-web-ui\.token"
set "WEBUI_LOG=%USERPROFILE%\.hermes-web-ui\server.log"

:: Pre-flight checks
if not exist "%NODE_EXE%" (
    echo [ERROR] Node.js not found at "%NODE_EXE%"
    echo         Web UI requires the Full version.
    echo         Run: install.bat full
    pause
    exit /b 1
)
if not exist "%WEBUI_SERVER%" (
    echo [ERROR] Web UI server not found at "%WEBUI_SERVER%"
    echo         Run: install.bat full
    pause
    exit /b 1
)

:: Check if Web UI is already running
if exist "%WEBUI_PID_FILE%" (
    set /p EXISTING_PID=<"%WEBUI_PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | find "node" >nul
    if !errorlevel! equ 0 (
        echo [OK] Web UI already running (PID: !EXISTING_PID!, port: %WEBUI_PORT%)
        goto :open_browser
    )
    del "%WEBUI_PID_FILE%" 2>nul
)

:: Make sure Hermes gateway is running
echo [INFO] Checking Hermes gateway (port %GATEWAY_PORT%)...
powershell -NoProfile -Command ^
    "try{Invoke-WebRequest 'http://127.0.0.1:%GATEWAY_PORT%/health' -TimeoutSec 2 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Gateway not running, starting it now...
    call "%SCRIPT_DIR%start_hermes_gateway.bat"
    if errorlevel 1 (
        echo [ERROR] Failed to start Hermes gateway.
        echo         Web UI requires gateway on port %GATEWAY_PORT%.
        pause
        exit /b 1
    )
)

:: Read or generate auth token
if not exist "%USERPROFILE%\.hermes-web-ui" mkdir "%USERPROFILE%\.hermes-web-ui"
if not exist "%WEBUI_TOKEN_FILE%" (
    powershell -NoProfile -Command ^
        "$t=[System.BitConverter]::ToString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))-replace'-','';" ^
        "Set-Content -Path '%WEBUI_TOKEN_FILE%' -Value $t.ToLower() -Encoding ASCII" >nul 2>&1
)
set /p WEBUI_TOKEN=<"%WEBUI_TOKEN_FILE%"

:: Force-free the port: kill ANY process holding port 8648 (not just node)
netstat -aon 2>nul | findstr ":%WEBUI_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARN] Port %WEBUI_PORT% in use, freeing it...
    for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%WEBUI_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
        echo [INFO] Killed PID %%p that held port %WEBUI_PORT%
    )
    timeout /t 2 /nobreak >nul
)

:: Verify port is now free
netstat -aon 2>nul | findstr ":%WEBUI_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERROR] Port %WEBUI_PORT% still in use after cleanup. Aborting.
    echo         Run manually: netstat -ano ^| findstr :%WEBUI_PORT%
    pause
    exit /b 1
)

:: Env vars consumed by hermes-web-ui server
set "PATH=%NODE_DIR%;%PATH%"
set "PORT=%WEBUI_PORT%"
set "NODE_ENV=production"
set "UPSTREAM=http://127.0.0.1:%GATEWAY_PORT%"
set "HERMES_HOME=%USERPROFILE%\.hermes"

:: HERMES_BIN: prefer pip-installed hermes.exe.
:: Node 23 blocks spawning .bat files via execFile due to CVE-2024-27980.
if exist "%SCRIPT_DIR%python_embedded\Scripts\hermes.exe" (
    set "HERMES_BIN=%SCRIPT_DIR%python_embedded\Scripts\hermes.exe"
) else (
    set "HERMES_BIN=%SCRIPT_DIR%hermes.bat"
)

set "AUTH_TOKEN=%WEBUI_TOKEN%"
set "NPM_CONFIG_CACHE=%SCRIPT_DIR%.npm-cache"
set "npm_config_ignore_scripts=true"

:: hermes-web-ui terminal feature uses findShell() which calls existsSync()
:: on bare names like 'cmd.exe' / 'powershell.exe' -- those return false on
:: Windows because no PATH lookup happens. Workaround: provide an absolute
:: SHELL path so the first candidate (process.env.SHELL) is honored.
if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" (
    set "SHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
) else (
    set "SHELL=%SystemRoot%\System32\cmd.exe"
)

:: Start Web UI in background
echo [INFO] Starting hermes-web-ui on port %WEBUI_PORT%...
cd /d "%WEBUI_DIR%"
start /b "" "%NODE_EXE%" "%WEBUI_SERVER%" >> "%WEBUI_LOG%" 2>&1

:: Capture PID after 1s
timeout /t 1 /nobreak >nul
for /f "tokens=2" %%p in ('wmic process where "name='node.exe'" get ProcessId /format:value 2^>nul ^| find "=" ^| sort /r') do (
    if not defined WEBUI_PID set "WEBUI_PID=%%p"
)
if defined WEBUI_PID (
    echo !WEBUI_PID!>"%WEBUI_PID_FILE%"
    echo [INFO] Web UI PID: !WEBUI_PID!
)

:: Poll /health up to 30 seconds
set "MAX_WAIT=30"
set "WAITED=0"
:wait_webui
timeout /t 1 /nobreak >nul
set /a WAITED+=1
<nul set /p =""
powershell -NoProfile -Command ^
    "try{Invoke-WebRequest 'http://127.0.0.1:%WEBUI_PORT%/health' -TimeoutSec 2 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] hermes-web-ui ready.
    goto :open_browser
)
if %WAITED% LSS %MAX_WAIT% goto :wait_webui
echo [WARN] Web UI did not respond in %MAX_WAIT%s.
echo        Check log: %WEBUI_LOG%

:open_browser
:: Open browser with token in URL fragment (Vue Router hash mode)
set "BROWSER_URL=http://localhost:%WEBUI_PORT%/#/?token=%WEBUI_TOKEN%"
echo [INFO] Opening browser: %BROWSER_URL%
start "" "%BROWSER_URL%"
echo [OK] Web UI is running at http://localhost:%WEBUI_PORT%
echo.
endlocal
