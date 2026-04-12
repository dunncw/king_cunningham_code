# KC Automation Suite

Windows-only PyQt6 desktop app. Employees install → modules automate paperwork (OCR, PDF processing, barcode scanning, doc generation).

Two-EXE model: small `launcher.exe` (self-installer + auto-updater) + large `KC_app.zip` (app payload downloaded on demand). Distributed via GitHub Releases.

Repo: `github.com/dunncw/king_cunningham_code`

## Doc Map

### Structural Docs — How System Works

Explain architecture + process. Stable. Version-agnostic.

| Doc | Scope |
|---|---|
| [packaging-architecture.md](packaging-architecture.md) | Two-EXE model, build pipeline, version flow, install layout, update mechanism, dep chain |
| [build.md](build.md) | How to build, release, manage binary deps. Hands-on steps |
| [testing.md](testing.md) | Local test harness, manual test procedures, gotchas |
| [user-experience.md](user-experience.md) | End user journey: first install, updates, error scenarios, UX pain points |

### Living Docs — Current State

Track active issues + decisions. Update as things change.

| Doc | Scope |
|---|---|
| [known-issues.md](known-issues.md) | Open bugs, improvement backlog (HIGH/MED/LOW), industry comparison, priority order |

## Status Marks — Living Doc Legend

Living docs use these marks. One mark per item. No ambiguity.

| Mark | Meaning | When use |
|---|---|---|
| `DONE` | Fixed. Shipped. In code | Merged + verified |
| `HUNT` | Actively working on | Has owner, in progress |
| `NEXT` | Queued. Will do | Decided yes, not started |
| `WAIT` | Blocked or deferred | Need something first |
| `WONT` | Not doing. Dead | Deliberate skip — always document why |
| `WATCH` | Eye on it. Not acting | Revisit if conditions change |

Format in living docs: **`[MARK]`** at start of item title. Example: **`[WONT]`** **No code signing** — too expensive for user base size.

## Quick Reference

| What | Where |
|---|---|
| Version source of truth | `version.txt` (repo root) |
| Build entry point | `python build.py` |
| Release automation | `scripts/release.ps1` |
| Local test harness | `scripts/test-local.ps1` |
| Launcher source | `launcher/launcher.py` |
| App entry point | `src/main.py` |
| GitHub API (launcher) | `api.github.com/repos/dunncw/king_cunningham_code/releases/latest` |
| Install dir (user machine) | `%LOCALAPPDATA%\King_Cunningham\KC_App\` |
| Config dir (user machine) | `%APPDATA%\King_Cunningham\` |
| Crash log (user machine) | `%TEMP%\kc_launcher_error.log` |
