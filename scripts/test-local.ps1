# Test the launcher and KC_app locally.
#
# Three test modes:
#   .\scripts\test-local.ps1                # Mode 1: Full rebuild + self-install + launch (no GitHub)
#   .\scripts\test-local.ps1 -SkipBuild     # Mode 2: Skip build, reuse dist\ + self-install + launch (no GitHub)
#   .\scripts\test-local.ps1 -TestUpdate    # Mode 3: Full update flow (publishes real release, idempotent)
#
# Reports written to data/test-reports/ as JSON for data-driven development.

param(
    [switch]$SkipBuild,
    [switch]$TestUpdate
)

$ErrorActionPreference = "Stop"

# ── Paths ──────────────────────────────────────────────────────────────────
$repoRoot   = (Resolve-Path "$PSScriptRoot\..").Path
$installDir = "$env:LOCALAPPDATA\King_Cunningham\KC_App"
$shortcut   = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk"
$version    = (Get-Content "$repoRoot\version.txt" -Raw).Trim()
$reportDir  = "$repoRoot\data\test-reports"
$logFile    = "$env:TEMP\kc_launcher_error.log"

# ── Logging ────────────────────────────────────────────────────────────────
function Log {
    param([string]$Phase, [string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $prefix = "[$ts][$Level][$Phase]"
    switch ($Level) {
        "FAIL" { Write-Host "$prefix $Message" -ForegroundColor Red }
        "PASS" { Write-Host "$prefix $Message" -ForegroundColor Green }
        "WARN" { Write-Host "$prefix $Message" -ForegroundColor Yellow }
        default { Write-Host "$prefix $Message" }
    }
}

function Measure-Phase {
    param([string]$Name, [scriptblock]$Block)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    & $Block
    $sw.Stop()
    $script:timings[$Name] = $sw.Elapsed.TotalSeconds
    Log $Name "completed in $([math]::Round($sw.Elapsed.TotalSeconds, 2))s"
}

# ── Report ─────────────────────────────────────────────────────────────────
function Write-TestReport {
    param([hashtable]$Results)
    if (-not (Test-Path $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }

    $mode = if ($TestUpdate) { "update" } elseif ($SkipBuild) { "skip-build" } else { "full-rebuild" }
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $reportPath = "$reportDir\test_${mode}_${timestamp}.json"

    $report = @{
        timestamp  = (Get-Date -Format "o")
        mode       = $mode
        version    = $version
        host       = $env:COMPUTERNAME
        timings    = @{}
        checks     = $Results
        passed     = ($Results.Values | Where-Object { $_ -eq $true }).Count
        failed     = ($Results.Values | Where-Object { $_ -eq $false }).Count
    }

    foreach ($k in $script:timings.Keys) {
        $report.timings[$k] = [math]::Round($script:timings[$k], 3)
    }

    $report | ConvertTo-Json -Depth 4 | Set-Content $reportPath -Encoding UTF8
    Log "report" "saved → $reportPath"
    return $reportPath
}

# ── Cleanup helper (idempotent) ────────────────────────────────────────────
function Remove-TestRelease {
    param([string]$Ver)
    $tag = "v$Ver"

    $existing = gh release view $tag 2>&1
    if ($LASTEXITCODE -eq 0) {
        Log "cleanup" "deleting existing release $tag"
        gh release delete $tag --yes 2>$null
    }

    git tag -d $tag 2>$null
    git push origin ":refs/tags/$tag" 2>$null
    Log "cleanup" "tag $tag cleaned (local + remote)"
}

# ── Kill stale processes ───────────────────────────────────────────────────
function Stop-StaleProcesses {
    foreach ($name in @("KC_app", "launcher")) {
        $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
        if ($procs) {
            Log "cleanup" "killing stale $name process(es)"
            $procs | Stop-Process -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
        }
    }
}

# ── Assertions ─────────────────────────────────────────────────────────────
function Assert-Check {
    param([string]$Name, [bool]$Condition)
    $script:checks[$Name] = $Condition
    if ($Condition) {
        Log "check" $Name "PASS"
    } else {
        Log "check" $Name "FAIL"
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

$script:timings = @{}
$script:checks  = @{}

$mode = if ($TestUpdate) { "MODE 3: Update Flow (GitHub)" } elseif ($SkipBuild) { "MODE 2: Skip Build (no GitHub)" } else { "MODE 1: Full Rebuild (no GitHub)" }
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  KC Test Harness — $mode" -ForegroundColor Cyan
Write-Host "  Version: $version" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# ── Kill stale processes from previous runs ────────────────────────────────
Stop-StaleProcesses

# ── Build (modes 1 & 3) ───────────────────────────────────────────────────
if (-not $SkipBuild) {
    Measure-Phase "build" {
        Log "build" "building version $version ..."
        python "$repoRoot\build.py"
        if ($LASTEXITCODE -ne 0) { throw "Build failed." }
    }
}

# ── Verify dist artifacts ─────────────────────────────────────────────────
Log "preflight" "checking dist artifacts ..."
$distKcApp    = Test-Path "$repoRoot\dist\KC_app\KC_app.exe"
$distLauncher = Test-Path "$repoRoot\dist\launcher.exe"
Assert-Check "dist_kc_app_exists" $distKcApp
Assert-Check "dist_launcher_exists" $distLauncher
if (-not $distKcApp -or -not $distLauncher) { throw "Missing dist artifacts. Run without -SkipBuild first." }

if ($TestUpdate) {
    $distZip = Test-Path "$repoRoot\dist\KC_app.zip"
    Assert-Check "dist_zip_exists" $distZip
    if (-not $distZip) { throw "Missing dist\KC_app.zip. Run without -SkipBuild first." }
}

# ── Clean previous install ─────────────────────────────────────────────────
Log "setup" "cleaning previous install dir ..."
if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
if (Test-Path $shortcut)   { Remove-Item $shortcut -Force -ErrorAction SilentlyContinue }
if (Test-Path $logFile)    { Remove-Item $logFile -Force }

# ── Seed install dir ───────────────────────────────────────────────────────
Measure-Phase "seed" {
    Log "seed" "pre-seeding install dir ..."
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    Copy-Item "$repoRoot\dist\KC_app" "$installDir\KC_app" -Recurse -Force
    $version | Set-Content "$installDir\version.txt"
}

if ($TestUpdate) {
    # ══════════════════════════════════════════════════════════════════════
    # MODE 3: Update flow (idempotent)
    # ══════════════════════════════════════════════════════════════════════

    # Override version so launcher thinks it's outdated
    "0.0.0" | Set-Content "$installDir\version.txt"
    Log "setup" "set installed version → 0.0.0 (trigger update)"

    # Idempotent: clean any leftover release/tag from previous runs
    Remove-TestRelease $version

    Measure-Phase "publish" {
        Log "release" "publishing test release v$version ..."
        gh release create "v$version" "$repoRoot\dist\KC_app.zip" `
            --title "v$version" `
            --notes "Local test release — will be deleted."
        if ($LASTEXITCODE -ne 0) { throw "gh release create failed." }
    }

    Log "launch" "running dist\launcher.exe (update prompt expected) ..."
    $launchStart = [System.Diagnostics.Stopwatch]::StartNew()
    & "$repoRoot\dist\launcher.exe"

    # Wait for KC_app to appear (user clicks "Yes" on update dialog)
    Log "bench" "waiting for KC_app process (up to 120s) ..."
    $deadline = (Get-Date).AddSeconds(120)
    while (-not (Get-Process -Name "KC_app" -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
    }
    $launchStart.Stop()
    $script:timings["user_update_flow_total"] = $launchStart.Elapsed.TotalSeconds

    Start-Sleep -Seconds 3

    # ── Checks ─────────────────────────────────────────────────────────
    $installedVersion = if (Test-Path "$installDir\version.txt") {
        (Get-Content "$installDir\version.txt" -Raw).Trim()
    } else { "" }

    Assert-Check "launcher_installed"    (Test-Path "$installDir\launcher.exe")
    Assert-Check "shortcut_created"      (Test-Path $shortcut)
    Assert-Check "kc_app_running"        ((Get-Process -Name "KC_app" -ErrorAction SilentlyContinue) -ne $null)
    Assert-Check "version_updated"       ($installedVersion -eq $version)
    Assert-Check "staging_cleaned"       (-not (Test-Path "$installDir\KC_app_staging"))
    Assert-Check "no_crash_log"          (-not (Test-Path $logFile))

    # ── Cleanup release (idempotent) ───────────────────────────────────
    Write-Host ""
    Write-Host "Press Enter after verifying update flow (release will be deleted) ..." -ForegroundColor Yellow
    $null = Read-Host

    Remove-TestRelease $version

} else {
    # ══════════════════════════════════════════════════════════════════════
    # MODE 1 & 2: Local test (no GitHub)
    # ══════════════════════════════════════════════════════════════════════

    Log "launch" "running dist\launcher.exe (KC_LAUNCHER_SKIP_UPDATE=1) ..."

    $env:KC_LAUNCHER_SKIP_UPDATE = "1"
    $launchStart = [System.Diagnostics.Stopwatch]::StartNew()
    Start-Process -FilePath "$repoRoot\dist\launcher.exe"
    $env:KC_LAUNCHER_SKIP_UPDATE = $null

    # Poll for launcher self-install
    Log "bench" "waiting for launcher.exe in install dir (up to 30s) ..."
    $deadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path "$installDir\launcher.exe") -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
    }

    # Poll for KC_app process (user-facing load time)
    Log "bench" "waiting for KC_app process (up to 60s) ..."
    $deadline = (Get-Date).AddSeconds(60)
    while (-not (Get-Process -Name "KC_app" -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 500
    }
    $launchStart.Stop()
    $script:timings["app_load_time"] = $launchStart.Elapsed.TotalSeconds
    Log "bench" "app_load_time = $([math]::Round($launchStart.Elapsed.TotalSeconds, 2))s" $(if ($launchStart.Elapsed.TotalSeconds -gt 10) { "WARN" } else { "INFO" })

    Start-Sleep -Seconds 2

    # ── Checks ─────────────────────────────────────────────────────────
    Assert-Check "launcher_installed"    (Test-Path "$installDir\launcher.exe")
    Assert-Check "shortcut_created"      (Test-Path $shortcut)
    Assert-Check "kc_app_running"        ((Get-Process -Name "KC_app" -ErrorAction SilentlyContinue) -ne $null)
    Assert-Check "kc_app_exe_exists"     (Test-Path "$installDir\KC_app\KC_app.exe")
    Assert-Check "version_file_exists"   (Test-Path "$installDir\version.txt")
    Assert-Check "no_crash_log"          (-not (Test-Path $logFile))
}

# ── Crash log dump ─────────────────────────────────────────────────────────
if (Test-Path $logFile) {
    Write-Host ""
    Log "crash" "launcher crash log found:" "WARN"
    Get-Content $logFile | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
}

# ── Summary ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Results" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$passCount = ($script:checks.Values | Where-Object { $_ -eq $true }).Count
$failCount = ($script:checks.Values | Where-Object { $_ -eq $false }).Count
$total = $passCount + $failCount

foreach ($k in ($script:checks.Keys | Sort-Object)) {
    $v = $script:checks[$k]
    $mark = if ($v) { "PASS" } else { "FAIL" }
    $color = if ($v) { "Green" } else { "Red" }
    Write-Host "  [$mark] $k" -ForegroundColor $color
}

Write-Host ""
if ($script:timings.Count -gt 0) {
    Write-Host "  Timings:" -ForegroundColor Cyan
    foreach ($k in ($script:timings.Keys | Sort-Object)) {
        $v = [math]::Round($script:timings[$k], 2)
        $color = "White"
        if ($k -eq "app_load_time" -and $v -gt 10) { $color = "Yellow" }
        Write-Host "    $k = ${v}s" -ForegroundColor $color
    }
    Write-Host ""
}

$reportPath = Write-TestReport $script:checks

if ($failCount -gt 0) {
    Write-Host "  $failCount/$total FAILED" -ForegroundColor Red
    exit 1
} else {
    Write-Host "  $passCount/$total PASSED" -ForegroundColor Green
    exit 0
}
