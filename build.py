import os
import subprocess
import shutil

def build_app():
    # Run PyInstaller
    subprocess.call(['pyinstaller', 'KC_app.spec', '--clean'])

    # Copy additional files if needed
    # shutil.copy('some_file.dll', 'dist/KC_app/')

    print("Build completed. Executable is in the 'dist' folder.")

if __name__ == '__main__':
    build_app()