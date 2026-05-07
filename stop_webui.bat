@echo off
setlocal enabledelayedexpansion

set "WEBUI_PID_FILE=%USERPROFILE%\.hermes-web-ui\server.pid"
set "GATEWAY_PID_FILE=%USERPROFILE%\.hermes\gateway.pid"

:: 停止 Web UI
if exist "%WEBUI_PID_FILE%" (
    set /p WEBUI_PID=<"%WEBUI_PID_FILE%"
    taskkill /F /PID !WEBUI_PID! >nul 2>&1
    del "%WEBUI_PID_FILE%"
    echo [OK] Web UI stopped (PID: !WEBUI_PID!).
) else (
    echo [INFO] Web UI is not running.
)

:: 询问是否也停止 Gateway
if "%~1"=="--all" goto :stop_gateway
if "%~1"=="-a" goto :stop_gateway
goto :done

:stop_gateway
if exist "%GATEWAY_PID_FILE%" (
    set /p GW_PID=<"%GATEWAY_PID_FILE%"
    taskkill /F /PID !GW_PID! >nul 2>&1
    del "%GATEWAY_PID_FILE%"
    echo [OK] Hermes gateway stopped (PID: !GW_PID!).
) else (
    echo [INFO] Gateway is not running.
)

:done
endlocal
