# Build + Release

## Overview

Windows-only PyQt6 desktop app. Build outputs:

| File | Purpose |
|---|---|
| `dist/KC_app/` | Onedir output. `KC_app.exe` + DLLs + data. |
| `dist/KC_app.zip` | Zipped onedir. Release asset launcher downloads. |
| `dist/launcher.exe` | Self-installing launcher. Users keep forever. Checks GitHub updates each run. |
| `dist/version.txt` | Installed version string. Read/written by launcher. |

## Prereqs

- Python 3.x + venv at `.venv/`
- All pkgs from `requirements.txt`
- Internet on first build (Tesseract download → `bin/`)

## Build

### 1. Set version

Edit `version.txt` at repo root:

```
0.0.14
```

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

```
dist/
  KC_app/           (onedir: KC_app.exe + DLLs)
  KC_app.zip        (zipped release asset)
  launcher.exe      (~37 MB)
  version.txt       (version string)
```

## Release

```bash
# 1. Version
echo "0.0.15" > version.txt

# 2. Build
python build.py

# 3. Commit, merge → main, tag, push
git add version.txt src/main.py
git commit -m "chore: bump version to 0.0.15"
# merge feature → dev → main
git checkout main && git merge dev
git tag v0.0.15
git push origin main --tags

# 4. GitHub Release — include KC_app.zip.
#    launcher.exe only for new user distribution.
gh release create v0.0.15 dist/KC_app.zip --title "v0.0.15"
```

Launcher checks `https://api.github.com/repos/dunncw/king_cunningham_code/releases/latest` → downloads asset named exactly `KC_app.zip`. Name must match.

## New User Distribution

Users only need `launcher.exe`. Give once:
- First run → self-install to `%LOCALAPPDATA%\King_Cunningham\KC_App\launcher.exe`
- Creates "KC Automation Suite" Start Menu entry
- Downloads `KC_app.zip` from latest GitHub release → extracts
- Subsequent runs → auto-check updates before launch

## Binary Deps (bin/)

`bin/` gitignored. Populated by `scripts/setup_binaries.py` at build time.

Pinned:
- **Tesseract OCR** 5.4.0.20240606 -- UB-Mannheim Windows build

Upgrade Tesseract: delete `bin/tesseract/`, update URL in `scripts/setup_binaries.py`, run:

```
python scripts/setup_binaries.py
```

## Windows Paths

| Data | Location |
|---|---|
| Installed EXEs | `%LOCALAPPDATA%\King_Cunningham\KC_App\` |
| App dir | `%LOCALAPPDATA%\King_Cunningham\KC_App\KC_app\` |
| App config | `%APPDATA%\King_Cunningham\` |
| Build outputs | `dist\` (gitignored) |
| External bins (build-time) | `bin\` (gitignored) |
