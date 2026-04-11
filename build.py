import os
import re
import subprocess
import sys
import zipfile
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
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "setup_binaries.py")],
            check=True,
        )
    else:
        print("[binaries] bin/ already populated, skipping download.")


def build_main_app() -> None:
    print("\n[build] Building KC_app (onedir) ...")
    subprocess.run(
        ["pyinstaller", "KC_app.spec", "--clean", "-y"],
        check=True,
        cwd=str(REPO_ROOT),
    )


def zip_onedir_output() -> Path:
    onedir = REPO_ROOT / "dist" / "KC_app"
    zippath = REPO_ROOT / "dist" / "KC_app.zip"
    if not onedir.is_dir():
        raise FileNotFoundError(f"Expected onedir output at {onedir}")
    print(f"\n[zip] Packaging {onedir} -> {zippath} ...")
    with zipfile.ZipFile(zippath, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(onedir):
            for f in files:
                filepath = Path(root) / f
                arcname = filepath.relative_to(onedir)
                zf.write(filepath, arcname)
    size_mb = zippath.stat().st_size // (1024 * 1024)
    print(f"[zip] Done. ({size_mb} MB)")
    return zippath


def build_launcher() -> None:
    print("\n[build] Building launcher.exe ...")
    subprocess.run(
        ["pyinstaller", str(REPO_ROOT / "launcher" / "launcher.spec"), "--clean", "-y"],
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
    zip_onedir_output()
    build_launcher()
    copy_version_to_dist(version)

    print("\nBuild complete. Outputs in dist/:")
    for name in ["KC_app/KC_app.exe", "KC_app.zip", "launcher.exe", "version.txt"]:
        p = REPO_ROOT / "dist" / name
        if p.exists():
            size_mb = p.stat().st_size // (1024 * 1024)
            print(f"  {name:25s} {size_mb} MB")
        else:
            print(f"  {name:25s} MISSING")


if __name__ == "__main__":
    main()
