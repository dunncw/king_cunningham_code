# Build and Release Guide

## Overview

This is a Windows-only PyQt6 desktop app. The build pipeline produces:

| File | Purpose |
|---|---|
| `dist/KC_app/` | Onedir output. Contains `KC_app.exe` plus all DLLs and data files. |
| `dist/KC_app.zip` | Zipped onedir output. This is the release asset the launcher downloads. |
| `dist/launcher.exe` | Small self-installing launcher. Users keep this forever. Checks GitHub for updates on each run. |
| `dist/version.txt` | Installed version string. Read and written by the launcher. |

## Prerequisites

- Python 3.x with virtualenv at `.venv/`
- All packages from `requirements.txt` installed
- Internet access on first build (to download Tesseract into `bin/`)

## Build Steps

### 1. Set the version

Edit `version.txt` at the repo root. Use the format that matches your git tags, e.g.:

```
0.0.14
```

### 2. Run the build

```
python build.py
```

This will:
- Sync `__version__` in `src/main.py` to match `version.txt`
- Download and install Tesseract into `bin/` if missing (first time only)
- Build `dist/KC_app/` directory via PyInstaller (onedir mode)
- Zip the directory into `dist/KC_app.zip`
- Build `dist/launcher.exe` via PyInstaller
- Write `dist/version.txt`

### 3. Verify outputs

```
dist/
  KC_app/           (onedir output, contains KC_app.exe + DLLs)
  KC_app.zip        (zipped release asset)
  launcher.exe      (~37 MB)
  version.txt       (version string)
```

## Release Process

```bash
# 1. Update version
echo "0.0.15" > version.txt

# 2. Build
python build.py

# 3. Commit, merge to main, tag, push
git add version.txt src/main.py
git commit -m "chore: bump version to 0.0.15"
# merge feature branch -> dev -> main (see branch workflow)
git checkout main && git merge dev
git tag v0.0.15
git push origin main --tags

# 4. Create GitHub Release — include KC_app.zip.
#    launcher.exe is only needed for new user distribution.
gh release create v0.0.15 dist/KC_app.zip --title "v0.0.15"
```

The launcher checks `https://api.github.com/repos/dunncw/king_cunningham_code/releases/latest` and
downloads an asset named exactly `KC_app.zip`. The asset name must match that string.

## Distributing the Launcher to New Users

Users only ever need `launcher.exe`. Give it to them once:
- On first run it installs itself to `%LOCALAPPDATA%\King_Cunningham\KC_App\launcher.exe`
- Creates a "KC Automation Suite" Start Menu entry
- Downloads `KC_app.zip` from the latest GitHub release and extracts it
- On every subsequent run it auto-checks for updates before launching

## Binary Dependencies (bin/)

`bin/` is gitignored. Binaries are populated by `scripts/setup_binaries.py` at build time.

Pinned versions:
- **Tesseract OCR** 5.4.0.20240606 -- UB-Mannheim Windows build

To upgrade Tesseract: delete the `bin/tesseract/` subdirectory, update the URL constant in `scripts/setup_binaries.py`, then re-run:

```
python scripts/setup_binaries.py
```

## Windows Path Conventions

| Data type | Location |
|---|---|
| Installed EXEs | `%LOCALAPPDATA%\King_Cunningham\KC_App\` |
| App directory | `%LOCALAPPDATA%\King_Cunningham\KC_App\KC_app\` |
| App config files | `%APPDATA%\King_Cunningham\` |
| Build outputs | `dist\` (gitignored) |
| External binaries (build-time) | `bin\` (gitignored) |
