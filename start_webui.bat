@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "NODE_DIR=%SCRIPT_DIR%node_embedded"
set "NODE_EXE=%NODE_DIR%\node.exe"
set "NPM_CMD=%NODE_DIR%\npm.cmd"
set "WEBUI_DIR=%SCRIPT_DIR%webui"
set "WEBUI_SERVER=%WEBUI_DIR%\dist\server\index.js"
set "WEBUI_NPM_SERVER=%WEBUI_DIR%\node_modules\hermes-web-ui\dist\server\index.js"
set "WEBUI_SOCKETIO=%WEBUI_DIR%\node_modules\socket.io\package.json"
set "WEBUI_PORT=8648"
set "GATEWAY_PORT=8642"
set "WEBUI_PID_FILE=%USERPROFILE%\.hermes-web-ui\server.pid"
set "WEBUI_MODE_FILE=%USERPROFILE%\.hermes-web-ui\server.mode"
set "WEBUI_LOG=%USERPROFILE%\.hermes-web-ui\server.log"

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

:: Make sure the gateway belongs to this install before opening Web UI.
echo [INFO] Checking Hermes gateway (port %GATEWAY_PORT%)...
call "%SCRIPT_DIR%start_hermes_gateway.bat"
if errorlevel 1 (
    echo [ERROR] Failed to start Hermes gateway.
    echo         Web UI requires gateway on port %GATEWAY_PORT%.
    pause
    exit /b 1
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
                    echo [OK] Web UI already running ^(PID: !EXISTING_PID!, port: %WEBUI_PORT%^)
                    goto :open_browser
                ) else (
                    echo [WARN] Existing Web UI was started with old settings, restarting it...
                    taskkill /F /PID !EXISTING_PID! >nul 2>&1
                    powershell -NoProfile -Command "Start-Sleep -Seconds 2" >nul 2>&1
                )
            )
        ) else (
            echo [WARN] Existing Web UI PID belongs to another install, restarting it...
            taskkill /F /PID !EXISTING_PID! >nul 2>&1
            powershell -NoProfile -Command "Start-Sleep -Seconds 2" >nul 2>&1
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
    )
    powershell -NoProfile -Command "Start-Sleep -Seconds 2" >nul 2>&1
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
if exist "%SCRIPT_DIR%scripts\recover-webui-assistant-history.py" if exist "%SCRIPT_DIR%python_embedded\python.exe" (
    "%SCRIPT_DIR%python_embedded\python.exe" "%SCRIPT_DIR%scripts\recover-webui-assistant-history.py" >nul 2>&1
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
    "Start-Sleep -Seconds 1;" ^
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

:: Capture PID after 1s
powershell -NoProfile -Command "Start-Sleep -Seconds 1" >nul 2>&1
for /f %%p in ('powershell -NoProfile -Command ^
    "$server=[IO.Path]::GetFullPath('%WEBUI_SERVER%');" ^
    "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -and $_.CommandLine.Contains($server) } | Sort-Object CreationDate -Descending | Select-Object -First 1 -ExpandProperty ProcessId"') do (
    if not defined WEBUI_PID set "WEBUI_PID=%%p"
)
if defined WEBUI_PID (
    echo !WEBUI_PID!>"%WEBUI_PID_FILE%"
    echo auth-disabled:!WEBUI_PID!>"%WEBUI_MODE_FILE%"
    echo [INFO] Web UI PID: !WEBUI_PID!
)

:: Poll /health up to 30 seconds
set "MAX_WAIT=30"
set "WAITED=0"
:wait_webui
powershell -NoProfile -Command "Start-Sleep -Seconds 1" >nul 2>&1
set /a WAITED+=1
powershell -NoProfile -Command ^
    "try{Invoke-WebRequest 'http://127.0.0.1:%WEBUI_PORT%/health' -TimeoutSec 2 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% equ 0 (
    if not defined WEBUI_PID (
        for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%WEBUI_PORT% " ^| findstr "LISTENING"') do (
            if not defined WEBUI_PID set "WEBUI_PID=%%p"
        )
        if defined WEBUI_PID (
            echo !WEBUI_PID!>"%WEBUI_PID_FILE%"
            echo auth-disabled:!WEBUI_PID!>"%WEBUI_MODE_FILE%"
            echo [INFO] Web UI PID: !WEBUI_PID!
        )
    )
    echo [OK] hermes-web-ui ready.
    goto :open_browser
)
if %WAITED% LSS %MAX_WAIT% goto :wait_webui
echo [WARN] Web UI did not respond in %MAX_WAIT%s.
echo        Check log: %WEBUI_LOG%
echo.
echo [DIAG] Expected files:
if exist "%NODE_EXE%" (echo        [OK] "%NODE_EXE%") else (echo        [MISS] "%NODE_EXE%")
if exist "%WEBUI_SERVER%" (echo        [OK] "%WEBUI_SERVER%") else (echo        [MISS] "%WEBUI_SERVER%")
echo.
echo [DIAG] Recent Web UI log:
powershell -NoProfile -Command "if(Test-Path -LiteralPath '%WEBUI_LOG%'){Get-Content -LiteralPath '%WEBUI_LOG%' -Tail 30}else{Write-Host 'Log file does not exist.'}" 2>nul
echo.
echo [DIAG] Common causes:
echo        - The installer copied an old or incomplete webui directory from CDN.
echo        - node_embedded was not installed or was removed by antivirus.
echo        - port %WEBUI_PORT% is occupied by another process.
echo        - node-pty failed to load on this Windows environment; check the log above.
echo [ERROR] Web UI failed to start, browser will not be opened.
pause
exit /b 1

:open_browser
:: Open local Web UI. Auth is disabled for localhost in this launcher.
set "BROWSER_URL=http://localhost:%WEBUI_PORT%/"
echo [INFO] Opening browser: %BROWSER_URL%
powershell -NoProfile -Command ^
    "try { Start-Process '%BROWSER_URL%'; exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel% neq 0 (
    start "" "%BROWSER_URL%"
)
echo [OK] Web UI is running at http://localhost:%WEBUI_PORT%
echo.
endlocal
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
if /i "%WEBUI_MODE%"=="auth-disabled:%EXISTING_PID%" exit /b 0
exit /b 1
