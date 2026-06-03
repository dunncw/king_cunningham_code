# Installer + Updater

Single source of truth for how the app installs, updates, and reaches users.
`launcher.exe` is both the installer and the updater. Build/release steps live
in [build.md](build.md); open bugs in [known-issues.md](known-issues.md).

## Two-EXE Model

```
launcher.exe (~40 MB)     KC_app.zip (~180 MB)
   onefile EXE               onedir ZIP
   self-contained             downloaded on demand
   user keeps forever         replaced each update
```

Why two: launcher = small, fast download for new users. App = big, only pulled
when needed/updated. Decoupled → launcher bugs fixable without rebuilding app,
and the launcher self-updates (see Update Mechanism).

| Component | PyInstaller mode | Why |
|---|---|---|
| KC_app | onedir | Fast startup, no temp extraction, DLLs load direct |
| launcher | onefile | Single portable EXE. Runs once → launches app, startup speed irrelevant |

Onedir = `KC_app.exe` + `_internal/` (DLLs + Python runtime). Onefile = one EXE,
extracted to temp at runtime.

## Distribution

GitHub Releases only. No app store, website, or CDN.

Launcher fetches: `api.github.com/repos/dunncw/king_cunningham_code/releases/latest`

Constraints (break these → updates silently fail):

- Only published, non-draft, non-prerelease releases are visible to `/releases/latest`
- Asset name must equal `KC_app.zip` exactly — launcher matches by name
- Version tags must be `vX.Y.Z` — launcher strips `v`, splits on `.`, tuple-compares.
  No dashes or extra dots (`v0.0.13.1` → ValueError → update silently skipped)

New users only need `launcher.exe` — hand it over once (email, Slack, USB, release page).

## First-Time Install

What the user sees:

1. Double-click `launcher.exe`
2. Windows SmartScreen: "Windows protected your PC" → "More info" → "Run anyway"
   (unsigned EXE warns once per machine; Windows remembers after)
3. Splash screen → "Installing..." → "Creating Start Menu shortcut..." → "Checking for updates..."
4. Progress dialog: "Downloading KC Automation Suite vX.Y.Z..." (progress bar + cancel)
5. App launches full-screen (PyQt6 main window)

Under the hood:

```
launcher.exe (from Downloads/)
  → detect not in install dir
  → copy self → %LOCALAPPDATA%\King_Cunningham\KC_App\launcher.exe
  → create Start Menu shortcut → installed launcher.exe
  → re-launch from installed location
  → no local version.txt → version = "0.0.0"
  → fetch /releases/latest → download KC_app.zip → extract
  → write version.txt → launch KC_app.exe → exit launcher
```

Time: ~30-60s depending on download speed (~180 MB zip).

## Subsequent Launches

Entry point: "KC Automation Suite" from Start Menu (or re-run installed `launcher.exe`).

| Case | Flow |
|---|---|
| No update | Splash (<2s) → app launches |
| Update available | Splash → dialog "Version X.Y.Z available (you have A.B.C). Update now?" → Yes: progress → install → launch / No: launch current |
| Network down, app installed | GitHub API fails → silently skip update check → launch current |
| Network down, no app | Error dialog with exception → exit |

## Update Mechanism

```
launcher.exe run
  → GET /releases/latest
  → compare tag vs local version.txt
  → newer? prompt user → download KC_app.zip → verify SHA-256 → extract to staging
  → rename old KC_app → KC_app_old
  → rename staging → KC_app
  → on extract failure: rename KC_app_old back (rollback)
  → delete KC_app_old → write new version.txt → launch KC_app.exe
```

Old version preserved as `KC_app_old` until new version confirmed extracted.
Download integrity checked against the release's `KC_app.zip.sha256` asset.

### Launcher self-update

`__version__` in `launcher.py` (synced by build.py) is compared against the
release tag. If newer → download new `launcher.exe` from the release asset,
rename-self → `launcher.old.exe`, swap in new, re-launch. Old cleaned up next
start. If the release has no launcher asset or download fails → skip silently.

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

App config lives separately at `%APPDATA%\King_Cunningham\`.
Crash log: `%TEMP%\kc_launcher_error.log`.

## Version Flow

```
version.txt (source of truth)
     ├──→ build.py syncs → src/main.py + launcher/launcher.py __version__
     ├──→ build.py copies → dist/version.txt
     ├──→ release.ps1 → git tag vX.Y.Z
     └──→ launcher writes → %LOCALAPPDATA%\..\version.txt (local install)
```

Comparison: launcher reads local version.txt → compares vs GitHub
`/releases/latest` tag_name → tuple comparison `(0,0,15) > (0,0,14)`.

## Start Menu Entry

- Name: "KC Automation Suite"
- Location: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk`
- Target: installed `launcher.exe` — icon from `app_icon.ico` baked into the EXE
- Searchable via Windows search, pinnable to taskbar

## Uninstall

No uninstaller, no Add/Remove Programs entry. Manual:

1. Delete `%LOCALAPPDATA%\King_Cunningham\` (install dir)
2. Delete `%APPDATA%\King_Cunningham\` (config dir)
3. Delete `%APPDATA%\Microsoft\Windows\Start Menu\Programs\KC Automation Suite.lnk`

## Error Handling — What User Sees

| Scenario | UX |
|---|---|
| Network down, app installed | App launches normally (silent skip) |
| Network down, no app | Error dialog with exception text |
| Download cancelled | App exits cleanly |
| Download fails mid-stream | Partial .tmp cleaned up; old version launches if present |
| Launcher crash | Generic Windows error; log → `%TEMP%\kc_launcher_error.log` |
| App crash | PyQt error dialog with full traceback |
| Corrupt zip | SHA-256 mismatch or extraction fails → old version launches |

## Dependency Chain

```
KC_app.exe
  ├── PyQt6 (GUI)
  ├── PyMuPDF + pypdf (PDF)
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

All deps bundled by PyInstaller. No runtime pip install, no system Python needed.

## Known Gaps + Pain Points

Tracked in [known-issues.md](known-issues.md): no code signing (SmartScreen),
full ~180 MB downloads (no delta), no Add/Remove Programs entry, double splash
on first install.
