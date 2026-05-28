@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "ORIGINAL_SCRIPT_DIR=%SCRIPT_DIR%"
call :resolve_install_root "%SCRIPT_DIR%"
if /i not "%SCRIPT_DIR%"=="%ORIGINAL_SCRIPT_DIR%" (
    echo [INFO] Resolved install root from "%ORIGINAL_SCRIPT_DIR%" to "%SCRIPT_DIR%"
)
set "SCRIPT_DIR=%SCRIPT_DIR%\"
set "NODE_DIR=%SCRIPT_DIR%node_embedded"
set "NODE_EXE=%NODE_DIR%\node.exe"
set "NPM_CMD=%NODE_DIR%\npm.cmd"
set "WEBUI_DIR=%SCRIPT_DIR%webui"
set "WEBUI_SERVER=%WEBUI_DIR%\dist\server\index.js"
set "WEBUI_NPM_SERVER=%WEBUI_DIR%\node_modules\hermes-web-ui\dist\server\index.js"
set "WEBUI_SOCKETIO=%WEBUI_DIR%\node_modules\socket.io\package.json"
set "WEBUI_PORT=8648"
set "GATEWAY_PORT=8642"
set "HERMES_HOME=%USERPROFILE%\.hermes"
set "WEBUI_PID_FILE=%USERPROFILE%\.hermes-web-ui\server.pid"
set "WEBUI_MODE_FILE=%USERPROFILE%\.hermes-web-ui\server.mode"
set "WEBUI_LOG=%USERPROFILE%\.hermes-web-ui\server.log"
set "WEBUI_LAUNCHER_PORT="
set "WEBUI_LAUNCHER_DIR=%WEBUI_DIR%\launcher"
set "PATCH_PY="
set "GATEWAY_PORT_SOURCE=default"

if exist "%SCRIPT_DIR%python_embedded\python.exe" (
    set "PATCH_PY=%SCRIPT_DIR%python_embedded\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 set "PATCH_PY=python"
)

call :resolve_hermes_home
call :resolve_gateway_port

:: Pre-flight checks
if not exist "%NODE_EXE%" (
    echo [ERROR] Node.js not found at "%NODE_EXE%"
    echo         Web UI requires the Full version.
    echo         Run: install.bat full
    echo         Expected install root: "%SCRIPT_DIR%"
    pause
    exit /b 1
)
if not exist "%WEBUI_SERVER%" if not exist "%WEBUI_NPM_SERVER%" (
    echo [ERROR] Web UI server not found.
    echo         Checked bundle mode: "%WEBUI_SERVER%"
    echo         Checked npm mode:    "%WEBUI_NPM_SERVER%"
    echo         Run: install.bat full
    echo         If this is a newly downloaded installer, the CDN package may be old or incomplete.
    pause
    exit /b 1
)
if exist "%WEBUI_NPM_SERVER%" set "WEBUI_SERVER=%WEBUI_NPM_SERVER%"

:: Apply local Web UI compatibility patches even when an existing server is reused.
if defined PATCH_PY if exist "%SCRIPT_DIR%scripts\patch-webui-persistence.py" (
    "%PATCH_PY%" "%SCRIPT_DIR%scripts\patch-webui-persistence.py" "%WEBUI_DIR%" >nul 2>&1
)

rem Start the gateway FIRST so it has maximum time to initialize while the
rem browser launcher page is loading. The gateway is the main bottleneck
rem on cold first-run (Python import + platform adapter setup).
echo [INFO] Checking Hermes gateway (port %GATEWAY_PORT%)...
echo [INFO] HERMES_HOME: %HERMES_HOME%
echo [INFO] Gateway port source: %GATEWAY_PORT_SOURCE%
powershell -NoProfile -Command ^
    "try{Invoke-WebRequest 'http://127.0.0.1:%GATEWAY_PORT%/health' -TimeoutSec 1 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Hermes gateway already running on port %GATEWAY_PORT%.
) else (
    echo [INFO] Starting Hermes gateway in background...
    if not exist "%SCRIPT_DIR%start_hermes_gateway.bat" (
        echo [ERROR] Gateway launcher not found: "%SCRIPT_DIR%start_hermes_gateway.bat"
        pause
        exit /b 1
    )
    powershell -NoProfile -Command ^
        "$cmd='call ""' + [IO.Path]::GetFullPath('%SCRIPT_DIR%start_hermes_gateway.bat') + '""';" ^
        "$work=[IO.Path]::GetFullPath('%SCRIPT_DIR%');" ^
        "Start-Process -FilePath $env:ComSpec -ArgumentList '/d','/s','/c',$cmd -WorkingDirectory $work -WindowStyle Hidden | Out-Null" >nul 2>&1
)

:: Local desktop launcher: Web UI binds to localhost, so auth is disabled by default.
:: If you expose the Web UI to LAN/Internet later, re-enable auth and use HTTPS.
set "AUTH_DISABLED=1"

:: Check if Web UI is already running
if exist "%WEBUI_PID_FILE%" (
    set /p EXISTING_PID=<"%WEBUI_PID_FILE%"
    tasklist /FI "PID eq !EXISTING_PID!" 2>nul | find "node" >nul
    if !errorlevel! equ 0 (
        call :is_current_webui
        if !errorlevel! equ 0 (
            powershell -NoProfile -Command ^
                "try{Invoke-WebRequest 'http://127.0.0.1:%WEBUI_PORT%/health' -TimeoutSec 2 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
            if !errorlevel! equ 0 (
                call :is_expected_webui_mode
                if !errorlevel! equ 0 (
                    call :is_webui_gateway_connected
                    if !errorlevel! equ 0 (
                        echo [OK] Web UI already running ^(PID: !EXISTING_PID!, port: %WEBUI_PORT%^)
                        goto :open_browser
                    ) else (
                        echo [INFO] Existing Web UI is running and will keep waiting for the gateway inside the startup page.
                        goto :open_browser
                    )
                ) else (
                    echo [WARN] Existing Web UI was started with old settings, restarting it...
                    del "%WEBUI_PID_FILE%" 2>nul
                    del "%WEBUI_MODE_FILE%" 2>nul
                    taskkill /F /PID !EXISTING_PID! >nul 2>&1
                    ping 127.0.0.1 -n 2 >nul 2>&1
                )
            )
        ) else (
            echo [WARN] Existing Web UI PID belongs to another install, restarting it...
            del "%WEBUI_PID_FILE%" 2>nul
            taskkill /F /PID !EXISTING_PID! >nul 2>&1
            ping 127.0.0.1 -n 2 >nul 2>&1
        )
    )
    del "%WEBUI_PID_FILE%" 2>nul
)

:: Force-free the port: kill ANY process holding port 8648 (not just node)
netstat -aon 2>nul | findstr ":%WEBUI_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARN] Port %WEBUI_PORT% in use, freeing it...
    for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%WEBUI_PORT% " ^| findstr "LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
        echo [INFO] Killed PID %%p that held port %WEBUI_PORT%
    ping 127.0.0.1 -n 2 >nul 2>&1
)

:: Verify port is now free
netstat -aon 2>nul | findstr ":%WEBUI_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [ERROR] Port %WEBUI_PORT% still in use after cleanup. Aborting.
    echo         Run manually: netstat -ano ^| findstr :%WEBUI_PORT%
    echo         Then stop the listed process or reboot Windows.
    pause
    exit /b 1
)

:: Backfill old Web UI databases where assistant messages were not persisted.
:: Run in background so it does not delay Node.js startup.
if defined PATCH_PY if exist "%SCRIPT_DIR%scripts\recover-webui-assistant-history.py" (
    powershell -NoProfile -Command ^
        "$py='%PATCH_PY%';$s='%SCRIPT_DIR%scripts\recover-webui-assistant-history.py';" ^
        "Start-Process -FilePath $py -ArgumentList $s -WindowStyle Hidden | Out-Null" >nul 2>&1
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

set "NPM_CONFIG_CACHE=%SCRIPT_DIR%.npm-cache"
set "npm_config_ignore_scripts=true"

if /i "%WEBUI_SERVER%"=="%WEBUI_DIR%\dist\server\index.js" (
    if not exist "%WEBUI_SOCKETIO%" (
        echo [INFO] Web UI dependencies missing, attempting auto-repair...
        if exist "%NPM_CMD%" (
            cd /d "%WEBUI_DIR%"
            call "%NPM_CMD%" install --omit=dev --registry https://registry.npmmirror.com --cache "%SCRIPT_DIR%\.npm-cache" --no-fund --no-audit
            if errorlevel 1 (
                echo [ERROR] Auto-repair failed. Please rerun full install.
                pause
                exit /b 1
            )
            if not exist "%WEBUI_SOCKETIO%" (
                echo [ERROR] Auto-repair failed. Please rerun full install.
                pause
                exit /b 1
            )
            echo [OK] Auto-repair completed, continuing startup...
        ) else (
            echo [ERROR] Web UI dependencies missing and npm is unavailable.
            echo         Please rerun full install.
            pause
            exit /b 1
        )
    )
)

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
echo [INFO] Install root: "%SCRIPT_DIR%"
echo [INFO] Node executable: "%NODE_EXE%"
echo [INFO] Web UI server: "%WEBUI_SERVER%"
echo [INFO] Auth mode: disabled for localhost
echo [INFO] Log file: "%WEBUI_LOG%"
cd /d "%WEBUI_DIR%"
for /f %%p in ('powershell -NoProfile -Command ^
    "$node=[IO.Path]::GetFullPath('%NODE_EXE%');" ^
    "$server=[IO.Path]::GetFullPath('%WEBUI_SERVER%');" ^
    "$work=[IO.Path]::GetFullPath('%WEBUI_DIR%');" ^
    "$log=[IO.Path]::GetFullPath('%WEBUI_LOG%');" ^
    "$logDir=[IO.Path]::GetDirectoryName($log);" ^
    "New-Item -ItemType Directory -Force -Path $logDir | Out-Null;" ^
    "$cmd='""' + $node + '"" ""' + $server + '"" >> ""' + $log + '"" 2>>&1';" ^
    "$p=Start-Process -FilePath $env:ComSpec -ArgumentList '/d','/s','/c',$cmd -WorkingDirectory $work -WindowStyle Hidden -PassThru;" ^
    "Start-Sleep -Milliseconds 300;" ^
    "Write-Output $p.Id"') do (
    if not defined WEBUI_WRAPPER_PID set "WEBUI_WRAPPER_PID=%%p"
)
if not defined WEBUI_WRAPPER_PID (
    echo [ERROR] Failed to launch Web UI wrapper process.
    echo         Possible causes:
    echo         - cmd.exe or PowerShell is blocked by policy.
    echo         - Node.js path is missing: "%NODE_EXE%"
    echo         - Web UI server path is missing: "%WEBUI_SERVER%"
    echo         - Log directory is not writable: "%USERPROFILE%\.hermes-web-ui"
    pause
    exit /b 1
)

:: Capture PID after a short settle delay
ping 127.0.0.1 -n 2 >nul 2>&1
for /f %%p in ('powershell -NoProfile -Command ^
    "$server=[IO.Path]::GetFullPath('%WEBUI_SERVER%');" ^
    "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -and $_.CommandLine.Contains($server) } | Sort-Object CreationDate -Descending | Select-Object -First 1 -ExpandProperty ProcessId"') do (
    if not defined WEBUI_PID set "WEBUI_PID=%%p"
)
if defined WEBUI_PID (
    echo !WEBUI_PID!>"%WEBUI_PID_FILE%"
    echo auth-disabled:%GATEWAY_PORT%:!WEBUI_PID!>"%WEBUI_MODE_FILE%"
    echo [INFO] Web UI PID: !WEBUI_PID!
)

call :start_launcher_page

:open_browser
if "%BROWSER_OPENED%"=="1" goto :after_browser_open
set "BROWSER_OPENED=1"
if defined WEBUI_LAUNCHER_PORT (
    set "BROWSER_URL=http://127.0.0.1:%WEBUI_LAUNCHER_PORT%/?targetPort=%WEBUI_PORT%^&gatewayPort=%GATEWAY_PORT%"
) else (
    set "BROWSER_URL=http://localhost:%WEBUI_PORT%/#/hermes/chat"
)
echo [INFO] Opening browser: %BROWSER_URL%
powershell -NoProfile -Command ^
    "try { Start-Process '%BROWSER_URL%'; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    start "" "%BROWSER_URL%"
)
:after_browser_open
call :is_webui_gateway_connected
if errorlevel 1 (
    echo [INFO] Hermes connection will finish inside the startup page.
)
echo [OK] Web UI is running at http://localhost:%WEBUI_PORT%
echo.
echo [INFO] Web UI startup will continue in background.
endlocal
exit /b 0

:resolve_hermes_home
set "ACTIVE_PROFILE_FILE=%USERPROFILE%\.hermes\active_profile"
if not exist "%ACTIVE_PROFILE_FILE%" exit /b 0
set "ACTIVE_PROFILE_NAME="
set /p ACTIVE_PROFILE_NAME=<"%ACTIVE_PROFILE_FILE%"
if not defined ACTIVE_PROFILE_NAME exit /b 0
if exist "%USERPROFILE%\.hermes\profiles\%ACTIVE_PROFILE_NAME%\config.yaml" (
    set "HERMES_HOME=%USERPROFILE%\.hermes\profiles\%ACTIVE_PROFILE_NAME%"
)
exit /b 0

:resolve_gateway_port
if not exist "%HERMES_HOME%\config.yaml" exit /b 0

:: 1. Try resolving using Python first
set "PORT_PY="
if exist "%SCRIPT_DIR%python_embedded\python.exe" (
    set "PORT_PY=%SCRIPT_DIR%python_embedded\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 set "PORT_PY=python"
)
if defined PORT_PY (
    for /f %%p in ('"%PORT_PY%" -c "import pathlib,sys,yaml; p=pathlib.Path(r'''%HERMES_HOME%\config.yaml'''); data=yaml.safe_load(p.read_text(encoding='utf-8')) or {}; extra=((data.get('platforms') or {}).get('api_server') or {}).get('extra') or {}; v=extra.get('port'); sys.stdout.write(str(int(v)) if str(v).strip().isdigit() else '')" 2^>nul') do (
        if not defined RESOLVED_GATEWAY_PORT (
            set "RESOLVED_GATEWAY_PORT=%%p"
            set "GATEWAY_PORT_SOURCE=%HERMES_HOME%\config.yaml platforms.api_server.extra.port (via PyYAML)"
        )
    )
)

:: 2. Fallback to robust PowerShell indentation-aware scanning
if not defined RESOLVED_GATEWAY_PORT (
    for /f %%p in ('powershell -NoProfile -Command ^
        "$path=[IO.Path]::GetFullPath('%HERMES_HOME%\config.yaml');" ^
        "$inPlatforms=$false;$inApi=$false;$inExtra=$false;$port='';" ^
        "foreach($line in Get-Content -LiteralPath $path){" ^
        "  if($line -match '^\s*(#|$)'){ continue }" ^
        "  $indent = 0;" ^
        "  if($line -match '^(\s*)'){ $indent = $matches[1].Length }" ^
        "  if($indent -le 2){ $inApi=$false; $inExtra=$false }" ^
        "  if($indent -le 4){ $inExtra=$false }" ^
        "  if($indent -eq 0){ $inPlatforms=$false }" ^
        "  if($line -match '^\s*platforms:\s*$'){ $inPlatforms=$true; continue }" ^
        "  if($inPlatforms -and $indent -eq 2 -and $line -match '^\s{2}api_server:\s*$'){ $inApi=$true; continue }" ^
        "  if($inApi -and $indent -eq 4 -and $line -match '^\s{4}extra:\s*$'){ $inExtra=$true; continue }" ^
        "  if($inExtra -and $indent -eq 6 -and $line -match '^\s{6}port:\s*(\d+)\s*$'){ $port=$matches[1]; break }" ^
        "}" ^
        "if($port){ Write-Output $port }"') do (
        if not defined RESOLVED_GATEWAY_PORT (
            set "RESOLVED_GATEWAY_PORT=%%p"
            set "GATEWAY_PORT_SOURCE=%HERMES_HOME%\config.yaml platforms.api_server.extra.port (via PowerShell)"
        )
    )
)

if defined RESOLVED_GATEWAY_PORT (
    set "GATEWAY_PORT=%RESOLVED_GATEWAY_PORT%"
)
exit /b 0

:resolve_install_root
set "RESOLVE_DIR=%~1"
if not defined RESOLVE_DIR exit /b 0
if exist "%RESOLVE_DIR%\node_embedded\node.exe" goto :resolve_install_root_done
if exist "%RESOLVE_DIR%\webui\dist\server\index.js" goto :resolve_install_root_done
if exist "%RESOLVE_DIR%\webui\node_modules\hermes-web-ui\dist\server\index.js" goto :resolve_install_root_done
for %%D in ("%RESOLVE_DIR%\.." "%RESOLVE_DIR%\..\..") do (
    if exist "%%~fD\node_embedded\node.exe" (
        set "SCRIPT_DIR=%%~fD"
        goto :resolve_install_root_done
    )
    if exist "%%~fD\webui\dist\server\index.js" (
        set "SCRIPT_DIR=%%~fD"
        goto :resolve_install_root_done
    )
    if exist "%%~fD\webui\node_modules\hermes-web-ui\dist\server\index.js" (
        set "SCRIPT_DIR=%%~fD"
        goto :resolve_install_root_done
    )
)
:resolve_install_root_done
exit /b 0

:start_launcher_page
if not exist "%WEBUI_LAUNCHER_DIR%\index.html" exit /b 0
set "WEBUI_LAUNCHER_PORT="
for /f %%p in ('powershell -NoProfile -Command "$l=New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Loopback,0);$l.Start();$p=$l.LocalEndpoint.Port;$l.Stop();Write-Output $p"') do (
    if not defined WEBUI_LAUNCHER_PORT set "WEBUI_LAUNCHER_PORT=%%p"
)
if not defined WEBUI_LAUNCHER_PORT set "WEBUI_LAUNCHER_PORT=8659"
if not defined PATCH_PY exit /b 0
powershell -NoProfile -Command ^
    "$python='%PATCH_PY%';" ^
    "$work=[IO.Path]::GetFullPath('%WEBUI_LAUNCHER_DIR%');" ^
    "$script=[IO.Path]::GetFullPath('%SCRIPT_DIR%scripts\webui_launcher_server.py');" ^
    "Start-Process -FilePath $python -ArgumentList $script,'--port','%WEBUI_LAUNCHER_PORT%','--root',$work -WorkingDirectory $work -WindowStyle Hidden | Out-Null" >nul 2>&1
rem Wait up to ~10s (7 rounds x 1.5s). The launcher server only imports
rem Python stdlib so it starts fast. Keep this wait very short: the launcher
rem page is only a visual bridge and must never block WebUI startup.
for /l %%i in (1,1,2) do (
    powershell -NoProfile -Command ^
        "try{Invoke-WebRequest 'http://127.0.0.1:%WEBUI_LAUNCHER_PORT%/' -TimeoutSec 1 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
    if !errorlevel! equ 0 exit /b 0
    ping 127.0.0.1 -n 2 >nul 2>&1
)
echo [WARN] Launcher page server did not start in time, browser will open WebUI directly.
set "WEBUI_LAUNCHER_PORT="
exit /b 0

:is_current_webui
if "%EXISTING_PID%"=="" exit /b 1
powershell -NoProfile -Command ^
    "$pidText='%EXISTING_PID%';" ^
    "$server=[IO.Path]::GetFullPath('%WEBUI_SERVER%');" ^
    "try{$p=Get-CimInstance Win32_Process -Filter ('ProcessId=' + [int]$pidText)}catch{$p=$null};" ^
    "if($p -and $p.CommandLine -and $p.CommandLine.Contains($server)){exit 0}else{exit 1}" >nul 2>&1
exit /b %errorlevel%

:is_expected_webui_mode
if "%EXISTING_PID%"=="" exit /b 1
if not exist "%WEBUI_MODE_FILE%" exit /b 1
set "WEBUI_MODE="
set /p WEBUI_MODE=<"%WEBUI_MODE_FILE%"
if /i "%WEBUI_MODE%"=="auth-disabled:%GATEWAY_PORT%:%EXISTING_PID%" exit /b 0
exit /b 1

:is_webui_gateway_connected
powershell -NoProfile -Command ^
    "try{$h=Invoke-RestMethod 'http://127.0.0.1:%WEBUI_PORT%/health' -TimeoutSec 2; if($h.gateway -eq 'running'){exit 0}else{exit 1}}catch{exit 1}" >nul 2>&1
exit /b %errorlevel%
