# KC Automation Suite

Desktop automation suite for King & Cunningham. Modules cover Simplifile3 document recording, PT-61 form generation, document OCR processing, court records gathering (CRG), SCRA lookup, and PACER access.

## Installation (end users)

1. Download `launcher.exe` from the [latest release](https://github.com/dunncw/king_cunningham_code/releases/latest).
2. Double-click `launcher.exe` from anywhere (e.g. your Downloads folder).
3. The launcher installs itself to `%LOCALAPPDATA%\King_Cunningham\KC_App\`, creates a Start Menu shortcut ("KC Automation Suite"), downloads and extracts `KC_app.zip`, and launches the app.

From that point on, open the app via the Start Menu shortcut. The launcher checks for updates automatically on each run.

## Requirements

- Windows 10 or later
- Internet access on first run (to download the application)

---

## Building from Source

### Prerequisites

- Windows 10 or later
- Python 3.8 or later
- Git

### 1. Clone the repository

```
git clone https://github.com/dunncw/king_cunningham_code.git
cd king_cunningham_code
```

### 2. Create and activate a virtual environment

```
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Download external binaries (first time only)

Tesseract OCR is not committed to the repo. Run the setup script to download and install the pinned version into `bin\`:

```
python scripts\setup_binaries.py
```

This is idempotent -- re-running it skips anything already present.

### 5. Set the version

Edit `version.txt` at the repo root to the version you want to build:

```
0.0.14
```

### 6. Build

```
python build.py
```

The build script:
- Syncs `__version__` in `src/main.py` from `version.txt`
- Runs `setup_binaries.py` automatically if `bin\` is not populated
- Builds `dist\KC_app\` directory via PyInstaller (onedir mode)
- Zips the directory into `dist\KC_app.zip`
- Builds `dist\launcher.exe` via PyInstaller
- Writes `dist\version.txt`

### 7. Verify outputs

```
dist\
  KC_app\           (onedir output with KC_app.exe + DLLs)
  KC_app.zip        (zipped release asset)
  launcher.exe      (~37 MB)
  version.txt
```

---

## Creating a Release

```bash
# 1. Bump version.txt and build (steps 5-6 above)

# 2. Commit, merge to main, tag, push
git add version.txt src/main.py
git commit -m "chore: bump to 0.0.15"
# merge feature branch -> dev -> main (standard branch workflow)
git checkout main && git merge dev
git tag v0.0.15
git push origin main --tags

# 3. Publish release -- include the zip
gh release create v0.0.15 dist/KC_app.zip --title "v0.0.15"
```

Users with an existing launcher receive the update automatically on next launch.
New users download `launcher.exe` once -- it self-installs and handles all future updates.

> The launcher identifies the update asset by the name `KC_app.zip` exactly.
> Do not rename that asset.

---

## Dependencies

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [OpenCV](https://opencv.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

Refer to each project's license for terms of use.
