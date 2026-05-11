$ErrorActionPreference = 'Continue'

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
$UserProfile = [Environment]::GetFolderPath('UserProfile')
$Desktop = [Environment]::GetFolderPath('DesktopDirectory')

$Quiet = $false
$DryRun = $false
$PurgeUserData = $false
$ShowHelp = $false

foreach ($arg in $args) {
    switch -Regex ($arg) {
        '^(?i)(/quiet|-quiet)$' { $Quiet = $true; continue }
        '^(?i)(/dry-run|-dry-run)$' { $DryRun = $true; continue }
        '^(?i)(/purge-user-data|-purge-user-data)$' { $PurgeUserData = $true; continue }
        '^(?i)(/\?|-h|--help|/help|-help)$' { $ShowHelp = $true; continue }
    }
}

function Write-Step([string]$Text) {
    Write-Host ''
    Write-Host $Text
}

function Test-ProcessBelongsToRoot($Process) {
    if (-not $Process) { return $false }
    $cmd = [string]$Process.CommandLine
    $exe = [string]$Process.ExecutablePath
    return (($cmd -and $cmd.Contains($Root)) -or ($exe -and $exe.StartsWith($Root, [StringComparison]::OrdinalIgnoreCase)))
}

function Stop-PidIfOwned([int]$PidValue, [string]$Label) {
    if ($DryRun) {
        Write-Host "[DRY] Would stop $Label PID $PidValue if it belongs to this install."
        return 'dry'
    }

    try {
        $proc = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $PidValue) -ErrorAction Stop
    } catch {
        Write-Host "[INFO] $Label PID $PidValue is not running."
        return 'stale'
    }

    if (-not (Test-ProcessBelongsToRoot $proc)) {
        Write-Host "[INFO] $Label PID $PidValue does not belong to this install."
        return 'foreign'
    }

    try {
        Stop-Process -Id $PidValue -Force -ErrorAction Stop
        Write-Host "[OK] Stopped $Label PID $PidValue."
        return 'stopped'
    } catch {
        Write-Host "[WARN] Failed to stop $Label PID ${PidValue}: $($_.Exception.Message)"
        return 'failed'
    }
}

function Stop-PidFile([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "[INFO] $Label PID file not found."
        return
    }

    $raw = (Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue).Trim()
    $pidValue = 0
    if (-not [int]::TryParse($raw, [ref]$pidValue)) {
        Write-Host "[INFO] $Label PID file is invalid."
        if (-not $DryRun) { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue }
        return
    }

    $result = Stop-PidIfOwned -PidValue $pidValue -Label $Label
    if ($result -in @('stopped', 'stale')) {
        Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    } elseif ($result -eq 'foreign') {
        Write-Host "[INFO] Keeping PID file because it points to another install."
    }
}

function Stop-ProcessesByName([string]$Name, [string]$Label) {
    if ($DryRun) {
        Write-Host "[DRY] Would stop $Name processes under $Root."
        return
    }

    $items = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ieq $Name -and (Test-ProcessBelongsToRoot $_) }

    $count = 0
    foreach ($proc in $items) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
            $count++
        } catch {}
    }

    if ($count -gt 0) {
        Write-Host "[OK] Stopped $count $Label process(es)."
    } else {
        Write-Host "[INFO] No $Label process found under this install."
    }
}

function Stop-PortIfOwned([int]$Port, [string]$Label) {
    $pids = @()
    try {
        $pids = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop |
            Select-Object -ExpandProperty OwningProcess -Unique
    } catch {
        $rows = netstat -aon 2>$null | Select-String ":$Port\s+.*LISTENING\s+(\d+)"
        foreach ($row in $rows) {
            if ($row.Matches.Count -gt 0) { $pids += [int]$row.Matches[0].Groups[1].Value }
        }
        $pids = $pids | Select-Object -Unique
    }

    foreach ($pidValue in $pids) {
        Stop-PidIfOwned -PidValue ([int]$pidValue) -Label "$Label port $Port" | Out-Null
    }
}

function Remove-DirSafe([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) {
        Write-Host "[INFO] $Label not found."
        return
    }

    if ($DryRun) {
        Write-Host "[DRY] Would remove ${Label}: $Path"
        return
    }

    Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $Path) {
        Write-Host "[WARN] Failed to remove ${Label}: $Path"
    } else {
        Write-Host "[OK] Removed $Label."
    }
}

function Remove-FileSafe([string]$Path, [string]$Label) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    if ($DryRun) {
        Write-Host "[DRY] Would remove ${Label}: $Path"
        return
    }

    Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $Path) {
        Write-Host "[WARN] Failed to remove ${Label}: $Path"
    } else {
        Write-Host "[OK] Removed $Label."
    }
}

function Remove-ShortcutByName([string]$Name) {
    $path = Join-Path $Desktop ($Name + '.lnk')
    if (-not (Test-Path -LiteralPath $path)) { return }
    if ($DryRun) {
        Write-Host "[DRY] Would remove desktop shortcut: $Name"
        return
    }
    Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Removed desktop shortcut: $Name"
}

function Remove-ShortcutsByRoot {
    if ($DryRun) {
        Write-Host "[DRY] Would remove desktop shortcuts pointing to $Root."
        return
    }

    try {
        $shell = New-Object -ComObject WScript.Shell
    } catch {
        Write-Host "[WARN] Cannot inspect desktop shortcuts: $($_.Exception.Message)"
        return
    }

    $count = 0
    Get-ChildItem -LiteralPath $Desktop -Filter '*.lnk' -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $shortcut = $shell.CreateShortcut($_.FullName)
            $haystack = ([string]$shortcut.TargetPath) + ' ' + ([string]$shortcut.Arguments) + ' ' + ([string]$shortcut.WorkingDirectory)
            if ($haystack.Contains($Root)) {
                Remove-Item -LiteralPath $_.FullName -Force -ErrorAction Stop
                $count++
            }
        } catch {}
    }
    if ($count -gt 0) {
        Write-Host "[OK] Removed $count desktop shortcut(s) pointing to this install."
    }
}

function Check-Path([string]$Path) {
    if (Test-Path -LiteralPath $Path) {
        Write-Host "[WARN] Still exists: $Path"
    } else {
        Write-Host "[OK] Cleaned: $Path"
    }
}

if ($ShowHelp) {
    Write-Host 'Usage: uninstall.bat [/quiet] [/dry-run] [/purge-user-data]'
    Write-Host ''
    Write-Host '  /quiet            Do not ask for the initial confirmation.'
    Write-Host '  /dry-run          Print what would be removed without changing anything.'
    Write-Host '  /purge-user-data  Also remove %USERPROFILE%\.hermes and %USERPROFILE%\.hermes-web-ui.'
    exit 0
}

Write-Host ''
Write-Host '============================================================'
Write-Host '  Hema Uninstaller'
Write-Host '============================================================'
Write-Host ''
Write-Host '  Install directory:'
Write-Host "  $Root"
Write-Host ''
Write-Host '  This removes local runtimes, caches, install markers, and desktop shortcuts.'
Write-Host '  User data is kept by default.'
if ($DryRun) {
    Write-Host ''
    Write-Host '  DRY RUN: no files or processes will be changed.'
}
Write-Host ''

if (-not $Quiet) {
    $confirm = Read-Host 'Continue uninstalling this Hema directory? [y/N]'
    if ($confirm -notin @('y', 'Y')) {
        Write-Host '[INFO] Uninstall cancelled.'
        exit 0
    }
}

Write-Step '[1/6] Stopping processes owned by this install...'
Stop-PidFile -Path (Join-Path $UserProfile '.hermes-web-ui\server.pid') -Label 'Web UI'
Stop-PidFile -Path (Join-Path $UserProfile '.hermes\gateway.pid') -Label 'Gateway'
Stop-ProcessesByName -Name 'node.exe' -Label 'Web UI / Node.js'
Stop-ProcessesByName -Name 'python.exe' -Label 'Hermes Gateway / Python'
Stop-ProcessesByName -Name 'pythonw.exe' -Label 'Hermes GUI / Python'
Stop-PortIfOwned -Port 8648 -Label 'Web UI'
Stop-PortIfOwned -Port 8642 -Label 'Gateway'

Write-Step '[2/6] Removing desktop shortcuts...'
foreach ($name in @('Hema Gateway', 'Hema Web UI', 'Hermes Gateway', 'Hermes Web UI', '河马网关', '河马 Web 管理界面')) {
    Remove-ShortcutByName -Name $name
}
Remove-ShortcutsByRoot

Write-Step '[3/6] Removing bundled runtimes...'
Remove-DirSafe -Path (Join-Path $Root 'node_embedded') -Label 'Node.js runtime'
Remove-DirSafe -Path (Join-Path $Root 'webui') -Label 'Web UI runtime'
Remove-DirSafe -Path (Join-Path $Root 'python_embedded') -Label 'Python runtime'

Write-Step '[4/6] Removing caches and install artifacts...'
Remove-DirSafe -Path (Join-Path $Root '.npm-cache') -Label 'npm cache'
Remove-DirSafe -Path (Join-Path $Root 'node_tmp') -Label 'Node temp directory'
Remove-DirSafe -Path (Join-Path $Root '_tcltk_temp') -Label 'Python Tcl/Tk temp directory'
Remove-DirSafe -Path (Join-Path $Root '__pycache__') -Label 'Python bytecode cache'
Remove-FileSafe -Path (Join-Path $Root 'python_embedded.zip') -Label 'Python download archive'
Remove-FileSafe -Path (Join-Path $Root 'node_embedded.zip') -Label 'Node.js download archive'
Remove-FileSafe -Path (Join-Path $Root 'node-v23.11.0-win-x64.zip') -Label 'Node.js download archive'
Remove-FileSafe -Path (Join-Path $Root 'hermes-webui-bundle.7z') -Label 'Web UI bundle archive'
Remove-FileSafe -Path (Join-Path $Root 'hermes-webui-bundle-v0.5.16-win-x64.7z') -Label 'Web UI bundle archive'
Remove-FileSafe -Path (Join-Path $Root '.install-complete') -Label 'install completion marker'
Remove-FileSafe -Path (Join-Path $Root 'gateway_fg_test.err.log') -Label 'test log'
Remove-FileSafe -Path (Join-Path $Root 'gateway_fg_test.out.log') -Label 'test log'

Write-Step '[5/6] User data...'
if (-not $PurgeUserData) {
    Write-Host '[INFO] Keeping user data:'
    Write-Host "       $(Join-Path $UserProfile '.hermes')"
    Write-Host "       $(Join-Path $UserProfile '.hermes-web-ui')"

    if (-not $Quiet) {
        $deleteUserData = Read-Host 'Also delete user data? This cannot be undone [y/N]'
        if ($deleteUserData -in @('y', 'Y')) {
            $confirmDelete = Read-Host 'Type DELETE to confirm user data deletion'
            if ($confirmDelete -eq 'DELETE') {
                $PurgeUserData = $true
            }
        }
    }
}

if ($PurgeUserData) {
    Remove-DirSafe -Path (Join-Path $UserProfile '.hermes') -Label 'Hermes user data'
    Remove-DirSafe -Path (Join-Path $UserProfile '.hermes-web-ui') -Label 'Web UI user data'
}

Write-Step '[6/6] Result check...'
Check-Path -Path (Join-Path $Root 'node_embedded')
Check-Path -Path (Join-Path $Root 'webui')
Check-Path -Path (Join-Path $Root 'python_embedded')
Check-Path -Path (Join-Path $Root '.npm-cache')

Write-Host ''
Write-Host '============================================================'
Write-Host '  Uninstall finished'
Write-Host '============================================================'
Write-Host ''
Write-Host '  To remove source files and scripts too, delete:'
Write-Host "  $Root"
Write-Host ''
exit 0
