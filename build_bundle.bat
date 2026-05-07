@echo off
:: ============================================================
:: build_bundle.bat
:: 在 Windows 构建机上预构建 hermes-web-ui 并打包为 .7z
:: 运行环境: Windows + Node.js v23.x + 7-Zip
::
:: 用法:
::   build_bundle.bat              # 构建并打包
::   build_bundle.bat --upload     # 构建、打包并上传到 CDN
::
:: 输出: hermes-webui-bundle-v<VER>-win-x64.7z
:: ============================================================
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

set "BUNDLE_VER=0.5.13"
set "WEBUI_REPO=https://github.com/EKKOLearnAI/hermes-web-ui.git"
set "SRC_DIR=%~dp0_build\hermes-web-ui-src"
set "BUNDLE_NAME=hermes-webui-bundle-v%BUNDLE_VER%-win-x64.7z"
set "OUT_FILE=%~dp0%BUNDLE_NAME%"
set "CDN_URL=http://121.40.165.216/hermes-cdn/files/"

echo.
echo ============================================================
echo   hermes-web-ui Bundle Builder
echo   Version: %BUNDLE_VER%
echo ============================================================
echo.

:: ── 检查 Node.js ────────────────────────────────────────────
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found on PATH.
    echo         Install Node.js v23.x from https://nodejs.org/
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>nul') do set "NODE_VER=%%v"
echo [OK] Node.js %NODE_VER%

for /f "tokens=1 delims=." %%m in ("%NODE_VER:~1%") do set "NODE_MAJOR=%%m"
if %NODE_MAJOR% LSS 23 (
    echo [ERROR] Need Node.js v23+, found %NODE_VER%
    exit /b 1
)

:: ── 检查 7-Zip ──────────────────────────────────────────────
where 7z >nul 2>&1
if errorlevel 1 (
    where 7za >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] 7-Zip not found. Install from https://www.7-zip.org/
        exit /b 1
    ) else (
        set "SEVENZIP=7za"
    )
) else (
    set "SEVENZIP=7z"
)
echo [OK] 7-Zip found (%SEVENZIP%)

:: ── 克隆/更新源码 ───────────────────────────────────────────
if not exist "%~dp0_build" mkdir "%~dp0_build"

if exist "%SRC_DIR%\.git" (
    echo [STEP 1/5] Updating hermes-web-ui source...
    cd /d "%SRC_DIR%"
    git fetch --tags --quiet
    git checkout "v%BUNDLE_VER%" --quiet 2>nul
    if errorlevel 1 git checkout main --quiet
) else (
    echo [STEP 1/5] Cloning hermes-web-ui v%BUNDLE_VER%...
    git clone "%WEBUI_REPO%" "%SRC_DIR%" --quiet
    cd /d "%SRC_DIR%"
    git checkout "v%BUNDLE_VER%" --quiet 2>nul
)
echo [OK] Source ready at %SRC_DIR%

:: ── npm install (含 devDependencies，用于构建) ──────────────
echo [STEP 2/5] Installing all dependencies (including devDeps)...
cd /d "%SRC_DIR%"
npm install --registry https://registry.npmmirror.com 2>nul
if errorlevel 1 (
    echo [WARN] npmmirror failed, trying npmjs.com...
    npm install 2>nul
    if errorlevel 1 (
        echo [ERROR] npm install failed.
        exit /b 1
    )
)
echo [OK] Dependencies installed.

:: ── 构建前端+后端 ───────────────────────────────────────────
echo [STEP 3/5] Building (vue-tsc + vite + esbuild)...
npm run build 2>nul
if errorlevel 1 (
    echo [ERROR] Build failed. Check output above.
    exit /b 1
)
if not exist "%SRC_DIR%\dist\server\index.js" (
    echo [ERROR] Build succeeded but dist\server\index.js not found.
    exit /b 1
)
echo [OK] Build complete.

:: ── 删除 devDependencies ────────────────────────────────────
echo [STEP 4/5] Pruning devDependencies...
npm prune --production 2>nul
echo [OK] Pruned to production dependencies only.

:: ── 打包 ────────────────────────────────────────────────────
echo [STEP 5/5] Creating bundle: %BUNDLE_NAME%
if exist "%OUT_FILE%" del "%OUT_FILE%"

cd /d "%SRC_DIR%"
%SEVENZIP% a -t7z -mx=9 -mmt=on "%OUT_FILE%" ^
    dist ^
    node_modules ^
    bin ^
    package.json >nul

if not exist "%OUT_FILE%" (
    echo [ERROR] Bundle creation failed.
    exit /b 1
)

:: SHA256 校验文件
powershell -NoProfile -Command ^
    "(Get-FileHash '%OUT_FILE%' -Algorithm SHA256).Hash.ToLower() + '  %BUNDLE_NAME%'" ^
    "| Set-Content '%OUT_FILE%.sha256' -Encoding ASCII" >nul 2>&1

for %%F in ("%OUT_FILE%") do set "BUNDLE_SIZE=%%~zF"
set /a BUNDLE_MB=%BUNDLE_SIZE% / 1048576
echo [OK] Bundle created: %BUNDLE_NAME% (%BUNDLE_MB% MB)
echo      SHA256 written: %BUNDLE_NAME%.sha256

:: ── 可选：上传到 CDN ─────────────────────────────────────────
if not "%~1"=="--upload" goto :done

echo.
echo [UPLOAD] Uploading to CDN %CDN_URL%...
echo          Make sure CDN SSH key is configured.
echo.

:: 使用 curl 上传（如 CDN 支持 HTTP PUT）
curl -s -T "%OUT_FILE%" "%CDN_URL%%BUNDLE_NAME%" 2>nul
if errorlevel 1 (
    echo [WARN] curl upload failed. Upload manually via SCP:
    echo        scp "%OUT_FILE%" deploy@121.40.165.216:/var/www/hermes-cdn/files/
) else (
    curl -s -T "%OUT_FILE%.sha256" "%CDN_URL%%BUNDLE_NAME%.sha256" >nul 2>&1
    echo [OK] Uploaded to CDN.
)

:done
echo.
echo ============================================================
echo   Done!
echo   Bundle: %~dp0%BUNDLE_NAME%
echo.
echo   Next steps:
echo   1. Upload to CDN:
echo      scp %BUNDLE_NAME% deploy@121.40.165.216:/var/www/hermes-cdn/files/
echo   2. Also upload node-v23.11.0-win-x64.zip and 7za.exe if not already there
echo   3. Update version.json on CDN
echo ============================================================
echo.
endlocal
