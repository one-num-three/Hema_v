@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ENV_FILE=%SCRIPT_DIR%.env"
for /f %%g in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString()"') do set "ENV_LOAD_SCRIPT=%TEMP%\hermes_env_%%g.cmd"

:: Load .env first so user vars are available, then set local vars after
:: (so local vars are not accidentally overridden by .env content).
:: Use PowerShell to generate a temporary .cmd file because plain FOR/CALL
:: parsing breaks easily when .env values contain characters like (), %, &.
if exist "%ENV_FILE%" (
    powershell -NoProfile -Command ^
        "$envFile = [IO.Path]::GetFullPath('%ENV_FILE%');" ^
        "$outFile = [IO.Path]::GetFullPath('%ENV_LOAD_SCRIPT%');" ^
        "Remove-Item -LiteralPath $outFile -ErrorAction SilentlyContinue;" ^
        "foreach($line in Get-Content -LiteralPath $envFile){" ^
        "  if($line -match '^\s*(#|$)'){ continue }" ^
        "  $parts = $line.Split('=', 2);" ^
        "  if($parts.Count -lt 2){ continue }" ^
        "  $key = $parts[0].Trim();" ^
        "  if([string]::IsNullOrWhiteSpace($key)){ continue }" ^
        "  $value = $parts[1];" ^
        "  $value = $value.Replace('^^','^^^^').Replace('%%','%%%%').Replace('(','^^(').Replace(')','^^)');" ^
        "  Add-Content -LiteralPath $outFile -Value ('set ""{0}={1}""' -f $key, $value);" ^
        "}"
    if errorlevel 1 (
        echo [ERROR] Failed to parse "%ENV_FILE%".
        exit /b 1
    )
    if exist "%ENV_LOAD_SCRIPT%" (
        call "%ENV_LOAD_SCRIPT%"
        del "%ENV_LOAD_SCRIPT%" 2>nul
    )
)

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

:: If the health endpoint answers, the gateway is already running.
powershell -NoProfile -Command ^
    "try{Invoke-WebRequest 'http://%GATEWAY_HOST%:%GATEWAY_PORT%/health' -TimeoutSec 2 -UseBasicParsing|Out-Null;exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% equ 0 (
    call :is_current_gateway
    if !errorlevel! equ 0 (
        echo [OK] Hermes gateway already running on port %GATEWAY_PORT%.
        exit /b 0
    )
    echo [WARN] Gateway on port %GATEWAY_PORT% belongs to another install, restarting it...
    call :free_gateway_port
)
if exist "%GATEWAY_PID_FILE%" del "%GATEWAY_PID_FILE%" 2>nul

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

:: Start gateway in background. Use Start-Process so the gateway stays alive
:: after this batch file exits; "start /b" is not reliable for detached
:: Python processes on Windows.
echo [INFO] Starting Hermes gateway on %GATEWAY_HOST%:%GATEWAY_PORT%...
cd /d "%SCRIPT_DIR%"

for /f %%p in ('powershell -NoProfile -Command ^
    "$p = Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList '-m','hermes_cli.main','gateway' -WorkingDirectory '%SCRIPT_DIR%' -WindowStyle Hidden -PassThru;" ^
    "Start-Sleep -Seconds 1;" ^
    "Write-Output $p.Id"') do (
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
powershell -NoProfile -Command "Start-Sleep -Seconds 1" >nul 2>&1
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

:is_current_gateway
if not exist "%GATEWAY_PID_FILE%" exit /b 1
powershell -NoProfile -Command ^
    "$raw=Get-Content -LiteralPath '%GATEWAY_PID_FILE%' -Raw;" ^
    "try{$pidValue=[int](($raw|ConvertFrom-Json).pid)}catch{if($raw -match '\d+'){$pidValue=[int]$matches[0]}else{exit 1}};" ^
    "$root=[IO.Path]::GetFullPath('%SCRIPT_DIR%').TrimEnd('\');" ^
    "$python=[IO.Path]::GetFullPath('%PYTHON_EXE%');" ^
    "try{$p=Get-CimInstance Win32_Process -Filter ('ProcessId=' + $pidValue)}catch{$p=$null};" ^
    "if($p -and (($p.ExecutablePath -and ([IO.Path]::GetFullPath($p.ExecutablePath) -ieq $python)) -or ($p.CommandLine -and $p.CommandLine.Contains($root)))){exit 0}else{exit 1}" >nul 2>&1
exit /b %errorlevel%

:free_gateway_port
for /f "tokens=5" %%p in ('netstat -aon 2^>nul ^| findstr ":%GATEWAY_PORT% " ^| findstr "LISTENING"') do (
    taskkill /F /PID %%p >nul 2>&1
    echo [INFO] Killed PID %%p that held port %GATEWAY_PORT%
)
powershell -NoProfile -Command "Start-Sleep -Seconds 2" >nul 2>&1
exit /b 0
