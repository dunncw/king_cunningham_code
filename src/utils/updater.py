import os
import sys
import requests
import zipfile
import tempfile
import shutil
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class UpdateChecker(QObject):
    update_available = pyqtSignal(str, str)
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.api_url = "https://api.github.com/repos/dunncw/king_cunningham_code/releases/latest"

    def check_for_updates(self):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            
            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')
            
            if self._version_compare(latest_version, self.current_version) > 0:
                download_url = latest_release['assets'][0]['browser_download_url']
                self.update_available.emit(latest_version, download_url)
            else:
                self.no_update.emit()
        except requests.RequestException as e:
            self.error_occurred.emit(f"Error checking for updates: {str(e)}")

    def _version_compare(self, version1, version2):
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        return 0

class Updater(QThread):
    update_progress = pyqtSignal(int)
    update_completed = pyqtSignal(str)  # Changed to emit the path of the updated executable
    error_occurred = pyqtSignal(str)

    def __init__(self, download_url):
        super().__init__()
        self.download_url = download_url

    def run(self):
        try:
            # Download the update
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, 'update.zip')
                
                # Download the zip file
                with open(zip_path, 'wb') as file:
                    for data in response.iter_content(block_size):
                        size = file.write(data)
                        downloaded += size
                        if total_size:
                            progress = int((downloaded / total_size) * 100)
                            self.update_progress.emit(progress)

                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Find the executable in the extracted files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.exe'):
                            exe_path = os.path.join(root, file)
                            self.update_completed.emit(exe_path)
                            return

                raise Exception("No executable found in the update package.")

        except Exception as e:
            self.error_occurred.emit(f"Error during update: {str(e)}")

def restart_with_updated_exe(new_exe_path):
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        current_exe = sys.executable
    else:
        # Running from script
        current_exe = sys.argv[0]

    # Copy the new executable to replace the current one
    shutil.copy2(new_exe_path, current_exe)

    # Restart the application
    os.execl(current_exe, current_exe, *sys.argv[1:])