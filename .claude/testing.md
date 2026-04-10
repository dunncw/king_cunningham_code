# Local Testing Guide

## Quick reference

```powershell
# Test install + launch (no GitHub needed)
.\scripts\test-local.ps1

# Same but skip the build step
.\scripts\test-local.ps1 -SkipBuild

# Test the full update download flow (publishes + deletes a real release)
.\scripts\test-local.ps1 -TestUpdate
```

## What each test covers

| Test | Build needed | GitHub needed | Covers |
|---|---|---|---|
| `test-local.ps1` | yes (or -SkipBuild) | no | Self-install, shortcut creation, app launch |
| `test-local.ps1 -TestUpdate` | yes | yes (publishes real release) | Update prompt, download, version.txt update |

## Step-by-step: normal test (no GitHub)

`test-local.ps1` does all of this automatically, but here it is manually if you need to debug a specific step:

```powershell
$installDir = "$env:LOCALAPPDATA\King_Cunningham\KC_App"

# 1. Build
python build.py

# 2. Clean previous test install
Remove-Item $installDir -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC App.lnk" -Force -ErrorAction SilentlyContinue

# 3. Seed install dir with built outputs
New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item dist\KC_app.exe  $installDir\ -Force
Copy-Item dist\launcher.exe $installDir\ -Force
(Get-Content version.txt -Raw).Trim() | Set-Content $installDir\version.txt

# 4. Run launcher (KC_LAUNCHER_SKIP_UPDATE=1 bypasses the GitHub check)
$env:KC_LAUNCHER_SKIP_UPDATE = "1"
& "$installDir\launcher.exe"
$env:KC_LAUNCHER_SKIP_UPDATE = $null
```

Check:
- App opens normally
- `%APPDATA%\Microsoft\Windows\Start Menu\Programs\KC App.lnk` exists
- Simplifile3 config saves to `%APPDATA%\King_Cunningham\simplifile3_config.json`

## Step-by-step: update flow test (requires GitHub)

The `/releases/latest` API only returns **published, non-draft, non-prerelease** releases.
Drafts and pre-releases are invisible to the launcher. You need to publish a real release.

`test-local.ps1 -TestUpdate` handles this automatically:
1. Sets `version.txt` in the install dir to `0.0.0`
2. Publishes a real release under the current version tag
3. Runs the launcher — you should see the update prompt and progress dialog
4. After you confirm, deletes the release and the git tag

To do it manually:
```powershell
$version = (Get-Content version.txt -Raw).Trim()

# Write an old version to trigger the update prompt
"0.0.0" | Set-Content "$env:LOCALAPPDATA\King_Cunningham\KC_App\version.txt"

# Publish the release (WARNING: visible to users while it exists)
gh release create "v$version" dist\KC_app.exe --title "v$version"

# Run the launcher
& "$env:LOCALAPPDATA\King_Cunningham\KC_App\launcher.exe"

# Cleanup after testing
gh release delete "v$version" --yes
git tag -d "v$version"
git push origin ":refs/tags/v$version"
```

## Cleanup between test runs

```powershell
Remove-Item "$env:LOCALAPPDATA\King_Cunningham\KC_App" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC App.lnk" -Force -ErrorAction SilentlyContinue
```

## Known gotchas

- **Draft releases** are never returned by `/releases/latest`. Use `test-local.ps1 -TestUpdate` which publishes a real release and cleans it up.
- **Env var scope**: `$env:KC_LAUNCHER_SKIP_UPDATE` set in PowerShell only affects child processes in that session. The launcher reads it on startup.
- **Locked EXE**: If a launcher.exe is already running, copying over it will fail. Kill the process first or wait for it to exit.
- **GitHub repo**: The launcher API URL points to `dunncw/king_cunningham_code` (the resolved name). The git remote URL still shows `King_app.git` — this is fine, GitHub redirects it.
