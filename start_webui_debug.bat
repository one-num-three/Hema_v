@echo off
setlocal

echo [INFO] Running start_webui.bat in debug mode...
echo [INFO] This window will stay open after launch.
echo.

call "%~dp0start_webui.bat"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo [INFO] start_webui.bat exit code: %EXIT_CODE%
echo [INFO] Bootstrap log: %USERPROFILE%\.hermes-web-ui\launcher-bootstrap.log
echo [INFO] WebUI log: %USERPROFILE%\.hermes-web-ui\server.log
echo.
pause
exit /b %EXIT_CODE%
