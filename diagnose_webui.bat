@echo off
setlocal

for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%T"
set "OUT=%USERPROFILE%\Desktop\hema_webui_diagnosis_%TS%.txt"

> "%OUT%" echo Hema / Hermes Web UI diagnosis
>> "%OUT%" echo Time: %date% %time%
>> "%OUT%" echo Script: %~f0
>> "%OUT%" echo CWD: %cd%
>> "%OUT%" echo UserProfile: %USERPROFILE%
>> "%OUT%" echo.

>> "%OUT%" echo [Install files]
>> "%OUT%" echo start_webui.bat: %~dp0start_webui.bat
>> "%OUT%" echo node_embedded\node.exe exists:
if exist "%~dp0node_embedded\node.exe" (>> "%OUT%" echo YES) else (>> "%OUT%" echo NO)
>> "%OUT%" echo webui exists:
if exist "%~dp0webui" (>> "%OUT%" echo YES) else (>> "%OUT%" echo NO)
>> "%OUT%" echo.

>> "%OUT%" echo [Modern browsers]
powershell -NoProfile -Command "$p=@('%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe','%ProgramFiles%\Microsoft\Edge\Application\msedge.exe','%LocalAppData%\Microsoft\Edge\Application\msedge.exe','%ProgramFiles%\Google\Chrome\Application\chrome.exe','%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe','%LocalAppData%\Google\Chrome\Application\chrome.exe'); foreach($x in $p){ if(Test-Path -LiteralPath $x){ Write-Output ('FOUND ' + $x) } }" >> "%OUT%" 2>&1
>> "%OUT%" echo.

>> "%OUT%" echo [Ports]
netstat -aon | findstr ":8648 " >> "%OUT%" 2>&1
netstat -aon | findstr ":8642 " >> "%OUT%" 2>&1
>> "%OUT%" echo.

>> "%OUT%" echo [Processes]
powershell -NoProfile -Command "$items=Get-CimInstance Win32_Process; foreach($p in $items){ if($p.Name -eq 'node.exe' -or $p.CommandLine -like '*8648*' -or $p.CommandLine -like '*hermes-web-ui*' -or $p.CommandLine -like '*hermes_cli.main gateway*'){ Write-Output ('ProcessId: ' + $p.ProcessId); Write-Output ('Name: ' + $p.Name); Write-Output ('ExecutablePath: ' + $p.ExecutablePath); Write-Output ('CommandLine: ' + $p.CommandLine); Write-Output '' } }" >> "%OUT%" 2>&1
>> "%OUT%" echo.

>> "%OUT%" echo [HTTP checks]
powershell -NoProfile -Command "$urls=@('http://127.0.0.1:8648/','http://localhost:8648/','http://127.0.0.1:8642/health'); foreach($u in $urls){ try{ $r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 8; Write-Output ('OK ' + $u + ' status=' + $r.StatusCode + ' bytes=' + $r.RawContentLength) } catch { Write-Output ('ERR ' + $u + ' ' + $_.Exception.Message) } }" >> "%OUT%" 2>&1
>> "%OUT%" echo.

>> "%OUT%" echo [Web UI asset checks]
powershell -NoProfile -Command "try{ $html=(Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8648/' -TimeoutSec 8).Content; $q=[char]34; $pattern='(?:src|href)=' + $q + '([^' + $q + ']+)' + $q; $seen=@{}; $matches=[regex]::Matches($html,$pattern); foreach($m in $matches){ $a=$m.Groups[1].Value; if(($a -like '/assets/*' -or $a -like '/hema-apps.js*') -and -not $seen.ContainsKey($a)){ $seen[$a]=1; $u='http://127.0.0.1:8648' + $a; try{ $r=Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 8; Write-Output ('OK ' + $a + ' status=' + $r.StatusCode + ' bytes=' + $r.RawContentLength) } catch { Write-Output ('ERR ' + $a + ' ' + $_.Exception.Message) } } } } catch { Write-Output ('ERR unable to fetch homepage assets: ' + $_.Exception.Message) }" >> "%OUT%" 2>&1
>> "%OUT%" echo.

>> "%OUT%" echo [Launcher bootstrap log tail]
if exist "%USERPROFILE%\.hermes-web-ui\launcher-bootstrap.log" (
    powershell -NoProfile -Command "Get-Content -LiteralPath '%USERPROFILE%\.hermes-web-ui\launcher-bootstrap.log' -Tail 120" >> "%OUT%" 2>&1
) else (
    >> "%OUT%" echo missing
)
>> "%OUT%" echo.

>> "%OUT%" echo [Server log tail]
if exist "%USERPROFILE%\.hermes-web-ui\server.log" (
    powershell -NoProfile -Command "Get-Content -LiteralPath '%USERPROFILE%\.hermes-web-ui\server.log' -Tail 160" >> "%OUT%" 2>&1
) else (
    >> "%OUT%" echo missing
)
>> "%OUT%" echo.

>> "%OUT%" echo [Server error log tail]
if exist "%USERPROFILE%\.hermes-web-ui\server.err.log" (
    powershell -NoProfile -Command "Get-Content -LiteralPath '%USERPROFILE%\.hermes-web-ui\server.err.log' -Tail 160" >> "%OUT%" 2>&1
) else (
    >> "%OUT%" echo missing
)

echo.
echo [OK] Diagnosis written to:
echo "%OUT%"
echo.
pause
endlocal
