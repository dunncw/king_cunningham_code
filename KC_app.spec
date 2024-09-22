import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Add the path to Tesseract executable
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path
if not os.path.exists(tesseract_path):
    raise FileNotFoundError(f"Tesseract executable not found at {tesseract_path}")

# Add the path to Ghostscript executable
ghostscript_path = r'C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe'  # Update this path
if not os.path.exists(ghostscript_path):
    raise FileNotFoundError(f"Ghostscript executable not found at {ghostscript_path}")

# Collect pyzbar binary and data files
pyzbar_binaries = collect_dynamic_libs('pyzbar')
pyzbar_datas = collect_data_files('pyzbar')

a = Analysis(['src\\main.py'],
             pathex=[os.path.abspath('.')],
             binaries=[(tesseract_path, '.'), (ghostscript_path, '.')] + pyzbar_binaries,
             datas=[
                 ('resources', 'resources'),
                 ('C:\\Program Files\\Tesseract-OCR\\tessdata', 'tessdata'),
             ] + pyzbar_datas,
             hiddenimports=['pyzbar'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='KC_app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,  # Changed back to False to hide the console
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon='resources\\app_icon.ico',
          splash='resources\\splash_image.png')