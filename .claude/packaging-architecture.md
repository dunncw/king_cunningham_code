# Packaging Architecture

## Two-EXE Model

```
launcher.exe (~40 MB)     KC_app.zip (~180 MB)
   onefile EXE               onedir ZIP
   self-contained             downloaded on demand
   user keeps forever         replaced each update
```

Why two: launcher = small, fast download for new users. App = big, only downloaded when needed/updated. Decoupled → can fix launcher bugs w/o rebuilding app (theory — see [known-issues.md](known-issues.md) re: launcher self-update gap).

## Build Pipeline

```
version.txt ──→ build.py ──→ dist/
                   │            ├── KC_app/          (onedir)
                   │            ├── KC_app.zip       (release asset)
                   │            ├── launcher.exe     (self-installer)
                   │            └── version.txt
                   │
                   ├── sync version → src/main.py
                   ├── setup_binaries.py (Tesseract → bin/)
                   ├── pyinstaller KC_app.spec
                   ├── zip onedir → KC_app.zip
                   └── pyinstaller launcher/launcher.spec
```

## PyInstaller Modes

| Component | Mode | Why |
|---|---|---|
| KC_app | onedir | Fast startup. No temp extraction. DLLs load direct. |
| launcher | onefile | Single portable EXE. User downloads one file. Startup speed irrelevant (runs once → launches app). |

Onedir = `KC_app.exe` + `_internal/` folder w/ all DLLs + Python runtime.
Onefile = everything packed into single EXE, extracted to temp dir at runtime.

## Version Flow

```
version.txt (source of truth)
     │
     ├──→ build.py syncs → src/main.py __version__
     ├──→ build.py copies → dist/version.txt
     ├──→ release.ps1 → git tag vX.Y.Z
     └──→ launcher writes → %LOCALAPPDATA%\..\version.txt (local install)
```

Comparison: launcher reads local version.txt → compares w/ GitHub `/releases/latest` tag_name → tuple comparison `(0,0,15) > (0,0,14)`.

## Distribution Channel

GitHub Releases only. No app store, no website, no CDN.

```
release.ps1
  ├── python build.py
  ├── git commit version bump
  ├── git tag vX.Y.Z
  ├── git push --tags
  └── gh release create vX.Y.Z dist/KC_app.zip dist/launcher.exe
```

Launcher fetches: `api.github.com/repos/dunncw/king_cunningham_code/releases/latest`

Asset name must = `KC_app.zip` exactly. Launcher matches by name.

## Install Directory Layout

```
%LOCALAPPDATA%\King_Cunningham\KC_App\
├── launcher.exe              ← self-installed copy
├── version.txt               ← local version cache
├── KC_app/                   ← extracted from KC_app.zip
│   ├── KC_app.exe
│   ├── _internal/            ← PyInstaller runtime + all DLLs
│   ├── tessdata/             ← OCR lang data
│   └── resources/            ← icons, images
├── KC_app_staging/           ← temp during download (cleaned)
└── KC_app_old/               ← backup during update (cleaned)
```

App config: `%APPDATA%\King_Cunningham\` (separate from install dir).

## Update Mechanism

```
launcher.exe run
  → GET /releases/latest
  → compare tag vs local version.txt
  → newer? prompt user → download KC_app.zip → extract
  → rename old KC_app → KC_app_old
  → rename staging → KC_app
  → delete KC_app_old
  → write new version.txt
  → launch KC_app.exe
```

Atomic-ish: old version preserved as KC_app_old until new version confirmed extracted. Rollback = manual (rename KC_app_old back). See [known-issues.md](known-issues.md) for rollback gap.

## Dependency Chain

```
KC_app.exe
  ├── PyQt6 (GUI)
  ├── PyMuPDF + PyPDF2 (PDF)
  ├── pytesseract → bundled tesseract.exe
  ├── pyzbar (barcodes)
  ├── opencv-python (CV)
  ├── python-docx (Word)
  ├── lxml (XML)
  └── pillow (images)

launcher.exe
  ├── PyQt6 (splash + dialogs)
  ├── requests (GitHub API + download)
  └── pywin32 (COM → Start Menu shortcut)
```

All deps bundled by PyInstaller. No runtime pip install. No system Python needed.

## Key Files

| File | Role |
|---|---|
| `version.txt` | Version source of truth |
| `build.py` | Build orchestrator |
| `KC_app.spec` | PyInstaller config — main app |
| `launcher/launcher.spec` | PyInstaller config — launcher |
| `launcher/launcher.py` | Launcher source |
| `src/main.py` | App entry point |
| `scripts/setup_binaries.py` | Tesseract downloader |
| `scripts/release.ps1` | Release automation |
| `scripts/test-local.ps1` | Local test harness |
| `requirements.txt` | Python deps (build-time) |
