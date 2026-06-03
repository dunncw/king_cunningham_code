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

__version__ = "0.0.18"

import ctypes
import hashlib
import os
import shutil
import subprocess
import sys
import winreg
import zipfile
from pathlib import Path

# Suppress console flash from shell-outs in a windowed (PyInstaller --noconsole) build.
CREATE_NO_WINDOW = 0x08000000

import requests
import win32com.client
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QSplashScreen

GITHUB_API = "https://api.github.com/repos/dunncw/king_cunningham_code/releases/latest"
APP_ZIP_NAME = "KC_app.zip"
APP_ZIP_SHA256_NAME = "KC_app.zip.sha256"
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

def _fetch_latest_release() -> tuple[str, str, str | None, str | None]:
    """Return (version, zip_url, sha256_url_or_None, launcher_url_or_None)."""
    resp = requests.get(GITHUB_API, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    tag = data["tag_name"].lstrip("v")
    assets = {a["name"]: a["browser_download_url"] for a in data.get("assets", [])}
    if APP_ZIP_NAME not in assets:
        raise ValueError(
            f"Release {data['tag_name']} has no asset named '{APP_ZIP_NAME}'."
        )
    return (
        tag,
        assets[APP_ZIP_NAME],
        assets.get(APP_ZIP_SHA256_NAME),
        assets.get(LAUNCHER_EXE_NAME),
    )


# ---------------------------------------------------------------------------
# Integrity verification
# ---------------------------------------------------------------------------

def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _fetch_expected_sha256(sha256_url: str) -> str | None:
    """Download .sha256 file, return hex digest or None on failure."""
    try:
        resp = requests.get(sha256_url, timeout=10)
        resp.raise_for_status()
        # Format: "<hex>  <filename>\n"
        return resp.text.strip().split()[0].lower()
    except Exception:
        return None


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

def _rename_retry(src: Path, dst: Path, retries: int = 10, delay: float = 1.0) -> None:
    # WinError 5/32 surface as PermissionError when AV/EDR scans freshly extracted
    # files and holds a transient lock. Retry rides out the scan window.
    import time
    for attempt in range(retries):
        try:
            src.rename(dst)
            return
        except PermissionError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def _install_from_zip(zip_path: Path, version: str) -> None:
    app_dir = INSTALL_DIR / APP_DIR_NAME
    staging_dir = INSTALL_DIR / "KC_app_staging"
    old_dir = INSTALL_DIR / "KC_app_old"

    shutil.rmtree(staging_dir, ignore_errors=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(staging_dir)

    try:
        if app_dir.exists():
            shutil.rmtree(old_dir, ignore_errors=True)
            _rename_retry(app_dir, old_dir)

        _rename_retry(staging_dir, app_dir)
    except PermissionError:
        # Retry exhausted: a lock that never clears (EDR hard-block / Controlled
        # Folder Access). Turn the crash into something the user can act on.
        _show_error(
            "KC Automation Suite — Update Blocked",
            "The update could not be installed because another program is "
            "blocking access to the install folder.\n\n"
            "This is usually antivirus or endpoint security.\n\n"
            "Try:\n"
            "  1. Close KC Automation Suite if it is open, then re-launch.\n"
            "  2. If it keeps failing, ask IT to allow this folder:\n"
            f"     {INSTALL_DIR}",
        )
        sys.exit(1)

    shutil.rmtree(old_dir, ignore_errors=True)

    _write_local_version(version)
    _register_uninstall(version)
    zip_path.unlink(missing_ok=True)


def _cleanup_stale_dirs() -> None:
    for name in ("KC_app_staging", "KC_app_old"):
        shutil.rmtree(INSTALL_DIR / name, ignore_errors=True)


# ---------------------------------------------------------------------------
# Shortcut creation via pywin32 COM
# ---------------------------------------------------------------------------

def _shortcut_path() -> Path:
    return (
        Path(os.environ["APPDATA"])
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "KC Automation Suite.lnk"
    )


def _create_start_menu_shortcut(target_exe: Path) -> None:
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(_shortcut_path()))
    shortcut.TargetPath = str(target_exe)
    shortcut.WorkingDirectory = str(target_exe.parent)
    shortcut.IconLocation = str(target_exe)
    shortcut.Description = "KC Automation Suite"
    shortcut.save()


# ---------------------------------------------------------------------------
# Add/Remove Programs registration (per-user, no admin needed)
# ---------------------------------------------------------------------------

_UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\KCAutomationSuite"


def _register_uninstall(version: str) -> None:
    launcher_exe = INSTALL_DIR / LAUNCHER_EXE_NAME
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _UNINSTALL_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "KC Automation Suite")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, version)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "King & Cunningham")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(INSTALL_DIR))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(launcher_exe))
            winreg.SetValueEx(
                key, "UninstallString", 0, winreg.REG_SZ, f'"{launcher_exe}" --uninstall'
            )
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except OSError:
        pass  # Registration is best-effort; never block install on it.


def _unregister_uninstall() -> None:
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _UNINSTALL_KEY)
    except OSError:
        pass


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

    _register_uninstall(__version__)

    splash.close()
    subprocess.Popen([str(installed_exe)])
    sys.exit(0)


# ---------------------------------------------------------------------------
# Launcher self-update
# ---------------------------------------------------------------------------

def _self_update(splash: QSplashScreen, latest_version: str, launcher_url: str) -> None:
    """Download new launcher, rename-self, swap, re-launch."""
    installed_exe = INSTALL_DIR / LAUNCHER_EXE_NAME
    old_exe = INSTALL_DIR / "launcher.old.exe"
    tmp_exe = INSTALL_DIR / "launcher.new.exe"

    _splash_msg(splash, "Updating launcher...")
    try:
        resp = requests.get(launcher_url, timeout=60)
        resp.raise_for_status()
        tmp_exe.write_bytes(resp.content)
    except Exception:
        tmp_exe.unlink(missing_ok=True)
        return

    try:
        old_exe.unlink(missing_ok=True)
        _rename_retry(installed_exe, old_exe)
        _rename_retry(tmp_exe, installed_exe)
    except OSError:
        tmp_exe.unlink(missing_ok=True)
        return

    splash.close()
    subprocess.Popen([str(installed_exe)])
    sys.exit(0)


def _cleanup_old_launcher() -> None:
    old = INSTALL_DIR / "launcher.old.exe"
    old.unlink(missing_ok=True)


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
# Running-process detection (update path only)
# ---------------------------------------------------------------------------

def _app_is_running() -> bool:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {APP_EXE_NAME}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
        return APP_EXE_NAME.lower() in out.stdout.lower()
    except Exception:
        return False  # If we can't tell, don't block the update.


def _wait_for_app_close() -> bool:
    """Block update until KC_app.exe is gone. Return False if user cancels."""
    while _app_is_running():
        reply = QMessageBox.warning(
            None,
            "KC Automation Suite — Close Required",
            "KC Automation Suite is currently running and must be closed "
            "before updating.\n\nPlease close it, then click Retry.",
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Retry,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
    return True


# ---------------------------------------------------------------------------
# Uninstall flow (--uninstall)
# ---------------------------------------------------------------------------

def _self_delete_launcher() -> None:
    # A running exe can't delete itself; defer to a detached shell that waits,
    # then removes the launcher (and its parent dir if now empty).
    # ping (not timeout) for the delay: timeout needs console stdin, which a
    # DETACHED_PROCESS lacks, so it would error out instantly and del would
    # fire while this exe is still locked.
    launcher_exe = INSTALL_DIR / LAUNCHER_EXE_NAME
    old_exe = INSTALL_DIR / "launcher.old.exe"
    cmd = (
        f'ping 127.0.0.1 -n 3 >nul & del /f /q "{launcher_exe}" '
        f'& del /f /q "{old_exe}" & rmdir "{INSTALL_DIR}" '
        f'& rmdir "{INSTALL_DIR.parent}"'
    )
    subprocess.Popen(
        ["cmd", "/c", cmd],
        creationflags=CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    )


def _uninstall() -> None:
    reply = QMessageBox.question(
        None,
        "Uninstall KC Automation Suite",
        "Remove KC Automation Suite from this computer?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    if reply != QMessageBox.StandardButton.Yes:
        sys.exit(0)

    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", APP_EXE_NAME],
            capture_output=True,
            creationflags=CREATE_NO_WINDOW,
        )
    except Exception:
        pass

    for name in (APP_DIR_NAME, "KC_app_staging", "KC_app_old"):
        shutil.rmtree(INSTALL_DIR / name, ignore_errors=True)
    (INSTALL_DIR / VERSION_FILE_NAME).unlink(missing_ok=True)
    _shortcut_path().unlink(missing_ok=True)
    _unregister_uninstall()

    QMessageBox.information(
        None,
        "KC Automation Suite",
        "KC Automation Suite has been uninstalled.",
    )
    _self_delete_launcher()
    sys.exit(0)


# ---------------------------------------------------------------------------
# Main launcher logic
# ---------------------------------------------------------------------------

def run(splash: QSplashScreen) -> None:
    _cleanup_stale_dirs()
    _cleanup_old_launcher()

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
        latest_version, download_url, sha256_url, launcher_url = _fetch_latest_release()
    except Exception as exc:
        if app_exe.exists():
            _launch_app(splash, app_exe)
        else:
            splash.close()
            _show_error("KC Automation Suite — Network Error", f"Could not reach GitHub.\n\n{exc}")
            sys.exit(1)
        return

    if launcher_url and _is_newer(__version__, latest_version):
        _self_update(splash, latest_version, launcher_url)

    local_version = _read_local_version()

    expected_hash = None
    if sha256_url:
        expected_hash = _fetch_expected_sha256(sha256_url)

    if not app_exe.exists():
        splash.close()
        tmp = INSTALL_DIR / f"{APP_ZIP_NAME}.tmp"
        ok = _download(download_url, tmp, f"Downloading KC Automation Suite v{latest_version}...")
        if not ok:
            tmp.unlink(missing_ok=True)
            sys.exit(0)
        if expected_hash:
            actual = _sha256_of(tmp)
            if actual != expected_hash:
                tmp.unlink(missing_ok=True)
                _show_error(
                    "KC Automation Suite — Integrity Error",
                    f"Download integrity check failed.\n\n"
                    f"Expected: {expected_hash}\nGot: {actual}\n\n"
                    "The file may be corrupted or tampered with. Try again later.",
                )
                sys.exit(1)
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
                if expected_hash:
                    actual = _sha256_of(tmp)
                    if actual != expected_hash:
                        tmp.unlink(missing_ok=True)
                        _show_error(
                            "KC Automation Suite — Integrity Error",
                            f"Download integrity check failed.\n\n"
                            f"Expected: {expected_hash}\nGot: {actual}\n\n"
                            "The file may be corrupted or tampered with. Try again later.",
                        )
                        sys.exit(1)
                if not _wait_for_app_close():
                    tmp.unlink(missing_ok=True)
                    _launch_app(splash, app_exe)
                    return
                splash.show()
                _splash_msg(splash, "Installing update...")
                _install_from_zip(tmp, latest_version)
            else:
                tmp.unlink(missing_ok=True)

    _launch_app(splash, app_exe)


def main() -> None:
    try:
        app = QApplication(sys.argv)

        if "--uninstall" in sys.argv:
            _uninstall()
            return

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
