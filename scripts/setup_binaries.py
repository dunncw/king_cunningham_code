"""
Populate bin/ with Tesseract OCR and Ghostscript binaries needed for the build.

Strategy (in order):
  1. If the target binary already exists in bin/, skip (idempotent).
  2. If a global installation is found (C:\\Program Files\\...), copy it to bin/.
  3. Otherwise, download the installer and run a silent install to bin/.

Run this once before 'python build.py'. No admin rights required if a
global installation is already present.

Pinned installer versions (fallback only):
  Tesseract  5.4.0.20240606  (UB-Mannheim Windows build)
  Ghostscript 10.04.0        (ArtifexSoftware release)
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
GHOSTSCRIPT_INSTALL_DIR = BIN_DIR / "ghostscript"

TESSERACT_URL = (
    "https://github.com/UB-Mannheim/tesseract/releases/download/"
    "v5.4.0.20240606/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
)
GHOSTSCRIPT_URL = (
    "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/"
    "gs10040/gs10040w64.exe"
)

TESSERACT_GLOBAL_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR"),
]

GHOSTSCRIPT_GLOBAL_BASE = Path(r"C:\Program Files\gs")


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
# Ghostscript
# ---------------------------------------------------------------------------

def install_ghostscript() -> None:
    matches = list(GHOSTSCRIPT_INSTALL_DIR.rglob("gswin64c.exe"))
    if matches:
        print(f"[skip] Ghostscript already present at {matches[0]}")
        return

    # 1. Copy from existing global install
    if GHOSTSCRIPT_GLOBAL_BASE.exists():
        for ver_dir in sorted(GHOSTSCRIPT_GLOBAL_BASE.iterdir(), reverse=True):
            gs_exe = ver_dir / "bin" / "gswin64c.exe"
            if gs_exe.exists():
                print(f"[ghostscript] Found global install at {ver_dir}")
                print(f"[ghostscript] Copying to {GHOSTSCRIPT_INSTALL_DIR} ...")
                shutil.copytree(ver_dir, GHOSTSCRIPT_INSTALL_DIR, dirs_exist_ok=True)
                print("[ghostscript] Done.")
                return

    # 2. Fallback: download and silent-install
    print("[ghostscript] No global install found — downloading installer ...")
    GHOSTSCRIPT_INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    installer = BIN_DIR / "ghostscript_setup.exe"
    download_file(GHOSTSCRIPT_URL, installer)

    print(f"[ghostscript] Installing to {GHOSTSCRIPT_INSTALL_DIR} ...")
    subprocess.run(
        [
            str(installer),
            "/VERYSILENT",
            "/SP-",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            f"/DIR={GHOSTSCRIPT_INSTALL_DIR.resolve()}",
        ],
        check=True,
    )
    installer.unlink(missing_ok=True)

    matches = list(GHOSTSCRIPT_INSTALL_DIR.rglob("gswin64c.exe"))
    if not matches:
        raise RuntimeError(
            f"Ghostscript install finished but gswin64c.exe not found under "
            f"{GHOSTSCRIPT_INSTALL_DIR}."
        )
    print(f"[ghostscript] Done. ({matches[0]})")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary() -> None:
    print("\n--- bin/ summary ---")
    tesseract_exe = TESSERACT_INSTALL_DIR / "tesseract.exe"
    gs_matches = list(GHOSTSCRIPT_INSTALL_DIR.rglob("gswin64c.exe"))
    tessdata = list(TESSERACT_INSTALL_DIR.rglob("tessdata"))

    print(f"  tesseract.exe : {'OK  ' + str(tesseract_exe) if tesseract_exe.exists() else 'MISSING'}")
    print(f"  gswin64c.exe  : {'OK  ' + str(gs_matches[0]) if gs_matches else 'MISSING'}")
    print(f"  tessdata/     : {'OK  ' + str(tessdata[0]) if tessdata else 'MISSING'}")


if __name__ == "__main__":
    BIN_DIR.mkdir(exist_ok=True)
    try:
        install_tesseract()
        install_ghostscript()
        print_summary()
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
