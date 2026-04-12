# Local Testing

## Quick Ref

```powershell
# Test install + launch (no GitHub)
.\scripts\test-local.ps1

# Skip build step
.\scripts\test-local.ps1 -SkipBuild

# Full update download flow (publishes + deletes real release)
.\scripts\test-local.ps1 -TestUpdate
```

## Test Coverage

| Test | Build | GitHub | Covers |
|---|---|---|---|
| `test-local.ps1` | yes (or -SkipBuild) | no | Self-install, shortcut, app launch |
| `test-local.ps1 -TestUpdate` | yes | yes (real release) | Update prompt, zip download, extraction, version.txt update |

## Manual: Normal Test (no GitHub)

`test-local.ps1` automates this. Manual steps for debugging:

```powershell
$installDir = "$env:LOCALAPPDATA\King_Cunningham\KC_App"

# 1. Build
python build.py

# 2. Clean prev install
Remove-Item $installDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk" -Force -ErrorAction SilentlyContinue

# 3. Seed install dir w/ KC_app dir + version.txt only.
#    Do NOT copy launcher.exe — dist\launcher.exe self-installs it.
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item dist\KC_app "$installDir\KC_app" -Recurse -Force
(Get-Content version.txt -Raw).Trim() | Set-Content $installDir\version.txt

# 4. Run dist\launcher.exe (self-install + shortcut).
#    KC_LAUNCHER_SKIP_UPDATE=1 bypasses GitHub check.
$env:KC_LAUNCHER_SKIP_UPDATE = "1"
Start-Process dist\launcher.exe
$env:KC_LAUNCHER_SKIP_UPDATE = $null

# Poll until launcher copies itself (up to 30s)
$deadline = (Get-Date).AddSeconds(30)
while (-not (Test-Path "$installDir\launcher.exe") -and (Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
}
```

Verify:
- App opens
- `$installDir\launcher.exe` exists (self-installed)
- `$installDir\KC_app\KC_app.exe` exists
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk` exists
- Simplifile3 config → `%APPDATA%\King_Cunningham\simplifile3_config.json`

## Manual: Update Flow (requires GitHub)

`/releases/latest` API → only published, non-draft, non-prerelease. Drafts/prereleases invisible to launcher. Must publish real release.

`test-local.ps1 -TestUpdate` handles automatically:
1. Sets install dir `version.txt` → `0.0.0`
2. Publishes real release w/ `KC_app.zip` under current version tag
3. Runs launcher → update prompt + progress dialog
4. After confirm → deletes release + git tag

Manual:
```powershell
$version = (Get-Content version.txt -Raw).Trim()

# Old version → triggers update prompt
"0.0.0" | Set-Content "$env:LOCALAPPDATA\King_Cunningham\KC_App\version.txt"

# Publish (WARNING: visible to users while exists)
gh release create "v$version" dist\KC_app.zip --title "v$version"

# Run launcher
& "$env:LOCALAPPDATA\King_Cunningham\KC_App\launcher.exe"

# Cleanup
gh release delete "v$version" --yes
git tag -d "v$version"
git push origin ":refs/tags/v$version"
```

## Cleanup Between Runs

```powershell
Remove-Item "$env:LOCALAPPDATA\King_Cunningham\KC_App" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk" -Force -ErrorAction SilentlyContinue
```

## Gotchas

- **Draft releases** → never returned by `/releases/latest`. Use `test-local.ps1 -TestUpdate` (publishes real release + cleans up).
- **Env var scope**: `$env:KC_LAUNCHER_SKIP_UPDATE` in PowerShell → only affects child processes in that session. Launcher reads on startup.
- **Locked EXE**: Running launcher.exe → copy fails. Kill process first or wait for exit.
- **GitHub repo**: Launcher API URL → `dunncw/king_cunningham_code` (resolved name). Git remote still shows `King_app.git` — fine, GitHub redirects.
- **Stale staging dirs**: Interrupted update → `KC_app_staging` or `KC_app_old` may remain. Launcher cleans automatically next run.
