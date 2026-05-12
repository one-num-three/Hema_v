@echo off
chcp 65001 >nul
title 彻底删除 WSL
color 0C

echo ========================================
echo   彻底删除 Windows Subsystem for Linux
echo ========================================
echo.
echo   [1/5] 关闭并注销所有 WSL 发行版...
wsl --shutdown
wsl --unregister Ubuntu-24.04 2>nul
wsl --unregister Ubuntu 2>nul
wsl --unregister debian 2>nul
wsl --unregister kali-linux 2>nul
wsl --unregister docker-desktop-data 2>nul
wsl --unregister docker-desktop 2>nul
echo   OK - 发行版已注销

echo.
echo   [2/5] 卸载 WSL 功能...
dism /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart /quiet
echo   OK - WSL 功能已禁用

echo.
echo   [3/5] 删除 WindowsApps 里的 WSL stub (0字节假bash)...
takeown /f "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe" /a >nul 2>&1
icacls "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe" /grant Administrators:F >nul 2>&1
del /f /q "%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\bash.exe" >nul 2>&1
echo   OK - WSL stub 已删除

echo.
echo   [4/5] 删除 wsl.exe 自身（可选，不影响 Git Bash）...
echo   保留 wsl.exe 以防万一，但删除了 bash.exe stub

echo.
echo   [5/5] 清理 Lxss 文件夹（WSL 用户数据）...
rmdir /s /q "%LOCALAPPDATA%\Packages\CanonicalGroupLimited.Ubuntu*" >nul 2>&1
rmdir /s /q "%LOCALAPPDATA%\Packages\TheDebianProject.Debian*" >nul 2>&1
rmdir /s /q "%LOCALAPPDATA%\Packages\*WSL*" >nul 2>&1
echo   OK - WSL 用户数据已清理

echo.
echo ========================================
echo   完成！建议重启电脑
echo ========================================
echo.
echo   重启后运行: where bash
echo   应该只显示: D:\Program Files\Git\bin\bash.exe
echo.
pause
