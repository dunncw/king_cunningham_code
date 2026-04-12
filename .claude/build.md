# Build + Release

## Build Outputs

| File | Purpose |
|---|---|
| `dist/KC_app/` | Onedir output. `KC_app.exe` + DLLs + data |
| `dist/KC_app.zip` | Zipped onedir. Release asset launcher downloads |
| `dist/launcher.exe` | Self-installing launcher. Users keep forever. Checks GitHub updates each run |
| `dist/version.txt` | Version string copy |

## Prereqs

- Python 3.x + venv at `.venv/`
- All pkgs from `requirements.txt`
- Internet on first build (Tesseract download → `bin/`)

## Build

### 1. Set version

Edit `version.txt` at repo root. Single line, format `X.Y.Z`.

### 2. Run build

```
python build.py
```

Does:
- Sync `__version__` in `src/main.py` ← `version.txt`
- Download Tesseract → `bin/` if missing (first time only)
- Build `dist/KC_app/` via PyInstaller (onedir)
- Zip → `dist/KC_app.zip`
- Build `dist/launcher.exe` via PyInstaller
- Write `dist/version.txt`

### 3. Verify

All four outputs in `dist/`. Build script prints summary w/ sizes.

## Release

### Automated (recommended)

```powershell
# 1. Edit version.txt
# 2. Run:
.\scripts\release.ps1        # full release
.\scripts\release.ps1 -Draft # draft (invisible to users)
```

`release.ps1` handles: build → commit version bump → git tag → push → `gh release create` w/ `KC_app.zip` + `launcher.exe`.

### Manual

```bash
# 1. Set version in version.txt
# 2. Build
python build.py

# 3. Commit, tag, push
git add version.txt src/main.py
git commit -m "chore: bump version to $(cat version.txt)"
git tag "v$(cat version.txt)"
git push origin $(git branch --show-current) --tags

# 4. GitHub Release
gh release create "v$(cat version.txt)" dist/KC_app.zip dist/launcher.exe --title "v$(cat version.txt)"
```

### Critical constraints

- Launcher fetches `/releases/latest` → only published, non-draft, non-prerelease releases visible
- Asset name must = `KC_app.zip` exactly. Launcher matches by name
- Version tags must follow `vX.Y.Z` format. Launcher strips `v` prefix, splits on `.` for comparison

## New User Distribution

Users only need `launcher.exe`. Give once (email, Slack, USB, GitHub release page).

- First run → self-install → Start Menu shortcut → download app → launch
- Subsequent runs → auto-check updates before launch
- See [user-experience.md](user-experience.md) for full UX flow

## Binary Deps (bin/)

`bin/` gitignored. Populated by `scripts/setup_binaries.py` at build time.

Pinned:
- **Tesseract OCR** — UB-Mannheim Windows build. Version pinned in `scripts/setup_binaries.py`

Upgrade Tesseract: delete `bin/tesseract/`, update URL in `scripts/setup_binaries.py`, rebuild.

## Windows Paths

| Data | Location |
|---|---|
| Installed EXEs | `%LOCALAPPDATA%\King_Cunningham\KC_App\` |
| App dir | `%LOCALAPPDATA%\King_Cunningham\KC_App\KC_app\` |
| App config | `%APPDATA%\King_Cunningham\` |
| Build outputs | `dist\` (gitignored) |
| External bins (build-time) | `bin\` (gitignored) |
