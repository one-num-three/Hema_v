param(
    [string]$Version = "v1.0-hema.local-20260530-offline"
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ReleaseDir = Join-Path $Root "release"
$ZipPath = Join-Path $ReleaseDir ("Hema_v-{0}-full-local.zip" -f $Version)
$ListPath = Join-Path $ReleaseDir ("package-list-{0}.txt" -f $Version)
$LogPath = Join-Path $ReleaseDir ("build-{0}.log" -f $Version)
$SevenZip = Join-Path $Root "tools\7za.exe"

if (-not (Test-Path -LiteralPath $ReleaseDir)) {
    New-Item -ItemType Directory -Path $ReleaseDir | Out-Null
}

if (-not (Test-Path -LiteralPath $SevenZip)) {
    throw "7za.exe not found: $SevenZip"
}

foreach ($path in @($ZipPath, "$ZipPath.sha256", $ListPath, $LogPath)) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force
    }
}

# Keep the full local package generous: embedded runtimes may legitimately
# contain .zip/.7z-like files such as python_embedded\python313.zip.
$ExcludeDirs = @(
    ".git",
    ".claude",
    "release",
    "logs",
    "data",
    ".pytest_cache",
    "tmp",
    "temp_vision_images",
    "__pycache__",
    ".mypy_cache",
    ".venv",
    "venv",
    ".npm-cache",
    "node_tmp",
    "_tcltk_temp",
    ".direnv",
    "result",
    "wandb",
    "testlogs",
    ".worktrees"
)

$ExcludeFiles = @(
    "2.0",
    ".env",
    ".env.local",
    ".env.development.local",
    ".env.test.local",
    ".env.production.local",
    ".env.development",
    ".env.test",
    "cli-config.yaml",
    ".install-complete",
    ".release_notes.md",
    "task_556_output.txt",
    "test_ilink_output.txt",
    "test_ilink_run_log.txt"
)

$ExcludeExts = @(".pyc", ".pyo")
$PrefixLen = $Root.TrimEnd("\").Length + 1
$RelativeFiles = New-Object System.Collections.Generic.List[string]

Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
    $Rel = $_.FullName.Substring($PrefixLen)
    $Parts = $Rel -split "[\\/]"

    foreach ($Part in $Parts) {
        if ($ExcludeDirs -contains $Part) {
            return
        }
    }

    if ($ExcludeFiles -contains $Rel -or $ExcludeFiles -contains $_.Name) {
        return
    }

    if ($ExcludeExts -contains $_.Extension.ToLowerInvariant()) {
        return
    }

    $RelativeFiles.Add($Rel)
}

$RelativeFiles | Sort-Object | Set-Content -LiteralPath $ListPath -Encoding UTF8

$RequiredFiles = @(
    "python_embedded\python.exe",
    "python_embedded\python313.zip",
    "python_embedded\Scripts\pip.exe",
    "node_embedded\node.exe",
    "webui\node_modules\hermes-web-ui\dist\server\index.js",
    "webui\node_modules\hermes-web-ui\dist\client\assets\js\index-cxxPdNAz.js",
    "start_webui.bat",
    "installer_gui.ps1",
    "assets\installer\hippo-installer.ico",
    "scripts\patch-webui-persistence.py",
    "skills\productivity\ppt-master\SKILL.md",
    "skills\productivity\ppt-master\requirements.txt",
    "skills\productivity\minimax-pdf\SKILL.md",
    "skills\productivity\minimax-pdf\scripts\render_body.py",
    "skills\productivity\minimax-xlsx\SKILL.md",
    "skills\productivity\minimax-xlsx\scripts\xlsx_reader.py",
    "skills\productivity\minimax-docx\SKILL.md",
    "skills\productivity\minimax-docx\scripts\dotnet\MiniMaxAIDocx.Core\Commands\CreateCommand.cs",
    "skills\research\nature-citation\SKILL.md",
    "skills\research\nature-data\SKILL.md",
    "skills\research\nature-figure\SKILL.md",
    "skills\research\nature-paper2ppt\SKILL.md",
    "skills\research\nature-polishing\SKILL.md",
    "skills\research\nature-reader\SKILL.md",
    "skills\research\nature-response\SKILL.md"
)

$Missing = @($RequiredFiles | Where-Object { $RelativeFiles -notcontains $_ })
if ($Missing.Count -gt 0) {
    throw "Package is missing required files: $($Missing -join ', ')"
}

Push-Location $Root
try {
    & $SevenZip a -tzip -mx=9 -scsUTF-8 $ZipPath ("@$ListPath") > $LogPath 2>&1
    if ($LASTEXITCODE -ne 0) {
        Get-Content -LiteralPath $LogPath -Tail 80
        throw "7-Zip failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

$Hash = Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256
("{0}  {1}" -f $Hash.Hash.ToLowerInvariant(), (Split-Path -Leaf $ZipPath)) |
    Set-Content -LiteralPath "$ZipPath.sha256" -Encoding ASCII

$SizeMb = [Math]::Round((Get-Item -LiteralPath $ZipPath).Length / 1MB, 2)
Write-Host "Built $ZipPath ($SizeMb MB)"
Write-Host "Files $($RelativeFiles.Count)"
Write-Host "SHA256 $($Hash.Hash.ToLowerInvariant())"
