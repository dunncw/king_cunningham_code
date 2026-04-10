# KC_app

Desktop automation suite for King & Cunningham. Modules cover Simplifile3 document recording, PT-61 form generation, document OCR processing, court records gathering (CRG), SCRA lookup, and PACER access.

## Installation (end users)

1. Download `launcher.exe` from the [latest release](https://github.com/dunncw/king_cunningham_code/releases/latest).
2. Double-click `launcher.exe` from anywhere (e.g. your Downloads folder).
3. The launcher installs itself to `%LOCALAPPDATA%\King_Cunningham\KC_App\`, creates a Start Menu shortcut ("KC App"), downloads `KC_app.exe`, and launches it.

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
cd King_app
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

Tesseract OCR and Ghostscript are not committed to the repo. Run the setup script to download and install pinned versions into `bin\`:

```
python scripts\setup_binaries.py
```

This is idempotent — re-running it skips anything already present. After it finishes, confirm the summary shows both `tesseract.exe` and `gswin64c.exe` as OK before proceeding.

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
- Builds `dist\KC_app.exe` (~171 MB) via PyInstaller
- Builds `dist\launcher.exe` via PyInstaller
- Writes `dist\version.txt`

### 7. Verify outputs

```
dist\
  KC_app.exe      ~171 MB
  launcher.exe    ~50-80 MB
  version.txt
```

---

## Creating a Release

```bash
# 1. Bump version.txt and build (steps 5-6 above)

# 2. Commit and tag
git add version.txt src/main.py
git commit -m "chore: bump to 0.0.14"
git tag v0.0.14
git push origin dev --tags

# 3. Publish release — uploads KC_app.exe as the release asset
gh release create v0.0.14 dist/KC_app.exe --title "v0.0.14"
```

Users with the launcher will receive the update automatically on their next launch.

> The launcher identifies the download by finding a release asset named exactly `KC_app.exe`.
> Do not rename the asset.

---

## Dependencies

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [Ghostscript](https://www.ghostscript.com/)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [OpenCV](https://opencv.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

Refer to each project's license for terms of use.
