import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from utils.updater import UpdateChecker
from PyQt6.QtCore import QCoreApplication
import asyncio

# Set the current version
CURRENT_VERSION = "0.0.1"  # This should match the version in your main.py

def update_available_callback(new_version, download_url):
    print(f"Update available: version {new_version}")
    print(f"Download URL: {download_url}")
    QCoreApplication.quit()

def error_callback(error_message):
    print(f"Error occurred: {error_message}")
    QCoreApplication.quit()

async def run_update_check():
    app = QCoreApplication([])
    
    update_checker = UpdateChecker(CURRENT_VERSION)
    update_checker.update_available.connect(update_available_callback)
    update_checker.error_occurred.connect(error_callback)
    
    update_checker.check_for_updates()
    
    await asyncio.get_event_loop().run_in_executor(None, app.exec)

if __name__ == "__main__":
    asyncio.run(run_update_check())