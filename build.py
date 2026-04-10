import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def read_version() -> str:
    version_file = REPO_ROOT / "version.txt"
    if not version_file.exists():
        raise FileNotFoundError("version.txt not found at repo root.")
    return version_file.read_text(encoding="utf-8").strip()


def sync_version_in_source(version: str) -> None:
    main_py = REPO_ROOT / "src" / "main.py"
    content = main_py.read_text(encoding="utf-8")
    updated = re.sub(
        r'^__version__ = ".*?"',
        f'__version__ = "{version}"',
        content,
        flags=re.MULTILINE,
    )
    if updated != content:
        main_py.write_text(updated, encoding="utf-8")
        print(f"[version] src/main.py __version__ updated to {version}")
    else:
        print(f"[version] src/main.py already at {version}")


def ensure_binaries() -> None:
    tesseract_exe = REPO_ROOT / "bin" / "tesseract" / "tesseract.exe"
    if not tesseract_exe.exists():
        print("[binaries] bin/tesseract/tesseract.exe missing — running setup_binaries.py ...")
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "setup_binaries.py")],
            check=True,
        )
    else:
        print("[binaries] bin/ already populated, skipping download.")


def build_main_app() -> None:
    print("\n[build] Building KC_app.exe ...")
    subprocess.run(
        ["pyinstaller", "KC_app.spec", "--clean"],
        check=True,
        cwd=str(REPO_ROOT),
    )


def build_launcher() -> None:
    print("\n[build] Building launcher.exe ...")
    subprocess.run(
        ["pyinstaller", str(REPO_ROOT / "launcher" / "launcher.spec"), "--clean"],
        check=True,
        cwd=str(REPO_ROOT),
    )


def copy_version_to_dist(version: str) -> None:
    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    dest = dist_dir / "version.txt"
    dest.write_text(version + "\n", encoding="utf-8")
    print(f"[dist] version.txt written ({version})")


def main() -> None:
    version = read_version()
    print(f"[version] Building version {version}")

    sync_version_in_source(version)
    ensure_binaries()
    build_main_app()
    build_launcher()
    copy_version_to_dist(version)

    print("\nBuild complete. Outputs in dist/:")
    for name in ["KC_app.exe", "launcher.exe", "version.txt"]:
        p = REPO_ROOT / "dist" / name
        status = f"{p.stat().st_size // (1024*1024)} MB" if p.exists() else "MISSING"
        print(f"  {name:20s} {status}")


if __name__ == "__main__":
    main()
