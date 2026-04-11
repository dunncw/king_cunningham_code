from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time
import pyautogui
import os

class CRGAutomationWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, excel_path, browser, username, password, save_location):
        super().__init__()
        self.excel_path = excel_path
        self.browser = browser
        self.username = username
        self.password = password
        self.save_location = save_location
        self.driver = None
        self._abort = False

    def stop(self):
        self._abort = True

    def run(self):
        try:
            print("DEBUG: Starting CRG Automation...")
            self.status.emit("Starting CRG Automation...")
            self.progress.emit(10)

            # Process Excel file
            print("DEBUG: Processing Excel file...")
            self.status.emit("Processing Excel file...")
            excel_processor = ExcelProcessor(self.excel_path)
            account_numbers = excel_processor.process_excel()
            print(f"DEBUG: Found {len(account_numbers)} account numbers: {account_numbers}")
            self.status.emit(f"Found {len(account_numbers)} account numbers for Myrtle Beach.")
            self.progress.emit(20)

            # Initialize web driver
            print("DEBUG: Initializing web browser...")
            self.status.emit("Initializing web browser...")
            self.init_driver()
            self.progress.emit(30)

            # Log in to the website
            print("DEBUG: Attempting login...")
            self.status.emit("Logging in to Capital IT Files...")
            self.login()
            self.progress.emit(40)

            # Process each account number
            for i, account_number in enumerate(account_numbers):
                if self._abort:
                    break
                print(f"DEBUG: Processing account {account_number} ({i+1}/{len(account_numbers)})")
                self.status.emit(f"Processing account number {account_number} ({i+1}/{len(account_numbers)})...")
                self.process_account(account_number)

            if self._abort:
                self.status.emit("Automation stopped by user.")
            else:
                self.status.emit("CRG Automation completed successfully!")
            self.finished.emit()
        except Exception as e:
            print(f"DEBUG: Error occurred: {str(e)}")
            self.error.emit(str(e))
        finally:
            if self.driver:
                print("DEBUG: Closing browser...")
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"DEBUG: Error closing driver: {str(e)}")
                self.driver = None

    def init_driver(self):
        print(f"DEBUG: Initializing {self.browser} driver...")
        if self.browser.lower() == "chrome":
            options = ChromeOptions()
            options.add_experimental_option('prefs', {
                'download.prompt_for_download': True,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            })
            self.driver = webdriver.Chrome(options=options)
        elif self.browser.lower() == "firefox":
            options = FirefoxOptions()
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.manager.showWhenStarting", True)
            options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/zip")
            self.driver = webdriver.Firefox(options=options)
        elif self.browser.lower() == "edge":
            options = EdgeOptions()
            options.add_experimental_option('prefs', {
                'download.prompt_for_download': True,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            })
            self.driver = webdriver.Edge(options=options)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")
        try:
            import ctypes
            from ctypes import wintypes
            rect = wintypes.RECT()
            ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
            x = (rect.right - rect.left) // 2 + rect.left
            w = (rect.right - rect.left) // 2
            self.driver.set_window_position(x, rect.top)
            self.driver.set_window_size(w, rect.bottom - rect.top)
        except Exception:
            self.driver.maximize_window()
        print(f"DEBUG: {self.browser} driver initialized successfully")

    def login(self):
        print("DEBUG: Navigating to login page...")
        self.driver.get("https://capitalit.files.com/login")
        time.sleep(0.5)
        print(f"DEBUG: Current URL after navigation: {self.driver.current_url}")
        
        # Wait for the username field to be visible and enter the username
        print("DEBUG: Looking for username field...")
        username_field = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "form-username"))
        )
        time.sleep(0.5)
        print("DEBUG: Username field found, entering username...")
        username_field.clear()
        time.sleep(0.5)
        username_field.send_keys(self.username)
        time.sleep(0.5)

        # Enter the password
        print("DEBUG: Looking for password field...")
        password_field = self.driver.find_element(By.ID, "form-password")
        time.sleep(0.5)
        print("DEBUG: Password field found, entering password...")
        password_field.clear()
        time.sleep(0.5)
        password_field.send_keys(self.password)
        time.sleep(0.5)

        # Click the login button
        print("DEBUG: Looking for login button...")
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        time.sleep(0.5)
        print("DEBUG: Login button found, clicking...")
        login_button.click()
        time.sleep(1.0)  # Longer wait after login click
        
        print("DEBUG: Waiting for login to complete...")
        print(f"DEBUG: Current URL before wait: {self.driver.current_url}")

        # Wait for the login process to complete
        try:
            WebDriverWait(self.driver, 15).until(
                EC.url_changes("https://capitalit.files.com/login")
            )
            print(f"DEBUG: URL changed after login: {self.driver.current_url}")
        except Exception as e:
            print(f"DEBUG: URL didn't change as expected: {str(e)}")
            print(f"DEBUG: Current URL: {self.driver.current_url}")

        self.status.emit("Successfully logged in to Capital IT Files.")
        print("DEBUG: Login process completed")

    def process_account(self, account_number):
        print(f"DEBUG: Starting to process account {account_number}")
        try:
            # Navigate to the main page before each search
            print("DEBUG: Navigating to main page...")
            self.driver.get("https://capitalit.files.com/")
            time.sleep(1.0)  # Wait for page load
            print(f"DEBUG: Current URL: {self.driver.current_url}")
            
            # Wait for the page to load and find the search bar
            print("DEBUG: Looking for search bar...")
            search_bar = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search files and folders...']"))
            )
            time.sleep(0.5)
            print("DEBUG: Search bar found, clearing and entering account number...")
            search_bar.clear()
            time.sleep(0.5)
            search_bar.send_keys(str(account_number))
            time.sleep(0.5)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(1.0)  # Wait for search to process
            print(f"DEBUG: Search submitted for account {account_number}")

            # Wait for search results and switch to grid view
            print("DEBUG: Waiting for search results to load...")
            time.sleep(2.0)  # Wait for results to appear
            
            print("DEBUG: Looking for grid view button...")
            grid_view_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Grid view']"))
            )
            time.sleep(0.5)
            print("DEBUG: Grid view button found, clicking...")
            grid_view_button.click()
            time.sleep(1.0)  # Wait for view to change

            # Select all files
            print("DEBUG: Looking for 'Select all' button...")
            select_all_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Select all')]"))
            )
            time.sleep(0.5)
            print("DEBUG: 'Select all' button found, clicking...")
            select_all_button.click()
            time.sleep(1.0)  # Wait for selection

            # Click download button
            print("DEBUG: Looking for download button...")
            download_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.FilesPageSelectedHeader-button-download"))
            )
            time.sleep(0.5)
            print("DEBUG: Download button found, clicking...")
            download_button.click()
            time.sleep(2.0)  # Wait for download dialog

            # Handle file save dialog using PyAutoGUI
            save_path = os.path.join(self.save_location, f"{account_number}")
            save_path = os.path.normpath(save_path)
            print(f"DEBUG: Typing save path: {save_path}")
            
            time.sleep(1.0)  # Wait for dialog to fully appear
            pyautogui.write(save_path)
            time.sleep(1.0)
            pyautogui.press('enter')
            time.sleep(1.0)  # Wait after confirming save
            print("DEBUG: Save path entered and confirmed")

            # Wait for the download to complete
            print("DEBUG: Waiting for download to complete...")
            time.sleep(5.0)  # Wait for download

            print(f"DEBUG: Account {account_number} processing completed")
            self.status.emit(f"Files for account {account_number} downloaded successfully as {save_path}")

        except Exception as e:
            print(f"DEBUG: Error processing account {account_number}: {str(e)}")
            try:
                self.driver.title
            except Exception:
                raise RuntimeError(f"Browser was closed. Stopped at account {account_number}.") from e
            self.status.emit(f"Error processing account {account_number}: {str(e)}")


def main():
    # This function allows you to test the CRGAutomationWorker independently
    excel_path = r"D:\repositorys\KC_appp\task\crg\data\in\Closing Worksheet SBO-CP-219.xlsm"
    browser = "chrome"
    username = "Kcunningham"
    password = "Capital1234!"
    save_location = r"D:\repositorys\KC_appp\task\crg\data\out"

    worker = CRGAutomationWorker(excel_path, browser, username, password, save_location)

    # Create simple callback functions to handle signals
    def on_progress(value):
        print(f"Progress: {value}%")

    def on_status(message):
        print(f"Status: {message}")

    def on_error(error_message):
        print(f"Error: {error_message}")

    def on_finished():
        print("Automation finished")

    # Connect signals to callback functions
    worker.progress.connect(on_progress)
    worker.status.connect(on_status)
    worker.error.connect(on_error)
    worker.finished.connect(on_finished)

    # Run the automation
    worker.run()

if __name__ == "__main__":
    from excel_processor import ExcelProcessor
    main()
else:
    from .excel_processor import ExcelProcessor