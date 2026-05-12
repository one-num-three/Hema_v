@echo off
chcp 65001 >nul
title 彻底删除 WSL - 请以管理员身份运行
cd /d "%~dp0"

echo ========================================
echo   彻底删除 Windows Subsystem for Linux
echo   请确保已以管理员身份运行！
echo ========================================
echo.

:: ========== [1] 关闭并注销所有 WSL 发行版 ==========
echo [1/5] 关闭并注销所有 WSL 发行版...
wsl --shutdown 2>nul

:: 列出所有发行版并逐个注销
for /f "tokens=1 delims= " %%d in ('wsl -l --quiet 2^>nul') do (
    echo   正在注销: %%d
    wsl --unregister %%d 2>nul
)
:: 备用：尝试已知名称
wsl --unregister Ubuntu 2>nul
wsl --unregister ubuntu 2>nul
wsl --unregister Debian 2>nul
wsl --unregister kali-linux 2>nul
wsl --unregister Alpine 2>nul
wsl --unregister docker-desktop 2>nul
wsl --unregister docker-desktop-data 2>nul
echo   OK - 发行版已注销
echo.

:: ========== [2] 卸载 WSL 功能 ==========
echo [2/5] 卸载 WSL 功能...
dism /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart /quiet
dism /online /disable-feature /featurename:VirtualMachinePlatform /norestart /quiet
echo   OK - WSL 功能已禁用
echo.

:: ========== [3] 删除 wsl.exe ==========
echo [3/5] 删除 wsl.exe 本体...
takeown /f "%SystemRoot%\System32\wsl.exe" >nul 2>&1
icacls "%SystemRoot%\System32\wsl.exe" /grant Administrators:F >nul 2>&1
del /f /q "%SystemRoot%\System32\wsl.exe" 2>nul && echo   OK - System32\wsl.exe 已删除

takeown /f "%SystemRoot%\SysWOW64\wsl.exe" >nul 2>&1
icacls "%SystemRoot%\SysWOW64\wsl.exe" /grant Administrators:F >nul 2>&1
del /f /q "%SystemRoot%\SysWOW64\wsl.exe" 2>nul && echo   OK - SysWOW64\wsl.exe 已删除

if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\wsl.exe" (
    del /f /q "%LOCALAPPDATA%\Microsoft\WindowsApps\wsl.exe" 2>nul && echo   OK - WindowsApps\wsl.exe 已删除
)
echo.

:: ========== [4] 删除 WSL 内核和 Lxss 数据 ==========
echo [4/5] 清理 WSL 内核和数据...
if exist "%SystemRoot%\System32\lxss" (
    takeown /f "%SystemRoot%\System32\lxss" /r /d y >nul 2>&1
    icacls "%SystemRoot%\System32\lxss" /grant Administrators:F /t >nul 2>&1
    rmdir /s /q "%SystemRoot%\System32\lxss" 2>nul
    echo   OK - lxss 文件夹已删除
)

if exist "%USERPROFILE%\AppData\Local\lxss" (
    rmdir /s /q "%USERPROFILE%\AppData\Local\lxss" 2>nul
    echo   OK - 用户 lxss 数据已删除
)

:: 删除 WSL 内核安装包
del /f /q "%TEMP%\wsl*" 2>nul
echo.

:: ========== [5] 清理注册表残留 ==========
echo [5/5] 清理注册表残留...
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss" /f >nul 2>&1 && echo   OK - Lxss 注册表键已删除
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WSL" /f >nul 2>&1 && echo   OK - WSL 注册表键已删除
echo.

echo ========================================
echo   清理完成！
echo ========================================
echo.
echo 接下来建议操作：
echo   1. 重启电脑（推荐）
echo   2. 重启后运行: where bash
echo      应该只显示: D:\Program Files\Git\usr\bin\bash.exe
echo.
echo   Git Bash 不受影响，继续可用！
echo.
pause
