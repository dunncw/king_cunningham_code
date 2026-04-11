# Test the launcher and KC_app locally.
#
# Usage:
#   .\scripts\test-local.ps1              # Build + full self-install + launch test
#   .\scripts\test-local.ps1 -SkipBuild   # Re-use existing dist\ outputs
#   .\scripts\test-local.ps1 -TestUpdate  # Test the update download flow (publishes a real release, then deletes it)
#
# The default test runs dist\launcher.exe so that the self-install code fires,
# the shortcut is created, and the installed launcher handles the launch.
# KC_LAUNCHER_SKIP_UPDATE=1 is inherited by all child processes so the GitHub
# check is skipped end-to-end without needing a live release.

param(
    [switch]$SkipBuild,
    [switch]$TestUpdate
)

$ErrorActionPreference = "Stop"

$installDir = "$env:LOCALAPPDATA\King_Cunningham\KC_App"
$shortcut   = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk"
$version    = (Get-Content version.txt -Raw).Trim()

# ── 1. Build ────────────────────────────────────────────────────────────────
if (-not $SkipBuild) {
    Write-Host "[build] Building version $version ..."
    python build.py
    if ($LASTEXITCODE -ne 0) { Write-Error "Build failed."; exit 1 }
}

# ── 2. Clean previous test install ──────────────────────────────────────────
Write-Host "[setup] Cleaning previous install ..."
if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
if (Test-Path $shortcut)   { Remove-Item $shortcut -Force -ErrorAction SilentlyContinue }

# ── 3. Pre-seed KC_app directory and version.txt so the installed launcher
#       can launch immediately without downloading anything.
#       Do NOT copy launcher.exe — let dist\launcher.exe self-install it.
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item "dist\KC_app" "$installDir\KC_app" -Recurse -Force
$version | Set-Content "$installDir\version.txt"

if ($TestUpdate) {
    # ── Update-flow test ────────────────────────────────────────────────────
    # Override the pre-seeded version so the launcher thinks it's out of date.
    # Publishes a real (non-draft) release so /releases/latest returns it.
    # WARNING: this release is visible to anyone running the launcher while it exists.

    "0.0.0" | Set-Content "$installDir\version.txt"

    Write-Host "[release] Publishing test release v$version ..."
    gh release create "v$version" dist\KC_app.zip `
        --title "v$version" `
        --notes "Local test release — will be deleted."
    if ($LASTEXITCODE -ne 0) { Write-Error "gh release create failed."; exit 1 }

    Write-Host "[launch] Running dist\launcher.exe (self-install + update prompt expected) ..."
    & "dist\launcher.exe"

    Write-Host ""
    Write-Host "Press Enter once you have verified the update flow ..."
    $null = Read-Host

    Write-Host "[cleanup] Deleting test release and tag ..."
    gh release delete "v$version" --yes
    git tag -d "v$version" 2>$null
    git push origin ":refs/tags/v$version" 2>$null
    Write-Host "[cleanup] Done."

} else {
    # ── Normal test (no GitHub required) ────────────────────────────────────
    Write-Host "[launch] Running dist\launcher.exe ..."
    Write-Host "         Watch for: self-install, shortcut creation, app launch."

    $logFile = "$env:TEMP\kc_launcher_error.log"
    if (Test-Path $logFile) { Remove-Item $logFile -Force }

    $env:KC_LAUNCHER_SKIP_UPDATE = "1"
    Start-Process -FilePath "dist\launcher.exe"
    $env:KC_LAUNCHER_SKIP_UPDATE = $null

    Write-Host "         Polling for launcher.exe in install dir (up to 30 s) ..."
    $deadline = (Get-Date).AddSeconds(30)
    while (-not (Test-Path "$installDir\launcher.exe") -and (Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
    }

    Start-Sleep -Seconds 5

    Write-Host ""
    Write-Host "── Results ──────────────────────────────────────────────────"
    $launcherInstalled = Test-Path "$installDir\launcher.exe"
    $shortcutCreated   = Test-Path $shortcut
    $appRunning        = (Get-Process -Name "KC_app" -ErrorAction SilentlyContinue) -ne $null

    Write-Host ("  launcher.exe installed : " + $(if ($launcherInstalled) { "YES" } else { "NO  <-- FAIL" }))
    Write-Host ("  Start Menu shortcut    : " + $(if ($shortcutCreated)   { "YES" } else { "NO  <-- FAIL" }))
    Write-Host ("  KC_app.exe running     : " + $(if ($appRunning)        { "YES" } else { "NO (may have opened and closed, check manually)" }))

    if (Test-Path $logFile) {
        Write-Host ""
        Write-Host "── Launcher crash log ($logFile) ─────────────────────────"
        Get-Content $logFile | ForEach-Object { Write-Host "  $_" }
    }
}
