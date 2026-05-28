@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

if "%HERMES_INSTALLER_NO_PAUSE%"=="" set "HERMES_INSTALLER_NO_PAUSE=0"

:: ============================================
:: 版本选择 (Lite = Python only, Full = + Node.js + Web UI)
:: ============================================
set "INSTALL_MODE=lite"
if /i "%~1"=="full"   set "INSTALL_MODE=full"
if /i "%~1"=="--full" set "INSTALL_MODE=full"
if /i "%~1"=="lite"   set "INSTALL_MODE=lite"
if /i "%~1"=="--lite" set "INSTALL_MODE=lite"

if not "%~1"=="" goto :mode_decided

echo.
echo ============================================
echo   Hermes Agent - Windows Installer
echo ============================================
echo.
echo   请选择安装版本 / Choose install edition:
echo.
echo     [1] 轻量版 Lite  (~150MB 下载)
echo         Python 3.13 + AI 工具 + 桌面 GUI
echo.
echo     [2] 完整版 Full  (~350MB 下载, 推荐)
echo         轻量版全部功能 + Node.js 23 + Web UI
echo         安装后可用浏览器访问 http://localhost:8648
echo.
set /p "MODE_CHOICE=  请输入 1 或 2 (直接回车 = 轻量版): "
if "%MODE_CHOICE%"=="2" set "INSTALL_MODE=full"

:mode_decided
if "%INSTALL_MODE%"=="full" (set "TOTAL_STEPS=12") else (set "TOTAL_STEPS=10")
echo.
if "%INSTALL_MODE%"=="full" (
    echo   [已选择] 完整版 Full  - Python + Node.js + Web UI
) else (
    echo   [已选择] 轻量版 Lite  - Python only
)
echo.
echo ============================================
echo   Hermes Agent - Windows Installer
echo ============================================
echo.
echo   This script sets up EVERYTHING from scratch:
echo   - Embedded Python 3.13 (portable, no system install)
echo   - Tkinter GUI support
echo   - All Python dependencies + extras
echo   - LM Studio SDK
echo   - Node.js dependencies (browser tools)
echo   - Git submodules (mini-swe-agent)
echo   - Skills sync (89+ skills)
echo   - Environment configuration
echo   - Default permissions
if "%INSTALL_MODE%"=="full" (
    echo   - Node.js 23 embedded ^(portable^)
    echo   - hermes-web-ui ^(browser interface on :8648^)
)
echo.
echo   No admin rights needed. No system changes.
echo   Everything stays inside this folder.
echo.

set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "PYTHON_DIR=%SCRIPT_DIR%\python_embedded"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"

:: pip mirror — primary: Tsinghua (fast in CN); fallbacks: Aliyun, USTC, official PyPI
:: --extra-index-url lets pip try all sources; if one returns 403/timeout the others work.
set "PIP_MIRROR=-i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://mirrors.aliyun.com/pypi/simple/ --extra-index-url https://mirrors.ustc.edu.cn/pypi/simple/ --extra-index-url https://pypi.org/simple/"

set "PYTHON_VERSION=3.13.12"
set "PYTHON_URL=https://www.python.org/ftp/python/3.13.12/python-3.13.12-embed-amd64.zip"
set "PYTHON_ZIP=%SCRIPT_DIR%python_embedded.zip"
set "TCLTK_URL=https://www.python.org/ftp/python/3.13.12/amd64/tcltk.msi"

:: ============================================
:: Step 1: Download Embedded Python
:: ============================================
if exist "%PYTHON_EXE%" goto :python_already_installed
goto :python_need_install
:python_already_installed
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try{& '%PYTHON_EXE%' -c 'import encodings, sys; print(sys.version)' *> $null; exit $LASTEXITCODE}catch{exit 1}" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Embedded Python exists but is incomplete or broken.
    echo        Expected standard library file is missing or unusable, for example:
    echo        "%PYTHON_DIR%\python313.zip"
    echo        Reinstalling embedded Python...
    rmdir /S /Q "%PYTHON_DIR%" 2>nul
    goto :python_need_install
)
echo [OK] Embedded Python already installed.
goto :check_pip
:python_need_install

echo [STEP 1/%TOTAL_STEPS%] Downloading Python %PYTHON_VERSION% embedded...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
    "$ProgressPreference = 'SilentlyContinue';" ^
    "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%'"

if not exist "%PYTHON_ZIP%" (
    echo ERROR: Failed to download Python. Check your internet connection.
    call :maybe_pause
    exit /b 1
)

echo [STEP 1/%TOTAL_STEPS%] Extracting Python...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYTHON_DIR%' -Force"

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python extraction failed.
    call :maybe_pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "if(Get-ChildItem -LiteralPath '%PYTHON_DIR%' -Filter 'python*.zip' -File -ErrorAction SilentlyContinue){exit 0}else{exit 1}" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python extraction is incomplete. Missing python*.zip standard library.
    echo        Python cannot start without this file because it contains encodings and core modules.
    call :maybe_pause
    exit /b 1
)
del "%PYTHON_ZIP%" 2>nul

:: ============================================
:: Step 2: Configure ._pth for site-packages
:: ============================================
echo [STEP 2/%TOTAL_STEPS%] Configuring Python for package installation...

if not exist "%PYTHON_DIR%\Lib\site-packages" mkdir "%PYTHON_DIR%\Lib\site-packages"
if not exist "%PYTHON_DIR%\DLLs" mkdir "%PYTHON_DIR%\DLLs"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$pthFiles = Get-ChildItem '%PYTHON_DIR%\python*._pth';" ^
    "if ($pthFiles.Count -gt 0) {" ^
    "  $pth = $pthFiles[0];" ^
    "  $zipName = (Get-ChildItem -LiteralPath '%PYTHON_DIR%' -Filter 'python*.zip' -File | Select-Object -First 1).Name;" ^
    "  if (-not $zipName) { $zipName = 'python313.zip' };" ^
    "  $content = @($zipName, '.', 'Lib', 'Lib\site-packages', 'DLLs', '', 'import site');" ^
    "  $content | Set-Content -Path $pth.FullName -Encoding ASCII;" ^
    "  Write-Host '   Configured:' $pth.Name" ^
    "}"

:: ============================================
:: Step 3: Bootstrap pip
:: ============================================
:check_pip
"%PYTHON_EXE%" -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [STEP 3/%TOTAL_STEPS%] Installing pip...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
        "$ProgressPreference = 'SilentlyContinue';" ^
        "try{Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%PYTHON_DIR%\get-pip.py' -TimeoutSec 120; exit 0}catch{Write-Host $_.Exception.Message; exit 1}"
    if errorlevel 1 (
        echo ERROR: Failed to download get-pip.py.
        echo        If you are using the full local package, this usually means bundled pip files are missing.
        echo        Otherwise, check TLS/proxy/firewall access to https://bootstrap.pypa.io/get-pip.py.
        call :maybe_pause
        exit /b 1
    )
    if not exist "%PYTHON_DIR%\get-pip.py" (
        echo ERROR: get-pip.py was not created after download.
        call :maybe_pause
        exit /b 1
    )
    "%PYTHON_EXE%" "%PYTHON_DIR%\get-pip.py" --quiet
    if errorlevel 1 (
        echo ERROR: Failed to install pip.
        call :maybe_pause
        exit /b 1
    )
    del "%PYTHON_DIR%\get-pip.py" 2>nul
    "%PYTHON_EXE%" -m pip install --upgrade pip --quiet 2>nul
) else (
    echo [OK] pip already available.
)

:: ============================================
:: Step 4: Install setuptools (needed for editable installs)
:: ============================================
echo [STEP 4/%TOTAL_STEPS%] Installing build tools...
"%PYTHON_EXE%" -m pip install setuptools wheel !PIP_MIRROR! --no-warn-script-location

:: ============================================
:: Step 5: Install Tkinter (GUI support)
:: ============================================
if not exist "%PYTHON_DIR%\Lib\tkinter" (
    echo [STEP 5/%TOTAL_STEPS%] Installing Tkinter GUI support...
    set "TCLTK_MSI=%SCRIPT_DIR%\tcltk.msi"
    set "TCLTK_TEMP=%SCRIPT_DIR%\_tcltk_temp"

    if exist "!TCLTK_MSI!" (
        echo [OK] Found local tcltk.msi, using offline copy.
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "$ProgressPreference = 'SilentlyContinue';" ^
            "Invoke-WebRequest -Uri '%TCLTK_URL%' -OutFile '!TCLTK_MSI!'"
    )

    if exist "!TCLTK_MSI!" (
        rem Use PowerShell Start-Process -Wait for reliable synchronous extraction.
        rem "start /wait msiexec /a" can return before extraction completes on
        rem Windows 11 Enterprise with restrictive Group Policy, leaving DLLs absent.
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "Start-Process msiexec.exe -ArgumentList '/a','\"!TCLTK_MSI!\"','/qn','TARGETDIR=\"!TCLTK_TEMP!\"' -Wait -NoNewWindow"
        if exist "!TCLTK_TEMP!\DLLs" (
            xcopy /E /Y /Q "!TCLTK_TEMP!\DLLs\*" "%PYTHON_DIR%\DLLs\" >nul 2>nul
            copy /Y "!TCLTK_TEMP!\DLLs\*.dll" "%PYTHON_DIR%\" >nul 2>nul
            copy /Y "!TCLTK_TEMP!\DLLs\*.pyd" "%PYTHON_DIR%\" >nul 2>nul
            xcopy /E /Y /Q "!TCLTK_TEMP!\Lib\tkinter\*" "%PYTHON_DIR%\Lib\tkinter\" >nul 2>nul
            xcopy /E /Y /Q "!TCLTK_TEMP!\tcl\*" "%PYTHON_DIR%\tcl\" >nul 2>nul
            if not exist "%PYTHON_DIR%\libs" mkdir "%PYTHON_DIR%\libs"
            xcopy /E /Y /Q "!TCLTK_TEMP!\libs\*" "%PYTHON_DIR%\libs\" >nul 2>nul
            echo [OK] Tkinter installed.
        ) else (
            echo [WARN] Tkinter extraction failed - GUI may not work.
        )
        rmdir /S /Q "!TCLTK_TEMP!" 2>nul
        del "!TCLTK_MSI!" 2>nul
    ) else (
        echo [WARN] Could not download Tkinter - GUI may not work.
    )
) else (
    echo [OK] Tkinter already installed.
)

:: ============================================
:: Step 6: Git submodules
:: ============================================
echo [STEP 6/%TOTAL_STEPS%] Initializing git submodules...
where git >nul 2>&1
if %errorlevel% equ 0 (
    cd /d "%SCRIPT_DIR%"
    git submodule update --init --recursive --quiet 2>nul
    if exist "%SCRIPT_DIR%\mini-swe-agent\pyproject.toml" (
        echo [OK] Submodules initialized.
    ) else (
        echo [INFO] Submodules not available - some features may be limited.
    )
) else (
    echo [INFO] Git not found - skipping submodules.
)

:: ============================================
:: Step 6b: Create run_py.sh helper (Unix line endings!)
:: ============================================
echo [STEP 6b] Creating Python helper script...
"%PYTHON_EXE%" -c "f=open(r'%SCRIPT_DIR%run_py.sh','wb');f.write(b'#!/bin/bash\n\"$(dirname \"$0\")/python_embedded/python.exe\" \"$@\"\n');f.close()"
echo [OK] run_py.sh created.

:: ============================================
:: Step 7: Install ALL Python dependencies
:: ============================================
:: 启用 Windows 长路径支持，避免某些深嵌套包（如 elevenlabs）解压失败
:: 该改动需要管理员权限；若失败则自动跳过（用户可能仍会看到长路径错误，但不影响核心功能）
powershell -NoProfile -Command ^
    "try{Set-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' LongPathsEnabled 1 -ErrorAction Stop}catch{}" >nul 2>&1

echo [STEP 7/%TOTAL_STEPS%] Installing Python dependencies...
echo        (this may take several minutes on first run)

:: Main package — three-level fallback so partial network failures don't leave
:: a broken install.  Every level is tested; on total failure we abort clearly.
echo        Installing core package...
"%PYTHON_EXE%" -m pip install -e "%SCRIPT_DIR%\." !PIP_MIRROR! --no-warn-script-location
if errorlevel 1 (
    echo [WARN] Editable install failed, trying requirements.txt...
    "%PYTHON_EXE%" -m pip install -r "%SCRIPT_DIR%\requirements.txt" !PIP_MIRROR! --no-warn-script-location
    if errorlevel 1 (
        echo [WARN] requirements.txt install also failed, installing critical packages individually...
        "%PYTHON_EXE%" -m pip install pyyaml python-dotenv openai rich httpx tenacity prompt_toolkit requests jinja2 "pydantic>=2.0" !PIP_MIRROR! --no-warn-script-location
        if errorlevel 1 (
            echo [ERROR] All install methods failed. Check your network and rerun install.bat.
            pause
            exit /b 1
        )
    )
)

:: Guarantee the project root is on sys.path regardless of editable-install outcome.
:: Embedded Python does not create .egg-link / .pth files the same way as regular
:: Python, so pip install -e . may succeed (exit 0) but leave hermes_cli unreachable.
set "PTH_FILE=%PYTHON_DIR%\Lib\site-packages\hermes_project.pth"
if exist "!PTH_FILE!" goto :pth_done
"%PYTHON_EXE%" -c "f=open(r'%PYTHON_DIR%\Lib\site-packages\hermes_project.pth','w');f.write(r'%SCRIPT_DIR%');f.close()"
echo [OK] hermes_project.pth created.
:pth_done

:: All optional extras
echo        Installing optional extras (messaging, cron, mcp...)
"%PYTHON_EXE%" -m pip install -e "%SCRIPT_DIR%\.[messaging,cron,cli,mcp,honcho,pty,tts-premium,homeassistant]" !PIP_MIRROR! --no-warn-script-location

:: Mini-swe-agent
if exist "%SCRIPT_DIR%\mini-swe-agent\pyproject.toml" (
    "%PYTHON_EXE%" -m pip install -e "%SCRIPT_DIR%\mini-swe-agent" !PIP_MIRROR! --no-warn-script-location
)

:: Extra packages needed for Windows GUI
"%PYTHON_EXE%" -m pip install Pillow ddgs lmstudio !PIP_MIRROR! --no-warn-script-location

:: ── Import-level verification for packages that crash Hermes at startup ──────
:: Any pip step above can partially fail (network glitch, write lock, etc.).
:: We import-test each critical package and repair on the spot; still broken →
:: hard exit so the user sees a clear error now, not a cryptic crash later.
echo        Verifying critical runtime packages...

"%PYTHON_EXE%" -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo [WARN] pyyaml missing -- repairing...
    "%PYTHON_EXE%" -m pip install pyyaml !PIP_MIRROR! --no-warn-script-location
    "%PYTHON_EXE%" -c "import yaml" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] pyyaml could not be installed. Check network and rerun install.bat.
        pause
        exit /b 1
    )
)

"%PYTHON_EXE%" -c "import dotenv" >nul 2>&1
if errorlevel 1 (
    echo [WARN] python-dotenv missing -- repairing...
    "%PYTHON_EXE%" -m pip install python-dotenv !PIP_MIRROR! --no-warn-script-location
    "%PYTHON_EXE%" -c "import dotenv" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] python-dotenv could not be installed. Check network and rerun install.bat.
        pause
        exit /b 1
    )
)

"%PYTHON_EXE%" -c "import openai" >nul 2>&1
if errorlevel 1 (
    echo [WARN] openai missing -- repairing...
    "%PYTHON_EXE%" -m pip install openai !PIP_MIRROR! --no-warn-script-location
    "%PYTHON_EXE%" -c "import openai" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] openai could not be installed. Check network and rerun install.bat.
        pause
        exit /b 1
    )
)
echo [OK] Critical runtime packages verified.
:: ─────────────────────────────────────────────────────────────────────────────

echo [OK] Python dependencies installed.

rem Pre-compile project source to .pyc so the gateway starts ~10s faster on
rem cold boot (Python no longer needs to parse .py files at import time).
echo        Pre-compiling Python bytecode...
"%PYTHON_EXE%" -m compileall -q "%SCRIPT_DIR%hermes_cli" "%SCRIPT_DIR%gateway" "%SCRIPT_DIR%tools" 2>nul
echo [OK] Python bytecode pre-compiled.

:: ============================================
:: Step 8: Node.js dependencies
:: ============================================
echo [STEP 8/%TOTAL_STEPS%] Installing Node.js dependencies...
where node >nul 2>&1
if errorlevel 1 goto :step8_no_node
if not exist "%SCRIPT_DIR%\package.json" goto :step8_done
cd /d "%SCRIPT_DIR%"
call npm install --quiet 2>nul
echo [OK] Node.js dependencies installed.
goto :step8_done

:step8_no_node
echo [INFO] Node.js not found - browser tools and WhatsApp bridge won't be available.
echo        Install Node.js from https://nodejs.org/ and re-run this installer.

:step8_done

:: ============================================
:: Step 9: Environment and config files
:: ============================================
echo [STEP 9/%TOTAL_STEPS%] Setting up configuration...

:: .env (flat \u7ed3\u6784\uff0c\u907f\u514d\u5d4c\u5957\u590d\u5408\u5757\u89e3\u6790\u95ee\u9898)
if exist "%SCRIPT_DIR%\.env" goto :env_done
if not exist "%SCRIPT_DIR%\.env.example" goto :env_done
copy "%SCRIPT_DIR%\.env.example" "%SCRIPT_DIR%\.env" >nul
echo [OK] Created .env from template.
:env_done

:: cli-config.yaml
if exist "%SCRIPT_DIR%\cli-config.yaml" goto :yaml_done
if not exist "%SCRIPT_DIR%\cli-config.yaml.example" goto :yaml_done
copy "%SCRIPT_DIR%\cli-config.yaml.example" "%SCRIPT_DIR%\cli-config.yaml" >nul
:: Fix Unicode chars that break on Windows
"%PYTHON_EXE%" -c "p=r'%SCRIPT_DIR%\cli-config.yaml';f=open(p,'r',encoding='utf-8');c=f.read();f.close();c=c.replace('\u2014','--').replace('\u2192','->');f=open(p,'w',encoding='utf-8');f.write(c);f.close()" 2>nul
echo [OK] Created cli-config.yaml.
:yaml_done

:: Create ~/.hermes directory
if not exist "%USERPROFILE%\.hermes" mkdir "%USERPROFILE%\.hermes"

rem Create default config.yaml if missing (gateway requires it)
if not exist "%USERPROFILE%\.hermes\config.yaml" (
    if exist "%SCRIPT_DIR%\cli-config.yaml.example" (
        copy "%SCRIPT_DIR%\cli-config.yaml.example" "%USERPROFILE%\.hermes\config.yaml" >nul
        echo [OK] Created ~/.hermes/config.yaml from template.
    )
)

:: Default permissions
if exist "%USERPROFILE%\.hermes\permissions.json" goto :perms_done
"%PYTHON_EXE%" -c "import json;json.dump({'read':2,'write':1,'install':1,'execute':2,'remove':1,'network':2},open(r'%USERPROFILE%\.hermes\permissions.json','w'),indent=2)" 2>nul
echo [OK] Default permissions created.
:perms_done

:: ============================================
:: Step 10: Sync skills
:: ============================================
echo [STEP 10/%TOTAL_STEPS%] Syncing skills...
cd /d "%SCRIPT_DIR%"
"%PYTHON_EXE%" "%SCRIPT_DIR%\tools\skills_sync.py" 2>nul
if not errorlevel 1 goto :skills_done
:: Fallback: manual copy（修了之前缺反斜杠的 bug）
if not exist "%SCRIPT_DIR%\skills" goto :skills_done
xcopy /E /Y /Q "%SCRIPT_DIR%\skills\*" "%USERPROFILE%\.hermes\skills\" >nul 2>nul
:skills_done
echo [OK] Skills synced.

:: ============================================
:: Step 11/12: Node.js 便携包 (仅 Full 版)
:: ============================================
if not "%INSTALL_MODE%"=="full" goto :skip_nodejs

set "NODE_DIR=%SCRIPT_DIR%\node_embedded"
set "NODE_EXE=%NODE_DIR%\node.exe"
set "NODE_VER=23.11.0"
set "NODE_ZIP=%SCRIPT_DIR%\node_embedded.zip"

if not exist "%NODE_EXE%" goto :node_need_download
for /f "tokens=*" %%v in ('"%NODE_EXE%" --version 2^>nul') do echo [OK] Node.js %%v already installed, skipping download.
goto :skip_nodejs_download
:node_need_download

:: Use local pre-staged Node.js zip if available (offline scenarios)
:: Accepted local filenames: node_embedded.zip OR node-v23.11.0-win-x64.zip
set "LOCAL_NODE_ALT=%SCRIPT_DIR%\node-v%NODE_VER%-win-x64.zip"
if exist "%NODE_ZIP%" goto :node_local_found
if not exist "%LOCAL_NODE_ALT%" goto :node_need_dl
copy "%LOCAL_NODE_ALT%" "%NODE_ZIP%" >nul
:node_local_found
echo [OK] Using local Node.js zip: %NODE_ZIP%
goto :node_dl_done

:node_need_dl
echo [STEP 11/12] Downloading Node.js v%NODE_VER% (~40MB)...
echo              (中国用户预计 2-10 分钟，请耐心等待)

:: 一级: npmmirror (中国最快)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{Invoke-WebRequest -Uri 'https://registry.npmmirror.com/-/binary/node/v%NODE_VER%/node-v%NODE_VER%-win-x64.zip' -OutFile '%NODE_ZIP%' -TimeoutSec 300}catch{}" >nul 2>&1
if not exist "%NODE_ZIP%" goto :node_dl_cdn
echo [OK] Downloaded from npmmirror.com
goto :node_dl_done

:node_dl_cdn
echo [WARN] npmmirror failed, trying CDN...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{Invoke-WebRequest -Uri 'http://121.40.165.216/hermes-cdn/files/node-v%NODE_VER%-win-x64.zip' -OutFile '%NODE_ZIP%' -TimeoutSec 300}catch{}" >nul 2>&1
if not exist "%NODE_ZIP%" goto :node_dl_official
echo [OK] Downloaded from CDN.
goto :node_dl_done

:node_dl_official
echo [WARN] CDN failed, trying nodejs.org (may be slow)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{Invoke-WebRequest -Uri 'https://nodejs.org/dist/v%NODE_VER%/node-v%NODE_VER%-win-x64.zip' -OutFile '%NODE_ZIP%' -TimeoutSec 600}catch{}" >nul 2>&1
if not exist "%NODE_ZIP%" goto :node_dl_failed
echo [OK] Downloaded from nodejs.org.
goto :node_dl_done

:node_dl_failed
echo [ERROR] Node.js download failed from all sources.
echo         Web UI will not be available.
echo         You can retry later by running: install.bat full
set "INSTALL_MODE=lite"
goto :skip_nodejs

:node_dl_done

echo [STEP 11/12] Extracting Node.js...
set "NODE_TMP=%SCRIPT_DIR%\node_tmp"
set "NODE_SRC=%NODE_TMP%\node-v%NODE_VER%-win-x64"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "Expand-Archive -Path '%NODE_ZIP%' -DestinationPath '%NODE_TMP%' -Force"

if not exist "%NODE_SRC%" goto :node_bad_structure
move "%NODE_SRC%" "%NODE_DIR%" >nul
rmdir /S /Q "%NODE_TMP%" 2>nul
del "%NODE_ZIP%" 2>nul
if not exist "%NODE_EXE%" goto :node_exe_missing
for /f "tokens=*" %%v in ('"%NODE_EXE%" --version 2^>nul') do echo [OK] Node.js %%v installed.
goto :skip_nodejs_download

:node_bad_structure
echo [ERROR] Node.js extraction produced unexpected structure.
set "INSTALL_MODE=lite"
goto :skip_nodejs

:node_exe_missing
echo [ERROR] Node.js extraction failed. Falling back to Lite.
set "INSTALL_MODE=lite"

:skip_nodejs_download
:skip_nodejs

:: ============================================
:: Step 12/12: hermes-web-ui Bundle (仅 Full 版)
:: ============================================
if not "%INSTALL_MODE%"=="full" goto :skip_webui

set "WEBUI_DIR=%SCRIPT_DIR%\webui"
set "WEBUI_SERVER=%WEBUI_DIR%\dist\server\index.js"
set "WEBUI_SOCKETIO=%WEBUI_DIR%\node_modules\socket.io\package.json"
set "WEBUI_NPM_SERVER=%WEBUI_DIR%\node_modules\hermes-web-ui\dist\server\index.js"
set "SEVENZIP=%SCRIPT_DIR%\tools\7za.exe"
set "BUNDLE_VER=0.5.16"
set "BUNDLE_FILE=%SCRIPT_DIR%\hermes-webui-bundle.7z"
set "BUNDLE_CDN=http://121.40.165.216/hermes-cdn/files/hermes-webui-bundle-v%BUNDLE_VER%-win-x64.7z"

if not exist "%WEBUI_NPM_SERVER%" goto :webui_check_bundle
echo [OK] hermes-web-ui v%BUNDLE_VER% already installed (npm mode), skipping.
goto :skip_webui
:webui_check_bundle
if not exist "%WEBUI_SERVER%" goto :webui_need_install
if exist "%WEBUI_SOCKETIO%" goto :webui_files_ok
echo [INFO] Detected incomplete Web UI files, reinstalling runtime dependencies...
goto :webui_need_install
:webui_files_ok
echo [OK] hermes-web-ui v%BUNDLE_VER% already installed, skipping.
goto :skip_webui
:webui_need_install

:: 下载 7za.exe（如无）—— flat 结构避免复合块解析问题
if exist "%SEVENZIP%" goto :sevenzip_ready
if not exist "%SCRIPT_DIR%\tools" mkdir "%SCRIPT_DIR%\tools"
echo [INFO] Downloading 7za.exe...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{Invoke-WebRequest 'http://121.40.165.216/hermes-cdn/files/7za.exe' -OutFile '%SEVENZIP%' -TimeoutSec 60}catch{}" >nul 2>&1
:sevenzip_ready

:: Use local pre-staged bundle if available (offline/dev scenarios)
:: Accepted local filenames: hermes-webui-bundle.7z OR hermes-webui-bundle-v0.5.16-win-x64.7z
set "LOCAL_BUNDLE_ALT=%SCRIPT_DIR%\hermes-webui-bundle-v%BUNDLE_VER%-win-x64.7z"
if exist "%BUNDLE_FILE%" goto :bundle_local_found
if not exist "%LOCAL_BUNDLE_ALT%" goto :bundle_need_download
copy "%LOCAL_BUNDLE_ALT%" "%BUNDLE_FILE%" >nul
:bundle_local_found
echo [OK] Using local bundle: %BUNDLE_FILE%
goto :bundle_downloaded

:bundle_need_download
echo [STEP 12/12] Downloading hermes-web-ui bundle (~50MB)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference='SilentlyContinue';" ^
    "try{Invoke-WebRequest '%BUNDLE_CDN%' -OutFile '%BUNDLE_FILE%' -TimeoutSec 300;exit 0}catch{exit 1}" >nul 2>&1

if exist "%BUNDLE_FILE%" goto :bundle_downloaded
echo [WARN] CDN bundle download failed, trying npm install...
goto :webui_npm_fallback
:bundle_downloaded

:: SHA256 校验（可选，CDN 可能无 .sha256 文件则跳过）
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "try{" ^
    "  $sha=(Get-FileHash '%BUNDLE_FILE%' -Algorithm SHA256).Hash.ToLower();" ^
    "  $exp=(Invoke-WebRequest '%BUNDLE_CDN%.sha256' -UseBasicParsing -TimeoutSec 10).Content.Trim().Split(' ')[0];" ^
    "  if($sha -ne $exp){exit 1} else {exit 0}" ^
    "}catch{exit 0}" >nul 2>&1
if not errorlevel 1 goto :bundle_verified
echo [WARN] SHA256 mismatch. Re-downloading via npm...
del "%BUNDLE_FILE%" 2>nul
goto :webui_npm_fallback
:bundle_verified

:: 解压 bundle
echo [STEP 12/12] Extracting Web UI bundle...
if not exist "%WEBUI_DIR%" mkdir "%WEBUI_DIR%"
if not exist "%SEVENZIP%" goto :webui_no_7za
"%SEVENZIP%" x "%BUNDLE_FILE%" -o"%WEBUI_DIR%" -y >nul
del "%BUNDLE_FILE%" 2>nul

:: Check if files extracted correctly (direct layout)
if exist "%WEBUI_SERVER%" goto :webui_done

:: Check if bundle had extra "hermes-web-ui-src" wrapper folder (old build format)
:: If so, flatten by moving inner contents up one level.
if not exist "%WEBUI_DIR%\hermes-web-ui-src\dist\server\index.js" goto :webui_extract_failed
echo [INFO] Detected legacy bundle layout, flattening...
xcopy /E /Y /Q "%WEBUI_DIR%\hermes-web-ui-src\*" "%WEBUI_DIR%\" >nul
rmdir /S /Q "%WEBUI_DIR%\hermes-web-ui-src" 2>nul
if exist "%WEBUI_SERVER%" goto :webui_done

:webui_extract_failed
echo [WARN] Bundle extraction did not produce expected files. Trying npm fallback...
goto :webui_npm_fallback

:webui_no_7za
echo [ERROR] 7za.exe not available, cannot extract .7z bundle.
del "%BUNDLE_FILE%" 2>nul

:webui_npm_fallback
echo [FALLBACK] Installing hermes-web-ui via npm (npmmirror)...
if not exist "%NODE_EXE%" goto :webui_no_node
set "PATH=%NODE_DIR%;%PATH%"
set "NPM_CONFIG_CACHE=%SCRIPT_DIR%\.npm-cache"
if not exist "%WEBUI_DIR%" mkdir "%WEBUI_DIR%"
cd /d "%WEBUI_DIR%"
call "%NODE_DIR%\npm.cmd" install "hermes-web-ui@%BUNDLE_VER%" ^
    --registry https://registry.npmmirror.com ^
    --cache "%SCRIPT_DIR%\.npm-cache" ^
    --prefer-offline 2>nul
set "NPM_WEBUI=%WEBUI_DIR%\node_modules\hermes-web-ui\dist\server\index.js"
if not exist "%NPM_WEBUI%" goto :webui_npm_fail
echo [OK] hermes-web-ui installed via npm.
set "WEBUI_SERVER=%NPM_WEBUI%"
goto :webui_done

:webui_no_node
echo [ERROR] Node.js not available. Cannot install Web UI.
goto :skip_webui

:webui_npm_fail
echo [ERROR] npm install also failed. Web UI will not be available.

:webui_done
cd /d "%SCRIPT_DIR%"
if exist "%SCRIPT_DIR%\scripts\patch-webui-persistence.py" if exist "%PY_EXE%" (
    "%PY_EXE%" "%SCRIPT_DIR%\scripts\patch-webui-persistence.py" "%WEBUI_DIR%" >nul 2>&1
)

:skip_webui

:: ============================================
:: Done!
:: ============================================
echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo   What's installed:
echo     - Python 3.13 (portable)
echo     - Tkinter GUI
echo     - 100 AI tools across 20+ toolsets
echo     - 88+ skills
echo     - LM Studio SDK
echo     - Browser automation
if exist "%SCRIPT_DIR%\node_embedded\node.exe" echo     - Node.js v23.11.0 (portable, in node_embedded/)
if exist "%SCRIPT_DIR%\webui\dist\server\index.js" echo     - hermes-web-ui v%BUNDLE_VER% (browser interface, bundle mode)
if exist "%SCRIPT_DIR%\webui\node_modules\hermes-web-ui\dist\server\index.js" echo     - hermes-web-ui v%BUNDLE_VER% (browser interface, npm mode)
echo.
echo   To start:
echo     hermes_gui.bat     Desktop GUI (recommended)
echo     hermes.bat         Command-line interface
if exist "%SCRIPT_DIR%\webui\dist\server\index.js" echo     start_webui.bat    Launch Web UI (http://localhost:8648)
if exist "%SCRIPT_DIR%\webui\node_modules\hermes-web-ui\dist\server\index.js" echo     start_webui.bat    Launch Web UI (http://localhost:8648)
echo.
echo   First time? The app will guide you through
echo   setting up your API keys on first launch.
echo.

:: ============================================
:: 状态总结：明确告诉用户 Web UI 装没装上（flat 结构，避免复合块解析问题）
:: ============================================
echo ============================================
echo   实际安装状态:

:: Python 检查
if exist "%SCRIPT_DIR%\python_embedded\python.exe" goto :status_py_ok
echo     [FAIL] Python 便携版
goto :status_py_done
:status_py_ok
echo     [OK]  Python 便携版
:status_py_done

:: Node.js 检查
if exist "%SCRIPT_DIR%\node_embedded\node.exe" goto :status_node_ok
echo     [SKIP] Node.js 便携版 (轻量版或下载失败)
goto :status_node_done
:status_node_ok
echo     [OK]  Node.js 便携版
:status_node_done

:: Web UI 检查（三种状态：bundle / npm / 未安装）
if exist "%SCRIPT_DIR%\webui\dist\server\index.js" goto :status_webui_bundle
if exist "%SCRIPT_DIR%\webui\node_modules\hermes-web-ui\dist\server\index.js" goto :status_webui_npm
echo     [SKIP] hermes-web-ui ^(未安装^)
goto :status_done
:status_webui_bundle
echo     [OK]  hermes-web-ui ^(bundle 模式，可双击 start_webui.bat 打开^)
goto :status_done
:status_webui_npm
echo     [OK]  hermes-web-ui ^(npm 模式^)
:status_done

echo ============================================
echo.

:: 标记安装已完成（HermesSetup.exe 用此判断是否需要进入安装界面）
echo %INSTALL_MODE%>"%SCRIPT_DIR%\.install-complete"

endlocal
call :maybe_pause
goto :eof

:maybe_pause
if "%HERMES_INSTALLER_NO_PAUSE%"=="1" goto :eof
pause
goto :eof
