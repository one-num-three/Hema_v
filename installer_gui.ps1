[CmdletBinding()]
param()

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

[System.Windows.Forms.Application]::EnableVisualStyles()

$script:SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:BrandImagePath = Join-Path $script:SourceDir 'assets\installer\hippo-installer.jpg'
$script:BrandIconPath = Join-Path $script:SourceDir 'assets\installer\hippo-installer.ico'
$script:IsInstalling = $false
$script:LastInstallPath = $null

function Resolve-NormalizedPath {
    param([string]$Path)
    [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
}

function Z {
    param([string]$Base64)
    [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Base64))
}

function Convert-BrandImageToIcon {
    param(
        [string]$ImagePath,
        [string]$IconPath
    )

    if (-not (Test-Path -LiteralPath $ImagePath)) {
        return $null
    }

    try {
        $bitmap = New-Object System.Drawing.Bitmap $ImagePath
        $icon = [System.Drawing.Icon]::FromHandle($bitmap.GetHicon())
        $stream = [System.IO.File]::Open($IconPath, [System.IO.FileMode]::Create)
        $icon.Save($stream)
        $stream.Close()
        $clonedIcon = New-Object System.Drawing.Icon $IconPath
        $icon.Dispose()
        $bitmap.Dispose()
        return $clonedIcon
    } catch {
        return $null
    }
}

function New-DesktopShortcut {
    param(
        [string]$Name,
        [string]$TargetPath,
        [string]$WorkingDirectory,
        [string]$IconLocation,
        [string]$Arguments = ''
    )

    $desktop = [Environment]::GetFolderPath('DesktopDirectory')
    $shortcutPath = Join-Path $desktop ($Name + '.lnk')
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath -Force
    }
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $WorkingDirectory
    if ($Arguments) {
        $shortcut.Arguments = $Arguments
    }
    if ($IconLocation -and (Test-Path -LiteralPath $IconLocation)) {
        $shortcut.IconLocation = ($IconLocation + ',0')
    }
    $shortcut.Save()
}

function Remove-DesktopShortcut {
    param([string]$Name)

    $shortcutPath = Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) ($Name + '.lnk')
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath -Force
    }
}

function Refresh-ShellIconCache {
    $ie4uinit = Join-Path $env:SystemRoot 'System32\ie4uinit.exe'
    if (Test-Path -LiteralPath $ie4uinit) {
        Start-Process -FilePath $ie4uinit -ArgumentList '-show' -WindowStyle Hidden -ErrorAction SilentlyContinue
    }
}

function Update-InstallModeUi {
    if ($comboMode.SelectedIndex -eq 0) {
        $checkWebUiShortcut.Checked = $true
        $checkWebUiShortcut.Enabled = $true
        $labelModeHint.Text = Z('5a6M5pW05a6J6KOF77ya6Ieq5Yqo6YWN572uIFB5dGhvbuOAgU5vZGUuanMg5ZKMIFdlYiDnrqHnkIbnlYzpnaI=')
    } else {
        $checkWebUiShortcut.Checked = $false
        $checkWebUiShortcut.Enabled = $false
        $labelModeHint.Text = Z('6L276YeP5a6J6KOF77ya5LuF5a6J6KOFIFB5dGhvbiDkuI7moYzpnaLnrqHnkIblt6Xlhbc=')
    }
}

$accent = [System.Drawing.Color]::FromArgb(26, 133, 110)
$accentSoft = [System.Drawing.Color]::FromArgb(232, 247, 243)
$textPrimary = [System.Drawing.Color]::FromArgb(30, 41, 59)
$textMuted = [System.Drawing.Color]::FromArgb(92, 108, 128)
$surface = [System.Drawing.Color]::White
$surfaceMuted = [System.Drawing.Color]::FromArgb(245, 247, 250)
$logBg = [System.Drawing.Color]::FromArgb(17, 24, 39)
$logFg = [System.Drawing.Color]::FromArgb(226, 232, 240)

$fontTitle = New-Object System.Drawing.Font('Microsoft YaHei UI', 18, [System.Drawing.FontStyle]::Bold)
$fontSubtitle = New-Object System.Drawing.Font('Microsoft YaHei UI', 9.75)
$fontBody = New-Object System.Drawing.Font('Microsoft YaHei UI', 10)
$fontSmall = New-Object System.Drawing.Font('Microsoft YaHei UI', 9)
$fontMono = New-Object System.Drawing.Font('Consolas', 9.5)

$form = New-Object System.Windows.Forms.Form
$form.Text = Z('SGVtYSDlronoo4Xlmag=')
$form.StartPosition = 'CenterScreen'
$form.Size = New-Object System.Drawing.Size(1060, 860)
$form.MinimumSize = New-Object System.Drawing.Size(980, 820)
$form.BackColor = $surfaceMuted
$form.FormBorderStyle = 'Sizable'
$form.MaximizeBox = $true
$form.AutoScaleMode = 'Dpi'
$form.AutoScroll = $true

$tempIconPath = Join-Path $env:TEMP 'hema-installer-icon.ico'
if (Test-Path -LiteralPath $script:BrandIconPath) {
    Copy-Item -LiteralPath $script:BrandIconPath -Destination $tempIconPath -Force
    $formIcon = New-Object System.Drawing.Icon $tempIconPath
} else {
    $formIcon = Convert-BrandImageToIcon -ImagePath $script:BrandImagePath -IconPath $tempIconPath
}
if ($formIcon) {
    $form.Icon = $formIcon
}

$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Location = New-Object System.Drawing.Point(18, 18)
$headerPanel.Size = New-Object System.Drawing.Size(928, 170)
$headerPanel.BackColor = $surface
$headerPanel.Anchor = 'Top, Left, Right'
$form.Controls.Add($headerPanel)

$brandPanel = New-Object System.Windows.Forms.Panel
$brandPanel.Location = New-Object System.Drawing.Point(0, 0)
$brandPanel.Size = New-Object System.Drawing.Size(928, 170)
$brandPanel.BackColor = $accentSoft
$brandPanel.Anchor = 'Top, Left, Right'
$headerPanel.Controls.Add($brandPanel)

$picture = New-Object System.Windows.Forms.PictureBox
$picture.Location = New-Object System.Drawing.Point(22, 17)
$picture.Size = New-Object System.Drawing.Size(136, 136)
$picture.BackColor = $surface
$picture.SizeMode = 'Zoom'
if (Test-Path -LiteralPath $script:BrandImagePath) {
    $picture.Image = [System.Drawing.Image]::FromFile($script:BrandImagePath)
}
$brandPanel.Controls.Add($picture)

$labelTitle = New-Object System.Windows.Forms.Label
$labelTitle.Location = New-Object System.Drawing.Point(182, 28)
$labelTitle.Size = New-Object System.Drawing.Size(620, 34)
$labelTitle.Text = Z('SGVtYSDlm77lvaLljJblronoo4Xlmag=')
$labelTitle.Font = $fontTitle
$labelTitle.ForeColor = $textPrimary
$brandPanel.Controls.Add($labelTitle)

$labelSubtitle = New-Object System.Windows.Forms.Label
$labelSubtitle.Location = New-Object System.Drawing.Point(184, 68)
$labelSubtitle.Size = New-Object System.Drawing.Size(700, 45)
$labelSubtitle.Text = Z('6Z2i5ZCR5pmu6YCa55So5oi355qE546w5LujIFdpbmRvd3Mg5a6J6KOF55WM6Z2i44CC5pSv5oyB6YCJ5oup5a6J6KOF55uu5b2V44CB5p+l55yL5a6e5pe25pel5b+X77yM5bm25Y+v5LiA6ZSu5Yib5bu65qGM6Z2i5b+r5o235pa55byP44CC')
$labelSubtitle.Font = $fontSubtitle
$labelSubtitle.ForeColor = $textMuted
$brandPanel.Controls.Add($labelSubtitle)

$labelHighlights = New-Object System.Windows.Forms.Label
$labelHighlights.Location = New-Object System.Drawing.Point(184, 118)
$labelHighlights.Size = New-Object System.Drawing.Size(720, 24)
$labelHighlights.Text = Z('5a6e5pe25pel5b+XICB8ICDnm67lvZXpgInmi6kgIHwgIOahjOmdouW/q+aNt+aWueW8jyAgfCAg5aSN55So546w5pyJIGluc3RhbGwuYmF0')
$labelHighlights.Font = $fontSmall
$labelHighlights.ForeColor = $accent
$brandPanel.Controls.Add($labelHighlights)

$settingsPanel = New-Object System.Windows.Forms.Panel
$settingsPanel.Location = New-Object System.Drawing.Point(18, 204)
$settingsPanel.Size = New-Object System.Drawing.Size(928, 190)
$settingsPanel.BackColor = $surface
$settingsPanel.Anchor = 'Top, Left, Right'
$form.Controls.Add($settingsPanel)

$labelPath = New-Object System.Windows.Forms.Label
$labelPath.Location = New-Object System.Drawing.Point(24, 22)
$labelPath.Size = New-Object System.Drawing.Size(180, 24)
$labelPath.Text = Z('5a6J6KOF55uu5b2V')
$labelPath.Font = $fontBody
$labelPath.ForeColor = $textPrimary
$settingsPanel.Controls.Add($labelPath)

$textInstallPath = New-Object System.Windows.Forms.TextBox
$textInstallPath.Location = New-Object System.Drawing.Point(24, 50)
$textInstallPath.Size = New-Object System.Drawing.Size(720, 28)
$textInstallPath.Font = $fontBody
$textInstallPath.Text = (Join-Path $env:LOCALAPPDATA 'HemaFix')
$textInstallPath.Anchor = 'Top, Left, Right'
$settingsPanel.Controls.Add($textInstallPath)

$buttonBrowse = New-Object System.Windows.Forms.Button
$buttonBrowse.Location = New-Object System.Drawing.Point(760, 48)
$buttonBrowse.Size = New-Object System.Drawing.Size(140, 34)
$buttonBrowse.Text = Z('6YCJ5oup55uu5b2V')
$buttonBrowse.Font = $fontBody
$buttonBrowse.BackColor = $surface
$buttonBrowse.FlatStyle = 'Flat'
$buttonBrowse.FlatAppearance.BorderColor = $accent
$buttonBrowse.ForeColor = $accent
$buttonBrowse.Anchor = 'Top, Right'
$settingsPanel.Controls.Add($buttonBrowse)

$labelMode = New-Object System.Windows.Forms.Label
$labelMode.Location = New-Object System.Drawing.Point(24, 98)
$labelMode.Size = New-Object System.Drawing.Size(180, 24)
$labelMode.Text = Z('5a6J6KOF54mI5pys')
$labelMode.Font = $fontBody
$labelMode.ForeColor = $textPrimary
$settingsPanel.Controls.Add($labelMode)

$comboMode = New-Object System.Windows.Forms.ComboBox
$comboMode.Location = New-Object System.Drawing.Point(24, 126)
$comboMode.Size = New-Object System.Drawing.Size(210, 30)
$comboMode.Font = $fontBody
$comboMode.DropDownStyle = 'DropDownList'
[void]$comboMode.Items.Add((Z('5a6M5pW05a6J6KOF')))
[void]$comboMode.Items.Add((Z('6L276YeP5a6J6KOF')))
$comboMode.SelectedIndex = 0
$settingsPanel.Controls.Add($comboMode)

$labelModeHint = New-Object System.Windows.Forms.Label
$labelModeHint.Location = New-Object System.Drawing.Point(250, 129)
$labelModeHint.Size = New-Object System.Drawing.Size(360, 24)
$labelModeHint.Font = $fontSmall
$labelModeHint.ForeColor = $textMuted
$settingsPanel.Controls.Add($labelModeHint)

$checkGatewayShortcut = New-Object System.Windows.Forms.CheckBox
$checkGatewayShortcut.Location = New-Object System.Drawing.Point(620, 108)
$checkGatewayShortcut.Size = New-Object System.Drawing.Size(280, 28)
$checkGatewayShortcut.Text = Z('5Yib5bu65qGM6Z2i5b+r5o235pa55byP77ya5ZCv5Yqo572R5YWz')
$checkGatewayShortcut.Checked = $true
$checkGatewayShortcut.Font = $fontBody
$checkGatewayShortcut.ForeColor = $textPrimary
$checkGatewayShortcut.Anchor = 'Top, Right'
$settingsPanel.Controls.Add($checkGatewayShortcut)

$checkWebUiShortcut = New-Object System.Windows.Forms.CheckBox
$checkWebUiShortcut.Location = New-Object System.Drawing.Point(620, 138)
$checkWebUiShortcut.Size = New-Object System.Drawing.Size(280, 28)
$checkWebUiShortcut.Text = Z('5Yib5bu65qGM6Z2i5b+r5o235pa55byP77ya5ZCv5YqoIFdlYiBVSQ==')
$checkWebUiShortcut.Checked = $true
$checkWebUiShortcut.Font = $fontBody
$checkWebUiShortcut.ForeColor = $textPrimary
$checkWebUiShortcut.Anchor = 'Top, Right'
$settingsPanel.Controls.Add($checkWebUiShortcut)

$progressPanel = New-Object System.Windows.Forms.Panel
$progressPanel.Location = New-Object System.Drawing.Point(18, 410)
$progressPanel.Size = New-Object System.Drawing.Size(928, 88)
$progressPanel.BackColor = $surface
$progressPanel.Anchor = 'Top, Left, Right'
$form.Controls.Add($progressPanel)

$labelStatus = New-Object System.Windows.Forms.Label
$labelStatus.Location = New-Object System.Drawing.Point(24, 18)
$labelStatus.Size = New-Object System.Drawing.Size(620, 24)
$labelStatus.Text = Z('5bey5YeG5aSH5bCx57uq77yM54K55Ye74oCc5byA5aeL5a6J6KOF4oCd5byA5aeL44CC')
$labelStatus.Font = $fontBody
$labelStatus.ForeColor = $textPrimary
$progressPanel.Controls.Add($labelStatus)

$labelProgressValue = New-Object System.Windows.Forms.Label
$labelProgressValue.Location = New-Object System.Drawing.Point(820, 18)
$labelProgressValue.Size = New-Object System.Drawing.Size(80, 24)
$labelProgressValue.Text = '0%'
$labelProgressValue.TextAlign = 'MiddleRight'
$labelProgressValue.Font = $fontBody
$labelProgressValue.ForeColor = $accent
$progressPanel.Controls.Add($labelProgressValue)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(24, 50)
$progressBar.Size = New-Object System.Drawing.Size(876, 18)
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$progressBar.Anchor = 'Top, Left, Right'
$progressPanel.Controls.Add($progressBar)

$logPanel = New-Object System.Windows.Forms.Panel
$logPanel.Location = New-Object System.Drawing.Point(18, 514)
$logPanel.Size = New-Object System.Drawing.Size(928, 190)
$logPanel.BackColor = $surface
$logPanel.Anchor = 'Top, Bottom, Left, Right'
$form.Controls.Add($logPanel)

$labelLog = New-Object System.Windows.Forms.Label
$labelLog.Location = New-Object System.Drawing.Point(24, 14)
$labelLog.Size = New-Object System.Drawing.Size(180, 24)
$labelLog.Text = Z('5a6J6KOF5pel5b+X')
$labelLog.Font = $fontBody
$labelLog.ForeColor = $textPrimary
$logPanel.Controls.Add($labelLog)

$logBox = New-Object System.Windows.Forms.RichTextBox
$logBox.Location = New-Object System.Drawing.Point(24, 44)
$logBox.Size = New-Object System.Drawing.Size(876, 126)
$logBox.ReadOnly = $true
$logBox.Font = $fontMono
$logBox.BackColor = $logBg
$logBox.ForeColor = $logFg
$logBox.BorderStyle = 'FixedSingle'
$logBox.WordWrap = $false
$logBox.DetectUrls = $false
$logBox.Anchor = 'Top, Bottom, Left, Right'
$logPanel.Controls.Add($logBox)

$buttonInstall = New-Object System.Windows.Forms.Button
$buttonInstall.Location = New-Object System.Drawing.Point(742, 726)
$buttonInstall.Size = New-Object System.Drawing.Size(204, 34)
$buttonInstall.Text = Z('5byA5aeL5a6J6KOF')
$buttonInstall.Font = New-Object System.Drawing.Font('Microsoft YaHei UI', 10, [System.Drawing.FontStyle]::Bold)
$buttonInstall.BackColor = $accent
$buttonInstall.ForeColor = [System.Drawing.Color]::White
$buttonInstall.FlatStyle = 'Flat'
$buttonInstall.FlatAppearance.BorderSize = 0
$buttonInstall.Anchor = 'Bottom, Right'
$form.Controls.Add($buttonInstall)

$buttonOpenFolder = New-Object System.Windows.Forms.Button
$buttonOpenFolder.Location = New-Object System.Drawing.Point(548, 726)
$buttonOpenFolder.Size = New-Object System.Drawing.Size(178, 34)
$buttonOpenFolder.Text = Z('5omT5byA5a6J6KOF55uu5b2V')
$buttonOpenFolder.Font = $fontBody
$buttonOpenFolder.BackColor = $surface
$buttonOpenFolder.FlatStyle = 'Flat'
$buttonOpenFolder.FlatAppearance.BorderColor = $accent
$buttonOpenFolder.ForeColor = $accent
$buttonOpenFolder.Visible = $false
$buttonOpenFolder.Anchor = 'Bottom, Right'
$form.Controls.Add($buttonOpenFolder)

$buttonClose = New-Object System.Windows.Forms.Button
$buttonClose.Location = New-Object System.Drawing.Point(18, 726)
$buttonClose.Size = New-Object System.Drawing.Size(122, 34)
$buttonClose.Text = Z('5YWz6Zet')
$buttonClose.Font = $fontBody
$buttonClose.BackColor = $surface
$buttonClose.FlatStyle = 'Flat'
$buttonClose.FlatAppearance.BorderColor = $textMuted
$buttonClose.ForeColor = $textPrimary
$buttonClose.Anchor = 'Bottom, Left'
$form.Controls.Add($buttonClose)

$folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
$folderDialog.Description = Z('6YCJ5oupIEhlbWEg55qE5a6J6KOF55uu5b2V')
$folderDialog.ShowNewFolderButton = $true

$appendLogAction = [System.Action[object]]{
    param($state)
    if ($state.Progress -ne $null) {
        $progressValue = [Math]::Max(0, [Math]::Min(100, [int]$state.Progress))
        $progressBar.Value = $progressValue
        $labelProgressValue.Text = ('{0}%' -f $progressValue)
    }
    if ($state.Status) {
        $labelStatus.Text = [string]$state.Status
    }
    if ($state.Text) {
        $logBox.AppendText(([string]$state.Text) + [Environment]::NewLine)
        $logBox.SelectionStart = $logBox.TextLength
        $logBox.ScrollToCaret()
    }
}

$buttonBrowse.Add_Click({
    $folderDialog.SelectedPath = $textInstallPath.Text
    if ($folderDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $textInstallPath.Text = $folderDialog.SelectedPath
    }
})

$comboMode.Add_SelectedIndexChanged({ Update-InstallModeUi })
Update-InstallModeUi

$buttonClose.Add_Click({
    if ($script:IsInstalling) {
        [System.Windows.Forms.MessageBox]::Show((Z('5a6J6KOF5LuN5Zyo6L+b6KGM5Lit77yM6K+3562J5b6F5a6J6KOF5a6M5oiQ44CC')), (Z('SGVtYSDlronoo4Xlmag=')), 'OK', 'Information') | Out-Null
        return
    }
    $form.Close()
})

$buttonOpenFolder.Add_Click({
    if ($script:LastInstallPath -and (Test-Path -LiteralPath $script:LastInstallPath)) {
        Start-Process explorer.exe $script:LastInstallPath | Out-Null
    }
})

function Set-InstallUiState {
    param([bool]$Installing)
    $script:IsInstalling = $Installing
    $buttonInstall.Enabled = -not $Installing
    $buttonBrowse.Enabled = -not $Installing
    $comboMode.Enabled = -not $Installing
    $checkGatewayShortcut.Enabled = -not $Installing
    if ($Installing) {
        $checkWebUiShortcut.Enabled = $false
    } else {
        Update-InstallModeUi
    }
}

function Complete-InstallSuccess {
    param($result)

    $script:LastInstallPath = $result.InstallPath
    $iconPath = Join-Path $result.InstallPath 'assets\installer\hippo-installer.ico'
    $sourceImage = Join-Path $result.InstallPath 'assets\installer\hippo-installer.jpg'
    if (-not (Test-Path -LiteralPath $iconPath)) {
        if (Test-Path -LiteralPath $script:BrandIconPath) {
            Copy-Item -LiteralPath $script:BrandIconPath -Destination $iconPath -Force
        } else {
            [void](Convert-BrandImageToIcon -ImagePath $sourceImage -IconPath $iconPath)
        }
    }

    if ($result.CreateGatewayShortcut) {
        Remove-DesktopShortcut -Name 'Hema Gateway'
        $gatewayBat = Join-Path $result.InstallPath 'start_hermes_gateway.bat'
        if (Test-Path -LiteralPath $gatewayBat) {
            New-DesktopShortcut -Name (Z('5rKz6ams572R5YWz')) -TargetPath $env:ComSpec -Arguments ("/c `"$gatewayBat`"") -WorkingDirectory $result.InstallPath -IconLocation $iconPath
        }
    }

    if ($result.Mode -eq 'full' -and $result.CreateWebUiShortcut) {
        Remove-DesktopShortcut -Name 'Hema Web UI'
        $webuiBat = Join-Path $result.InstallPath 'start_webui.bat'
        if (Test-Path -LiteralPath $webuiBat) {
            New-DesktopShortcut -Name (Z('5rKz6amsIFdlYiDnrqHnkIbnlYzpnaI=')) -TargetPath $env:ComSpec -Arguments ("/c `"$webuiBat`"") -WorkingDirectory $result.InstallPath -IconLocation $iconPath
        }
    }

    Refresh-ShellIconCache

    $appendLogAction.Invoke(@{
        Progress = 100
        Status = (Z('5a6J6KOF5a6M5oiQ44CC'))
        Text = (Z('Pj4+IOWuieijheW3suWujOaIkO+8jOW/q+aNt+aWueW8j+WSjOWQr+WKqOWFpeWPo+W3suWHhuWkh+Wwsee7quOAgg=='))
    })

    $buttonOpenFolder.Visible = $true
    [System.Windows.Forms.MessageBox]::Show(((Z('5a6J6KOF5a6M5oiQ44CCYG5gbuWuieijheebruW9le+8mg==')) + $result.InstallPath), (Z('SGVtYSDlronoo4Xlmag=')), 'OK', 'Information') | Out-Null
}

$script:InstallJob = $null
$script:InstallJobResult = $null

$jobTimer = New-Object System.Windows.Forms.Timer
$jobTimer.Interval = 700
$jobTimer.Add_Tick({
    if (-not $script:InstallJob) {
        return
    }

    $updates = @(Receive-Job -Job $script:InstallJob -ErrorAction SilentlyContinue)
    foreach ($item in $updates) {
        if ($null -eq $item) {
            continue
        }

        if ($item.Kind -eq 'result') {
            $script:InstallJobResult = $item
            continue
        }

        $appendLogAction.Invoke($item)
    }

    if ($script:InstallJob.State -notin @('Completed', 'Failed', 'Stopped')) {
        return
    }

    $jobTimer.Stop()
    $remaining = @(Receive-Job -Job $script:InstallJob -ErrorAction SilentlyContinue)
    foreach ($item in $remaining) {
        if ($null -eq $item) {
            continue
        }

        if ($item.Kind -eq 'result') {
            $script:InstallJobResult = $item
            continue
        }

        $appendLogAction.Invoke($item)
    }

    Set-InstallUiState -Installing $false

    if ($script:InstallJob.State -eq 'Completed' -and $script:InstallJobResult) {
        Complete-InstallSuccess -result $script:InstallJobResult
    } else {
        $errorMessage = $null
        if ($script:InstallJob.ChildJobs.Count -gt 0) {
            $reason = $script:InstallJob.ChildJobs[0].JobStateInfo.Reason
            if ($reason) {
                $errorMessage = $reason.Message
            }
            if (-not $errorMessage) {
                $jobError = $script:InstallJob.ChildJobs[0].Error | Select-Object -Last 1
                if ($jobError) {
                    $errorMessage = $jobError.ToString()
                }
            }
        }
        if (-not $errorMessage) {
            $errorMessage = Z('5ZCO5Y+w5a6J6KOF5Lu75Yqh5oSP5aSW57uT5p2f77yM6K+35qOA5p+l5pel5b+X44CC')
        }

        $appendLogAction.Invoke(@{
            Progress = 100
            Status = (Z('5a6J6KOF5aSx6LSl77yM6K+35qOA5p+l5pel5b+X44CC'))
            Text = ((Z('W+mUmeivr10g')) + ' ' + $errorMessage)
        })
        [System.Windows.Forms.MessageBox]::Show($errorMessage, (Z('5a6J6KOF5aSx6LSl')), 'OK', 'Error') | Out-Null
    }

    Remove-Job -Job $script:InstallJob -Force -ErrorAction SilentlyContinue
    $script:InstallJob = $null
    $script:InstallJobResult = $null
})

$buttonInstall.Add_Click({
    if ($script:IsInstalling) {
        return
    }

    $targetPath = $textInstallPath.Text.Trim()
    if ([string]::IsNullOrWhiteSpace($targetPath)) {
        [System.Windows.Forms.MessageBox]::Show((Z('6K+35YWI6YCJ5oup5a6J6KOF55uu5b2V44CC')), (Z('SGVtYSDlronoo4Xlmag=')), 'OK', 'Warning') | Out-Null
        return
    }

    try {
        [void](Resolve-NormalizedPath $targetPath)
    } catch {
        [System.Windows.Forms.MessageBox]::Show((Z('6YCJ5oup55qE5a6J6KOF55uu5b2V5peg5pWI44CC')), (Z('SGVtYSDlronoo4Xlmag=')), 'OK', 'Warning') | Out-Null
        return
    }

    Set-InstallUiState -Installing $true
    $buttonOpenFolder.Visible = $false
    $progressBar.Value = 0
    $labelProgressValue.Text = '0%'
    $labelStatus.Text = Z('5bey5YeG5aSH5bCx57uq77yM54K55Ye74oCc5byA5aeL5a6J6KOF4oCd5byA5aeL44CC')
    $logBox.Clear()

    $mode = if ($comboMode.SelectedIndex -eq 0) { 'full' } else { 'lite' }
    $script:InstallJobResult = $null
    $script:InstallJob = Start-Job -ArgumentList @(@{
        SourceDir = $script:SourceDir
        TargetDir = $targetPath
        Mode = $mode
        CreateGatewayShortcut = $checkGatewayShortcut.Checked
        CreateWebUiShortcut = $checkWebUiShortcut.Checked
    }) -ScriptBlock {
        param($config)

        function Resolve-NormalizedPath {
            param([string]$Path)
            [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
        }

        function Z {
            param([string]$Base64)
            [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Base64))
        }

        function New-Update {
            param(
                [string]$Kind = 'update',
                [object]$Progress = $null,
                [string]$Status = $null,
                [string]$Text = $null,
                [string]$InstallPath = $null,
                [string]$Mode = $null,
                [bool]$CreateGatewayShortcut = $false,
                [bool]$CreateWebUiShortcut = $false
            )

            [pscustomobject]@{
                Kind = $Kind
                Progress = $Progress
                Status = $Status
                Text = $Text
                InstallPath = $InstallPath
                Mode = $Mode
                CreateGatewayShortcut = $CreateGatewayShortcut
                CreateWebUiShortcut = $CreateWebUiShortcut
            }
        }

        function Emit-Update {
            param(
                [object]$Progress = $null,
                [string]$Status = $null,
                [string]$Text = $null
            )

            New-Update -Progress $Progress -Status $Status -Text $Text
        }

        $sourceDir = Resolve-NormalizedPath $config.SourceDir
        $targetDir = Resolve-NormalizedPath $config.TargetDir

        if ($targetDir.StartsWith($sourceDir + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
            throw (Z('5a6J6KOF55uu5b2V5LiN6IO95pS+5Zyo5b2T5YmN5a6J6KOF5YyF55uu5b2V5YaF6YOo77yM6K+36YCJ5oup5YW25LuW55uu5b2V44CC'))
        }

        Emit-Update -Progress 3 -Status (Z('5q2j5Zyo5YeG5aSH5a6J6KOF55uu5b2VLi4u')) -Text ((Z('5rqQ55uu5b2V77ya')) + $sourceDir)
        Emit-Update -Progress 5 -Status (Z('5q2j5Zyo5YeG5aSH5a6J6KOF55uu5b2VLi4u')) -Text ((Z('55uu5qCH55uu5b2V77ya')) + $targetDir)

        if (-not (Test-Path -LiteralPath $targetDir)) {
            [System.IO.Directory]::CreateDirectory($targetDir) | Out-Null
        }

        if ($sourceDir -ne $targetDir) {
            Emit-Update -Progress 8 -Status (Z('5q2j5Zyo5aSN5Yi25a6J6KOF5paH5Lu2Li4u')) -Text (Z('5q2j5Zyo5ZCM5q2l5a6J6KOF5YyF5paH5Lu25Yiw55uu5qCH55uu5b2VLi4u'))
            $excludeDirs = @('.git', '.github', '__pycache__', 'node_modules', '.npm-cache', '.plans', 'testlogs')
            $excludeFiles = @('.install-complete', 'gateway_fg_test.err.log', 'gateway_fg_test.out.log')
            $robocopyArgs = @(
                $sourceDir,
                $targetDir,
                '/E',
                '/R:1',
                '/W:1',
                '/NP',
                '/NFL',
                '/NDL',
                '/NJH',
                '/NJS',
                '/XD'
            ) + $excludeDirs + @('/XF') + $excludeFiles

            & robocopy.exe @robocopyArgs 2>&1 | ForEach-Object {
                if ($_ -is [string] -and -not [string]::IsNullOrWhiteSpace($_)) {
                    Emit-Update -Text $_
                }
            }
            if ($LASTEXITCODE -gt 7) {
                throw ((Z('5aSN5Yi25a6J6KOF5paH5Lu25aSx6LSl77yMcm9ib2NvcHkg6YCA5Ye656CB77yaezB9')) -f $LASTEXITCODE)
            }

            Emit-Update -Progress 16 -Status (Z('5a6J6KOF5paH5Lu25bey5bCx57uq44CC')) -Text (Z('5paH5Lu25ZCM5q2l5a6M5oiQ44CC'))
        } else {
            Emit-Update -Progress 16 -Status (Z('5bCG55u05o6l5Zyo5b2T5YmN55uu5b2V5a6J6KOF44CC')) -Text (Z('5rqQ55uu5b2V5ZKM55uu5qCH55uu5b2V55u45ZCM77yM5bey6Lez6L+H5aSN5Yi244CC'))
        }

        $installBat = Join-Path $targetDir 'install.bat'
        if (-not (Test-Path -LiteralPath $installBat)) {
            throw (Z('55uu5qCH55uu5b2V5Lit5pyq5om+5YiwIGluc3RhbGwuYmF044CC'))
        }

        $modeArg = if ($config.Mode -eq 'full') { 'full' } else { 'lite' }
        Emit-Update -Progress 18 -Status (Z('5q2j5Zyo5omn6KGM5a6J6KOF6ISa5pysLi4u')) -Text ((Z('5q2j5Zyo5omn6KGMIGluc3RhbGwuYmF0IA==')) + $modeArg)

        Push-Location $targetDir
        try {
            $env:HERMES_INSTALLER_NO_PAUSE = '1'
            cmd.exe /c "`"$installBat`" $modeArg" 2>&1 | ForEach-Object {
                $line = "$_"
                if ([string]::IsNullOrWhiteSpace($line)) {
                    return
                }

                $status = $null
                $progress = $null
                if ($line -match '\[STEP\s+(\d+)/(\d+)\]') {
                    $current = [int]$matches[1]
                    $total = [int]$matches[2]
                    if ($total -gt 0) {
                        $progress = 18 + [Math]::Round(($current / $total) * 74)
                        $status = ((Z('5q2j5Zyo5a6J6KOF6L+Q6KGM546v5aKD77ya5q2l6aqkIHswfS97MX0=')) -f $current, $total)
                    }
                }

                Emit-Update -Progress $progress -Status $status -Text $line
            }
            if ($LASTEXITCODE -ne 0) {
                throw ((Z('5a6J6KOF6ISa5pys5omn6KGM5aSx6LSl77yM6YCA5Ye656CB77yaezB9')) -f $LASTEXITCODE)
            }
        } finally {
            Pop-Location
        }

        $completionFile = Join-Path $targetDir '.install-complete'
        if (-not (Test-Path -LiteralPath $completionFile)) {
            throw (Z('5a6J6KOF5a6M5oiQ5ZCO5pyq55Sf5oiQ5a6M5oiQ5qCH6K6w5paH5Lu244CC'))
        }

        New-Update -Kind 'result' -InstallPath $targetDir -Mode $config.Mode -CreateGatewayShortcut $config.CreateGatewayShortcut -CreateWebUiShortcut $config.CreateWebUiShortcut
    }
    $jobTimer.Start()
})

$form.Add_FormClosing({
    param($sender, $e)
    if ($script:IsInstalling) {
        $e.Cancel = $true
        [System.Windows.Forms.MessageBox]::Show((Z('5a6J6KOF5LuN5Zyo6L+b6KGM5Lit77yM6K+3562J5b6F5a6J6KOF5a6M5oiQ5ZCO5YaN5YWz6Zet56qX5Y+j44CC')), (Z('SGVtYSDlronoo4Xlmag=')), 'OK', 'Information') | Out-Null
    }
})

[void]$form.ShowDialog()
