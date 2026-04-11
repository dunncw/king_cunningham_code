import glob
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None


def _find_one(pattern: str, label: str) -> str:
    matches = glob.glob(pattern, recursive=True)
    if not matches:
        raise FileNotFoundError(
            f"{label} not found matching '{pattern}'. "
            "Run 'python scripts/setup_binaries.py' first."
        )
    return matches[0]


tesseract_path = _find_one(
    os.path.join("bin", "tesseract", "**", "tesseract.exe"),
    "tesseract.exe",
)
tessdata_path = _find_one(
    os.path.join("bin", "tesseract", "**", "tessdata"),
    "tessdata/",
)

# Collect pyzbar binary and data files
pyzbar_binaries = collect_dynamic_libs('pyzbar')
pyzbar_datas = collect_data_files('pyzbar')

a = Analysis(['src\\main.py'],
             pathex=[os.path.abspath('.')],
             binaries=[(tesseract_path, '.')] + pyzbar_binaries,
             datas=[
                 ('resources', 'resources'),
                 (tessdata_path, 'tessdata'),
                 (tesseract_path, '.'),
             ] + pyzbar_datas,
             hiddenimports=['pyzbar', 'pytesseract'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='KC_app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='resources\\app_icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='KC_app')
