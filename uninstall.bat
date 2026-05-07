@echo off
:: ============================================================
:: uninstall.bat - Hermes Agent 卸载脚本
:: 仅删除安装目录内的组件；用户数据需手动确认删除
:: ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
set "SCRIPT_DIR=%~dp0"

echo.
echo ============================================================
echo   Hermes Agent 卸载程序
echo ============================================================
echo.
echo   安装目录: %SCRIPT_DIR%
echo.

:: ── 停止运行中的服务 ─────────────────────────────────────────
echo [1/4] 停止 Web UI 和 Gateway...

set "WEBUI_PID_FILE=%USERPROFILE%\.hermes-web-ui\server.pid"
if exist "%WEBUI_PID_FILE%" (
    set /p WEBUI_PID=<"%WEBUI_PID_FILE%"
    taskkill /F /PID !WEBUI_PID! >nul 2>&1
    del "%WEBUI_PID_FILE%" 2>nul
    echo [OK] Web UI 已停止 (PID: !WEBUI_PID!)
) else (
    echo [INFO] Web UI 未在运行
)

set "GW_PID_FILE=%USERPROFILE%\.hermes\gateway.pid"
if exist "%GW_PID_FILE%" (
    set /p GW_PID=<"%GW_PID_FILE%"
    taskkill /F /PID !GW_PID! >nul 2>&1
    del "%GW_PID_FILE%" 2>nul
    echo [OK] Gateway 已停止 (PID: !GW_PID!)
) else (
    echo [INFO] Gateway 未在运行
)

:: 保险起见，杀掉所有本目录下的 node/python 进程
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── 删除 Full 版组件 ─────────────────────────────────────────
echo [2/4] 删除 Node.js 和 Web UI 组件...

if exist "%SCRIPT_DIR%node_embedded" (
    echo       删除 node_embedded/ (~95MB)...
    rmdir /s /q "%SCRIPT_DIR%node_embedded" 2>nul
    if not exist "%SCRIPT_DIR%node_embedded" (
        echo [OK] node_embedded/ 已删除
    ) else (
        echo [WARN] node_embedded/ 删除失败，请手动删除
    )
) else (
    echo [INFO] node_embedded/ 不存在，跳过
)

if exist "%SCRIPT_DIR%webui" (
    echo       删除 webui/ (~155MB)...
    rmdir /s /q "%SCRIPT_DIR%webui" 2>nul
    if not exist "%SCRIPT_DIR%webui" (
        echo [OK] webui/ 已删除
    ) else (
        echo [WARN] webui/ 删除失败，请手动删除
    )
) else (
    echo [INFO] webui/ 不存在，跳过
)

:: ── 删除 npm 缓存和临时文件 ─────────────────────────────────
echo [3/4] 清理缓存和临时文件...

if exist "%SCRIPT_DIR%.npm-cache" (
    rmdir /s /q "%SCRIPT_DIR%.npm-cache" 2>nul
    echo [OK] .npm-cache/ 已删除
)
if exist "%SCRIPT_DIR%node_tmp" (
    rmdir /s /q "%SCRIPT_DIR%node_tmp" 2>nul
)
if exist "%SCRIPT_DIR%_build" (
    rmdir /s /q "%SCRIPT_DIR%_build" 2>nul
)
if exist "%SCRIPT_DIR%tools\7za.exe" (
    del "%SCRIPT_DIR%tools\7za.exe" 2>nul
)

:: ── 询问是否删除用户数据 ─────────────────────────────────────
echo [4/4] 用户数据处理...
echo.
echo   以下用户数据位于您的个人目录（不在安装目录内）：
echo     %USERPROFILE%\.hermes\          （Agent 配置、技能权限）
echo     %USERPROFILE%\.hermes-web-ui\   （Web UI 数据、认证 Token）
echo.
set /p "DEL_USERDATA=  是否同时删除用户数据？删除后无法恢复 [y/N]: "
if /i "!DEL_USERDATA!"=="y" (
    if exist "%USERPROFILE%\.hermes" (
        rmdir /s /q "%USERPROFILE%\.hermes" 2>nul
        echo [OK] %USERPROFILE%\.hermes\ 已删除
    )
    if exist "%USERPROFILE%\.hermes-web-ui" (
        rmdir /s /q "%USERPROFILE%\.hermes-web-ui" 2>nul
        echo [OK] %USERPROFILE%\.hermes-web-ui\ 已删除
    )
) else (
    echo [INFO] 用户数据已保留
)

echo.
echo ============================================================
echo   卸载完成。
echo   请手动删除安装目录: %SCRIPT_DIR%
echo ============================================================
echo.
pause
endlocal
