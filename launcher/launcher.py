r"""
KC Automation Suite Launcher

On the first run from an arbitrary location this script installs itself to
  %LOCALAPPDATA%\King_Cunningham\KC_App\launcher.exe
creates a Start Menu shortcut, then re-launches from the installed path.

On every subsequent run it:
  1. Shows a splash screen immediately.
  2. Cleans up any stale staging directories from previous updates.
  3. Reads the installed version from version.txt in its own directory.
  4. Queries the GitHub Releases API for the latest release.
  5. If a newer version is available, prompts the user and downloads KC_app.zip.
  6. Extracts the zip into a KC_app/ subdirectory.
  7. Launches KC_app/KC_app.exe from the install directory and exits.

Set KC_LAUNCHER_SKIP_UPDATE=1 to bypass the GitHub check (local testing).
"""

import ctypes
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import requests
import win32com.client
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QSplashScreen

GITHUB_API = "https://api.github.com/repos/dunncw/king_cunningham_code/releases/latest"
APP_ZIP_NAME = "KC_app.zip"
APP_DIR_NAME = "KC_app"
APP_EXE_NAME = "KC_app.exe"
LAUNCHER_EXE_NAME = "launcher.exe"
VERSION_FILE_NAME = "version.txt"

INSTALL_DIR = Path(os.environ["LOCALAPPDATA"]) / "King_Cunningham" / "KC_App"


def _resource_path(relative: str) -> str:
    base = getattr(sys, "_MEIPASS", None) or os.path.join(os.path.dirname(__file__), "..")
    return os.path.join(base, relative)


# ---------------------------------------------------------------------------
# Splash screen
# ---------------------------------------------------------------------------

def _make_splash() -> QSplashScreen:
    img_path = _resource_path(os.path.join("resources", "splash_image.png"))
    if os.path.exists(img_path):
        pixmap = QPixmap(img_path)
    else:
        pixmap = QPixmap(480, 280)
        pixmap.fill(QColor("#000000"))

    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    splash.show()
    return splash


def _splash_msg(splash: QSplashScreen, msg: str) -> None:
    splash.showMessage(
        msg,
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
        Qt.GlobalColor.white,
    )
    QApplication.processEvents()


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def _parse_version(v: str) -> tuple:
    return tuple(int(x) for x in v.strip().lstrip("v").split("."))


def _is_newer(current: str, candidate: str) -> bool:
    try:
        return _parse_version(candidate) > _parse_version(current)
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def _fetch_latest_release() -> tuple[str, str]:
    resp = requests.get(GITHUB_API, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    tag = data["tag_name"].lstrip("v")
    asset = next(
        (a for a in data.get("assets", []) if a["name"] == APP_ZIP_NAME),
        None,
    )
    if asset is None:
        raise ValueError(
            f"Release {data['tag_name']} has no asset named '{APP_ZIP_NAME}'."
        )
    return tag, asset["browser_download_url"]


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

def _download(url: str, dest: Path, label: str) -> bool:
    progress = QProgressDialog(label, "Cancel", 0, 100)
    progress.setWindowTitle("KC Automation Suite")
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumDuration(0)
    progress.setMinimumWidth(400)
    progress.setValue(0)
    QApplication.processEvents()

    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=65536):
                if progress.wasCanceled():
                    return False
                fh.write(chunk)
                downloaded += len(chunk)
                if total:
                    progress.setValue(int(downloaded / total * 100))
                QApplication.processEvents()
    finally:
        progress.close()

    return True


# ---------------------------------------------------------------------------
# Zip extraction and install
# ---------------------------------------------------------------------------

def _install_from_zip(zip_path: Path, version: str) -> None:
    app_dir = INSTALL_DIR / APP_DIR_NAME
    staging_dir = INSTALL_DIR / "KC_app_staging"
    old_dir = INSTALL_DIR / "KC_app_old"

    shutil.rmtree(staging_dir, ignore_errors=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(staging_dir)

    if app_dir.exists():
        shutil.rmtree(old_dir, ignore_errors=True)
        app_dir.rename(old_dir)

    staging_dir.rename(app_dir)
    shutil.rmtree(old_dir, ignore_errors=True)

    _write_local_version(version)
    zip_path.unlink(missing_ok=True)


def _cleanup_stale_dirs() -> None:
    for name in ("KC_app_staging", "KC_app_old"):
        shutil.rmtree(INSTALL_DIR / name, ignore_errors=True)


# ---------------------------------------------------------------------------
# Shortcut creation via pywin32 COM
# ---------------------------------------------------------------------------

def _create_start_menu_shortcut(target_exe: Path) -> None:
    programs_dir = (
        Path(os.environ["APPDATA"])
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
    )
    shortcut_path = programs_dir / "KC Automation Suite.lnk"

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = str(target_exe)
    shortcut.WorkingDirectory = str(target_exe.parent)
    shortcut.IconLocation = str(target_exe)
    shortcut.Description = "KC Automation Suite"
    shortcut.save()


# ---------------------------------------------------------------------------
# Self-install logic
# ---------------------------------------------------------------------------

def _needs_install() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    current_exe = Path(sys.executable).resolve()
    installed_exe = (INSTALL_DIR / LAUNCHER_EXE_NAME).resolve()
    return current_exe != installed_exe


def _self_install(splash: QSplashScreen) -> None:
    _splash_msg(splash, "Installing KC Automation Suite...")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    installed_exe = INSTALL_DIR / LAUNCHER_EXE_NAME
    shutil.copy2(sys.executable, installed_exe)

    _splash_msg(splash, "Creating Start Menu shortcut...")
    try:
        _create_start_menu_shortcut(installed_exe)
    except Exception as exc:
        QMessageBox.warning(
            None,
            "KC Automation Suite — Shortcut Warning",
            f"Could not create Start Menu shortcut:\n\n{exc}",
        )

    splash.close()
    subprocess.Popen([str(installed_exe)])
    sys.exit(0)


# ---------------------------------------------------------------------------
# Version file helpers
# ---------------------------------------------------------------------------

def _read_local_version() -> str:
    version_file = INSTALL_DIR / VERSION_FILE_NAME
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"


def _write_local_version(version: str) -> None:
    (INSTALL_DIR / VERSION_FILE_NAME).write_text(version + "\n", encoding="utf-8")


def _show_error(title: str, message: str) -> None:
    QMessageBox.critical(None, title, message)


_LOG_PATH = Path(os.environ.get("TEMP", ".")) / "kc_launcher_error.log"


# ---------------------------------------------------------------------------
# App launch
# ---------------------------------------------------------------------------

def _grant_foreground_to(pid: int) -> None:
    try:
        ctypes.windll.user32.AllowSetForegroundWindow(pid)
    except Exception:
        pass


def _launch_app(splash: QSplashScreen, app_exe: Path) -> None:
    proc = subprocess.Popen([str(app_exe)], cwd=str(app_exe.parent))
    _grant_foreground_to(proc.pid)
    splash.close()
    sys.exit(0)


# ---------------------------------------------------------------------------
# Main launcher logic
# ---------------------------------------------------------------------------

def run(splash: QSplashScreen) -> None:
    _cleanup_stale_dirs()

    app_exe = INSTALL_DIR / APP_DIR_NAME / APP_EXE_NAME

    if os.environ.get("KC_LAUNCHER_SKIP_UPDATE"):
        if not app_exe.exists():
            splash.close()
            _show_error("KC Automation Suite", f"{APP_EXE_NAME} not found in {INSTALL_DIR / APP_DIR_NAME}.")
            sys.exit(1)
        _launch_app(splash, app_exe)
        return

    _splash_msg(splash, "Checking for updates...")
    try:
        latest_version, download_url = _fetch_latest_release()
    except Exception as exc:
        if app_exe.exists():
            _launch_app(splash, app_exe)
        else:
            splash.close()
            _show_error("KC Automation Suite — Network Error", f"Could not reach GitHub.\n\n{exc}")
            sys.exit(1)
        return

    local_version = _read_local_version()

    if not app_exe.exists():
        splash.close()
        tmp = INSTALL_DIR / f"{APP_ZIP_NAME}.tmp"
        ok = _download(download_url, tmp, f"Downloading KC Automation Suite v{latest_version}...")
        if not ok:
            tmp.unlink(missing_ok=True)
            sys.exit(0)
        _install_from_zip(tmp, latest_version)
    elif _is_newer(local_version, latest_version):
        splash.close()
        reply = QMessageBox.question(
            None,
            "KC Automation Suite — Update Available",
            f"Version {latest_version} is available (you have {local_version}).\n\nUpdate now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            tmp = INSTALL_DIR / f"{APP_ZIP_NAME}.tmp"
            ok = _download(download_url, tmp, f"Downloading KC Automation Suite v{latest_version}...")
            if ok:
                splash.show()
                _splash_msg(splash, "Installing update...")
                _install_from_zip(tmp, latest_version)
            else:
                tmp.unlink(missing_ok=True)

    _launch_app(splash, app_exe)


def main() -> None:
    try:
        app = QApplication(sys.argv)
        splash = _make_splash()

        if _needs_install():
            _self_install(splash)
            return

        run(splash)
    except Exception:
        import traceback
        from datetime import datetime
        entry = f"\n--- {datetime.now().isoformat()} ---\n{traceback.format_exc()}"
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(entry)
        raise


if __name__ == "__main__":
    main()
