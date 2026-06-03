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
- Sync `__version__` in `src/main.py` + `launcher/launcher.py` ← `version.txt`
- Download Tesseract → `bin/` if missing (first time only)
- Build `dist/KC_app/` via PyInstaller (onedir)
- Zip → `dist/KC_app.zip` + write `.sha256` checksum
- Build `dist/launcher.exe` via PyInstaller
- Write `dist/version.txt`

### 3. Verify

All outputs in `dist/`. Build script prints summary w/ sizes.

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

### Release constraints

Release tag/asset rules the launcher depends on (draft visibility, exact
`KC_app.zip` name, `vX.Y.Z` tag format) → see Distribution in
[installer-updater.md](installer-updater.md). Break them and updates silently fail.

## Binary Deps (bin/)

`bin/` gitignored. Populated by `scripts/setup_binaries.py` at build time.

Pinned:
- **Tesseract OCR** — UB-Mannheim Windows build. Version pinned in `scripts/setup_binaries.py`

Upgrade Tesseract: delete `bin/tesseract/`, update URL in `scripts/setup_binaries.py`, rebuild.

## Build-Time Paths

| Data | Location |
|---|---|
| Build outputs | `dist\` (gitignored) |
| External bins | `bin\` (gitignored) |

Runtime install/config paths on the user machine → [installer-updater.md](installer-updater.md#install-directory-layout).
