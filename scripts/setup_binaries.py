"""
Populate bin/ with Tesseract OCR binaries needed for the build.

Strategy (in order):
  1. If the target binary already exists in bin/, skip (idempotent).
  2. If a global installation is found (C:\\Program Files\\...), copy it to bin/.
  3. Otherwise, download the installer and run a silent install to bin/.

Run this once before 'python build.py'. No admin rights required if a
global installation is already present.

Pinned installer version (fallback only):
  Tesseract  5.4.0.20240606  (UB-Mannheim Windows build)
"""

import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = REPO_ROOT / "bin"

TESSERACT_INSTALL_DIR = BIN_DIR / "tesseract"

TESSERACT_URL = (
    "https://github.com/UB-Mannheim/tesseract/releases/download/"
    "v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
)

TESSERACT_GLOBAL_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path) -> None:
    print(f"  Downloading {url}")
    print(f"  -> {dest}")

    def progress(block_count, block_size, total_size):
        if total_size > 0:
            pct = min(100, int(block_count * block_size / total_size * 100))
            print(f"\r  {pct}%", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook=progress)
    print()


# ---------------------------------------------------------------------------
# Tesseract
# ---------------------------------------------------------------------------

def install_tesseract() -> None:
    target = TESSERACT_INSTALL_DIR / "tesseract.exe"
    if target.exists():
        print(f"[skip] Tesseract already present at {target}")
        return

    # 1. Copy from existing global install (preferred — no NSIS issues)
    for global_path in TESSERACT_GLOBAL_PATHS:
        if (global_path / "tesseract.exe").exists():
            print(f"[tesseract] Found global install at {global_path}")
            print(f"[tesseract] Copying to {TESSERACT_INSTALL_DIR} ...")
            shutil.copytree(global_path, TESSERACT_INSTALL_DIR, dirs_exist_ok=True)
            print("[tesseract] Done.")
            return

    # 2. Fallback: download and silent-install
    print("[tesseract] No global install found — downloading installer ...")
    TESSERACT_INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    installer = BIN_DIR / "tesseract_setup.exe"
    download_file(TESSERACT_URL, installer)

    print(f"[tesseract] Installing to {TESSERACT_INSTALL_DIR} ...")
    # NSIS: /S = silent, /D= = destination (must be last, must be absolute path)
    subprocess.run(
        [str(installer), "/S", f"/D={TESSERACT_INSTALL_DIR.resolve()}"],
        check=True,
    )
    installer.unlink(missing_ok=True)

    if not target.exists():
        raise RuntimeError(
            f"Tesseract install finished but {target} not found.\n"
            "Check bin/tesseract/ — the installer may have created a subdirectory."
        )
    print(f"[tesseract] Done. ({target})")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> None:
    print("\n--- bin/ summary ---")
    tesseract_exe = TESSERACT_INSTALL_DIR / "tesseract.exe"
    tessdata = list(TESSERACT_INSTALL_DIR.rglob("tessdata"))

    print(f"  tesseract.exe : {'OK  ' + str(tesseract_exe) if tesseract_exe.exists() else 'MISSING'}")
    print(f"  tessdata/     : {'OK  ' + str(tessdata[0]) if tessdata else 'MISSING'}")


if __name__ == "__main__":
    BIN_DIR.mkdir(exist_ok=True)
    try:
        install_tesseract()
        print_summary()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
