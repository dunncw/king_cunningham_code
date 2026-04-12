# KC Automation Suite

Desktop automation tools for King & Cunningham.

**Modules:** Simplifile3 recording, PT-61 forms, document OCR, court records (CRG), SCRA lookup, PACER access.

## Install

1. Download `launcher.exe` from [latest release](https://github.com/dunncw/king_cunningham_code/releases/latest)
2. Double-click it — works from any folder (Downloads, Desktop, wherever)
3. Done. Launcher handles everything:
   - Installs to `%LOCALAPPDATA%\King_Cunningham\KC_App\`
   - Creates Start Menu shortcut ("KC Automation Suite")
   - Downloads app files and launches

**After first install:** use Start Menu shortcut. Updates happen automatically on launch.

### Requirements

- Windows 10+
- Internet on first run

---

## Build from Source

### Prerequisites

- Windows 10+
- Python 3.8+
- Git

### Setup

```
git clone https://github.com/dunncw/king_cunningham_code.git
cd king_cunningham_code
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### External binaries (first time)

Tesseract OCR not in repo. Download pinned version:

```
python scripts\setup_binaries.py
```

Safe to re-run — skips what's already there.

### Build

Set version in `version.txt`, then:

```
python build.py
```

Build script handles:
- Syncs `__version__` in `src/main.py` from `version.txt`
- Runs `setup_binaries.py` if `bin\` empty
- PyInstaller onedir build → `dist\KC_app\`
- Zips to `dist\KC_app.zip`
- Builds `dist\launcher.exe`
- Writes `dist\version.txt`

### Output

```
dist\
  KC_app\           KC_app.exe + DLLs
  KC_app.zip        release asset
  launcher.exe      ~37 MB
  version.txt
```

---

## Dependencies

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF)
- [OpenCV](https://opencv.org/)
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)

See each project's license for terms.
