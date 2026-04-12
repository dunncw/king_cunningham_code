# Testing

## Quick Ref

```powershell
# Mode 1: Full rebuild + install + launch (no GitHub)
.\scripts\test-local.ps1

# Mode 2: Skip build, reuse dist\ (no GitHub)
.\scripts\test-local.ps1 -SkipBuild

# Mode 3: Update flow — publishes real release, idempotent (GitHub)
.\scripts\test-local.ps1 -TestUpdate
```

## Test Modes

| Mode | Flag | Build | GitHub | What it tests |
|------|------|-------|--------|---------------|
| 1 | (none) | yes | no | Build pipeline, self-install, shortcut, app launch |
| 2 | `-SkipBuild` | no | no | Self-install, shortcut, app launch (fast iteration) |
| 3 | `-TestUpdate` | yes | yes | Old version (0.0.0) sees new release, downloads, extracts, launches |

## Test Reports

JSON reports → `data/test-reports/` (gitignored). Each run produces:

```json
{
  "timestamp": "2026-04-12T14:30:00-05:00",
  "mode": "full-rebuild",
  "version": "0.0.15",
  "host": "WORKSTATION",
  "timings": { "build": 45.2, "seed": 1.1, "app_load_time": 3.8 },
  "checks": { "launcher_installed": true, "shortcut_created": true, ... },
  "passed": 6,
  "failed": 0
}
```

Use reports to track regressions over time (build duration, app load time).

## Benchmarks

| Metric | What | Warn threshold |
|--------|------|----------------|
| `app_load_time` | Launcher start → KC_app process visible | > 10s |
| `build` | Full `python build.py` | informational |
| `user_update_flow_total` | Launcher start → KC_app after update (mode 3) | informational |

## Checks per Mode

### Mode 1 & 2

| Check | Validates |
|-------|-----------|
| `dist_kc_app_exists` | Build produced `dist\KC_app\KC_app.exe` |
| `dist_launcher_exists` | Build produced `dist\launcher.exe` |
| `launcher_installed` | `dist\launcher.exe` self-copied to install dir |
| `shortcut_created` | Start Menu `.lnk` exists |
| `kc_app_running` | KC_app.exe process is alive |
| `kc_app_exe_exists` | `KC_app.exe` in install dir |
| `version_file_exists` | `version.txt` in install dir |
| `no_crash_log` | No `%TEMP%\kc_launcher_error.log` |

### Mode 3 (Update)

| Check | Validates |
|-------|-----------|
| `dist_kc_app_exists` | Build artifacts present |
| `dist_launcher_exists` | Build artifacts present |
| `dist_zip_exists` | `KC_app.zip` exists for upload |
| `launcher_installed` | Self-install worked |
| `shortcut_created` | Shortcut created |
| `kc_app_running` | App launched after update |
| `version_updated` | `version.txt` updated from 0.0.0 → current |
| `staging_cleaned` | No `KC_app_staging` dir left behind |
| `no_crash_log` | No crash log |

## Idempotency (Mode 3)

Mode 3 is safe to rerun indefinitely:

1. **Before publish** — deletes any existing release + tag (local + remote) for `v{version}`
2. **On clean exit** — deletes release + tag after user confirms
3. **On dirty exit** (ctrl+C, crash) — next run cleans up before creating new release

No manual cleanup needed between runs.

## Gotchas

- **Draft releases** — `/releases/latest` API ignores drafts. Mode 3 publishes real release → visible to users while it exists. Press Enter promptly after verifying.
- **Locked EXE** — script kills stale `KC_app` and `launcher` processes before each run. If still locked, check Task Manager.
- **GitHub repo** — launcher API URL = `dunncw/king_cunningham_code`. Git remote shows `King_app.git` — GitHub redirects, this is fine.
- **Stale staging dirs** — interrupted update may leave `KC_app_staging` or `KC_app_old`. Launcher cleans automatically next run. Mode 3 checks for this.
- **Env var scope** — `KC_LAUNCHER_SKIP_UPDATE` set only for child process in modes 1/2.

## Cleanup (manual, if needed)

```powershell
# Nuke install dir
Remove-Item "$env:LOCALAPPDATA\King_Cunningham\KC_App" -Recurse -Force -ErrorAction SilentlyContinue

# Remove shortcut
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk" -Force -ErrorAction SilentlyContinue

# Remove orphaned test release
gh release delete "v$(Get-Content version.txt -Raw)" --yes 2>$null
git tag -d "v$(Get-Content version.txt -Raw)" 2>$null
```
