<#
.SYNOPSIS
    Starts RAG Studio in Docker, then opens it in Chrome (or the system default browser).
.DESCRIPTION
    Starts Docker Desktop if its engine is not running, runs `docker compose up -d` from this folder (adding
    compose.gpu.yaml when nvidia-smi finds an NVIDIA GPU), waits for the API
    and UI to answer, starts the hidden Windows folder dialog helper (folder-picker/) and opens the UI. Stop everything
    with the UI's Shut down button.

    Without a build flag, a menu offers "no build" (default) or "build" for 5 seconds. No build still builds any image
    that does not exist yet; build also rebuilds existing images, which picks up code changes. Without a browser flag, a
    second menu offers Chrome (default) or the system default browser, also for 5 seconds.

    Flags work in either style: --chrome / -Chrome, --default / -Default, --build / -Build, --no-build / -NoBuild.
.PARAMETER Chrome
    Open the UI in Google Chrome (the default); falls back to the system default browser when Chrome is not installed.
.PARAMETER Default
    Open the UI in the system default browser.
.PARAMETER Build
    Rebuild the images before starting, skipping the menu.
.PARAMETER NoBuild
    Start from the existing images, skipping the menu.
.EXAMPLE
    .\start.ps1 --default --build
#>
param(
    [switch]$Chrome,
    [switch]$Default,
    [switch]$Build,
    [switch]$NoBuild,
    [Parameter(ValueFromRemainingArguments)][string[]]$GnuStyleFlags
)

# Explorer's "Run with PowerShell" uses Windows PowerShell 5.1; the menus need PowerShell 7, so hand off to pwsh and keep
# the window open on failure so the error stays readable.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    if (-not (Get-Command pwsh -ErrorAction SilentlyContinue)) {
        Write-Host 'RAG Studio needs PowerShell 7, which is not installed.' -ForegroundColor Red
        Write-Host 'Install it with "winget install Microsoft.PowerShell" or "choco install powershell-core", then run start.ps1 again.'
        Read-Host 'Press Enter to close'
        exit 1
    }
    $forwardedFlags = @($PSBoundParameters.Keys | Where-Object { $_ -ne 'GnuStyleFlags' } | ForEach-Object { "-$_" }) + $GnuStyleFlags
    pwsh -NoProfile -ExecutionPolicy Bypass -File $PSCommandPath @forwardedFlags
    if ($LASTEXITCODE) { Read-Host 'RAG Studio failed to start. Press Enter to close' }
    exit $LASTEXITCODE
}

$ErrorActionPreference = 'Stop'
$StudioUrl = 'http://localhost:3000'
$ApiHealthUrl = 'http://localhost:8000/api/health'
$FolderPickerHealthUrl = 'http://127.0.0.1:8010/health'
$FolderPickerScript = Join-Path $PSScriptRoot 'folder-picker\folder_picker.py'
$DockerDesktopRegistryKey = 'HKLM:\SOFTWARE\Docker Inc.\Docker Desktop'
$ChromeRegistryKeys = @(
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe'
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe'
)

# PowerShell reads `--chrome` as a plain argument, not a switch, so the double-dash spellings are mapped here.
foreach ($flag in $GnuStyleFlags) {
    switch ($flag) {
        '--chrome' { $Chrome = $true }
        '--default' { $Default = $true }
        '--build' { $Build = $true }
        '--no-build' { $NoBuild = $true }
        default { throw "Unknown argument '$flag'. Use --chrome, --default, --build or --no-build." }
    }
}
if ($Chrome -and $Default) { throw 'Choose one browser: --chrome or --default.' }
if ($Build -and $NoBuild) { throw 'Choose one: --build or --no-build.' }

$BuildChoices = @('No build: start from the existing images (fast)', 'Build: rebuild the images first (after code changes)')
$BrowserChoices = @('Chrome', 'System default browser')
$MenuSeconds = 5

function Format-ChoiceFrame([string]$Prompt, [string[]]$Options, [int]$Selected, [int]$SecondsLeft) {
    <# The menu's lines for one redraw: prompt with countdown, then each option, the selected one highlighted. #>
    $header = "$Prompt (Up/Down to choose, Enter to confirm, auto-selects in ${SecondsLeft}s)"
    $rows = for ($index = 0; $index -lt $Options.Count; $index++) {
        if ($index -eq $Selected) { "  $($PSStyle.Reverse)> $($Options[$index])$($PSStyle.ReverseOff)" } else { "    $($Options[$index])" }
    }
    return @($header) + $rows
}

function Read-TimedChoice([string]$Prompt, [string[]]$Options, [int]$DefaultIndex, [int]$TimeoutSeconds) {
    <# Arrow keys move the highlight and Enter picks it; when the time runs out the highlighted option is picked. Returns its index. #>
    $selected = $DefaultIndex
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lineCount = $Options.Count + 1
    $drawn = $false
    [Console]::CursorVisible = $false
    try {
        while ($true) {
            $secondsLeft = [math]::Ceiling(($deadline - (Get-Date)).TotalSeconds)
            if ($drawn) { [Console]::Write("`e[${lineCount}A") }
            foreach ($line in Format-ChoiceFrame $Prompt $Options $selected ([math]::Max($secondsLeft, 0))) {
                [Console]::Write("`e[2K$line`n")
            }
            $drawn = $true
            if ($secondsLeft -le 0) { return $selected }
            if (-not [Console]::KeyAvailable) {
                Start-Sleep -Milliseconds 100
                continue
            }
            switch ([Console]::ReadKey($true).Key) {
                'UpArrow' { $selected = ($selected - 1 + $Options.Count) % $Options.Count }
                'DownArrow' { $selected = ($selected + 1) % $Options.Count }
                'Enter' { return $selected }
            }
        }
    } finally {
        [Console]::CursorVisible = $true
    }
}

function Select-BuildMode {
    <# $true to rebuild. A flag decides without asking; without a keyboard (input redirected) the default is used. #>
    if ($Build -or $NoBuild) { return [bool]$Build }
    if ([Console]::IsInputRedirected) { return $false }
    return (Read-TimedChoice 'How should RAG Studio start?' $BuildChoices 0 $MenuSeconds) -eq 1
}

function Select-DefaultBrowser {
    <# $true for the system default browser. A flag decides without asking; so does a missing Chrome (both options would
    open the same browser) and a missing keyboard (input redirected), which keep Chrome as the choice. #>
    if ($Chrome -or $Default) { return [bool]$Default }
    if ([Console]::IsInputRedirected -or -not (Find-Chrome)) { return $false }
    return (Read-TimedChoice 'Which browser should open RAG Studio?' $BrowserChoices 0 $MenuSeconds) -eq 1
}

function Test-DockerEngine {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { return $false }
    docker info --format '{{.ServerVersion}}' *> $null
    return $LASTEXITCODE -eq 0
}

function Find-DockerDesktop {
    <# Docker Desktop.exe in the folder its installer records; the default install folder when that record is missing. #>
    $recorded = (Get-ItemProperty $DockerDesktopRegistryKey -ErrorAction SilentlyContinue).AppPath
    $folder = if ($recorded) { $recorded } else { Join-Path $env:ProgramFiles 'Docker\Docker' }
    return Join-Path $folder 'Docker Desktop.exe'
}

function Wait-Until([scriptblock]$Condition, [string]$What, [int]$TimeoutSeconds) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (-not (& $Condition)) {
        if ((Get-Date) -gt $deadline) { throw "$What did not become ready within $TimeoutSeconds seconds." }
        Start-Sleep -Seconds 2
    }
}

function Test-Url([string]$Url) {
    try { return (Invoke-WebRequest $Url -UseBasicParsing -TimeoutSec 3).StatusCode -eq 200 } catch { return $false }
}

function Find-Chrome {
    <# Path of chrome.exe from the per-user or machine-wide App Paths registration; $null when Chrome is not installed. #>
    foreach ($key in $ChromeRegistryKeys) {
        $path = (Get-ItemProperty $key -ErrorAction SilentlyContinue).'(default)'
        if ($path -and (Test-Path $path)) { return $path }
    }
    return $null
}

function Start-FolderPicker {
    <# The Windows folder dialog behind the Browse… button. It runs hidden, outside Docker, and the UI's Shut down button
    stops it. Already running: nothing to do. No uv: Browse… is unavailable, typing a path still works. #>
    if (Test-Url $FolderPickerHealthUrl) { return }
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Warning 'uv is not installed, so Browse… cannot open the Windows folder dialog. Type source paths instead.'
        return
    }
    Start-Process uv -ArgumentList @('run', '--script', "`"$FolderPickerScript`"") -WindowStyle Hidden
}

function Open-Studio([bool]$UseDefaultBrowser) {
    $chromePath = if ($UseDefaultBrowser) { $null } else { Find-Chrome }
    if ($chromePath) {
        Start-Process $chromePath $StudioUrl
        return 'Chrome'
    }
    if (-not $UseDefaultBrowser) { Write-Warning 'Chrome is not installed; opening the system default browser instead.' }
    Start-Process $StudioUrl
    return 'the default browser'
}

function Test-NvidiaGpu {
    if (-not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) { return $false }
    nvidia-smi --query-gpu=name --format=csv,noheader *> $null
    return $LASTEXITCODE -eq 0
}

function Get-ComposeFileArguments {
    if (Test-NvidiaGpu) {
        Write-Host 'NVIDIA GPU found: GPU choices are on.'
        return '-f', 'compose.yaml', '-f', 'compose.gpu.yaml'
    }
    Write-Warning 'No NVIDIA GPU found (nvidia-smi is missing or failed): every model runs on the CPU.'
    return '-f', 'compose.yaml'
}

$rebuild = Select-BuildMode
$useDefaultBrowser = Select-DefaultBrowser

if (-not (Test-DockerEngine)) {
    $dockerDesktop = Find-DockerDesktop
    if (-not (Test-Path $dockerDesktop)) {
        throw "Docker Desktop was not found at $dockerDesktop. Install it (see README.md, Requirements), or start it by hand and run start.ps1 again."
    }
    Write-Host 'Starting Docker Desktop...'
    Start-Process $dockerDesktop
    Wait-Until { Test-DockerEngine } 'The Docker engine' 240
}

# Without --build, compose still builds any image that does not exist yet.
Write-Host $(if ($rebuild) { 'Building and starting RAG Studio...' } else { 'Starting RAG Studio (missing images are built)...' })
Push-Location $PSScriptRoot
try {
    docker compose @(Get-ComposeFileArguments) up -d @(if ($rebuild) { '--build' })
    if ($LASTEXITCODE) { throw "docker compose up failed (exit code $LASTEXITCODE)." }
} finally {
    Pop-Location
}

Write-Host 'Waiting for the API and UI...'
Wait-Until { Test-Url $ApiHealthUrl } 'The API' 180
Wait-Until { Test-Url $StudioUrl } 'The UI' 120
Start-FolderPicker

$browser = Open-Studio $useDefaultBrowser
Write-Host "RAG Studio is running at $StudioUrl (opened in $browser). Use the Shut down button in the UI to stop it."
