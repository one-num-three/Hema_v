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

:: ── 前置检查 ────────────────────────────────────────────────────────
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

:: ── 检查 Web UI 是否已在运行 ────────────────────────────────────────
if exist "%WEBUI_PID_FILE%" (
    set /p EXISTING_PID=<"%WEBUI_PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | find "node" >nul
    if !errorlevel! equ 0 (
        echo [OK] Web UI already running (PID: !EXISTING_PID!, port: %WEBUI_PORT%)
        goto :open_browser
    )
    del "%WEBUI_PID_FILE%" 2>nul
)

:: ── 确保 Gateway 在运行 ─────────────────────────────────────────────
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

:: ── 读取或生成 Auth Token ───────────────────────────────────────────
if not exist "%USERPROFILE%\.hermes-web-ui" mkdir "%USERPROFILE%\.hermes-web-ui"
if not exist "%WEBUI_TOKEN_FILE%" (
    powershell -NoProfile -Command ^
        "$t=[System.BitConverter]::ToString([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))-replace'-','';" ^
        "Set-Content -Path '%WEBUI_TOKEN_FILE%' -Value $t.ToLower() -Encoding ASCII" >nul 2>&1
)
set /p WEBUI_TOKEN=<"%WEBUI_TOKEN_FILE%"

:: ── 检测并处理端口冲突（强力版：杀掉占用 %WEBUI_PORT% 的所有进程，不只是 node） ─
netstat -aon 2>nul | findstr ":%WEBUI_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARN] Port %WEBUI_PORT% in use, freeing it...
    for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%WEBUI_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
        echo [INFO] Killed PID %%p that held port %WEBUI_PORT%
    )
    timeout /t 2 /nobreak >nul
)

:: 二次确认端口已释放
netstat -aon 2>nul | findstr ":%WEBUI_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERROR] Port %WEBUI_PORT% still in use after cleanup. Aborting.
    echo         Run manually: netstat -ano ^| findstr :%WEBUI_PORT%
    pause
    exit /b 1
)

:: ── 环境变量配置（hermes-web-ui server 读取这些）───────────────────
set "PATH=%NODE_DIR%;%PATH%"
set "PORT=%WEBUI_PORT%"
set "NODE_ENV=production"
set "UPSTREAM=http://127.0.0.1:%GATEWAY_PORT%"
set "HERMES_HOME=%USERPROFILE%\.hermes"
set "HERMES_BIN=%SCRIPT_DIR%hermes.bat"
set "AUTH_TOKEN=%WEBUI_TOKEN%"
set "NPM_CONFIG_CACHE=%SCRIPT_DIR%.npm-cache"
set "npm_config_ignore_scripts=true"

:: ── 后台启动 Web UI 服务器 ──────────────────────────────────────────
echo [INFO] Starting hermes-web-ui on port %WEBUI_PORT%...
cd /d "%WEBUI_DIR%"
start /b "" "%NODE_EXE%" "%WEBUI_SERVER%" >> "%WEBUI_LOG%" 2>&1

:: 等 1 秒再抓 PID
timeout /t 1 /nobreak >nul
for /f "tokens=2" %%p in ('wmic process where "name='node.exe'" get ProcessId /format:value 2^>nul ^| find "=" ^| sort /r') do (
    if not defined WEBUI_PID set "WEBUI_PID=%%p"
)
if defined WEBUI_PID (
    echo !WEBUI_PID!>"%WEBUI_PID_FILE%"
    echo [INFO] Web UI PID: !WEBUI_PID!
)

:: ── 轮询等待 Web UI 就绪（最多 30 秒）──────────────────────────────
set "MAX_WAIT=30"
set "WAITED=0"
:wait_webui
timeout /t 1 /nobreak >nul
set /a WAITED+=1
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
:: ── 打开浏览器（附带 token）────────────────────────────────────────
set "BROWSER_URL=http://localhost:%WEBUI_PORT%/#/?token=%WEBUI_TOKEN%"
echo [INFO] Opening browser: %BROWSER_URL%
start "" "%BROWSER_URL%"
echo [OK] Web UI is running at http://localhost:%WEBUI_PORT%
echo.
endlocal
