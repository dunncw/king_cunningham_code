from PyQt6.QtCore import QObject, pyqtSignal
from .excel_processor import ExcelProcessor
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

    def run(self):
        try:
            self.status.emit("Starting CRG Automation...")
            self.progress.emit(10)

            # Process Excel file
            self.status.emit("Processing Excel file...")
            excel_processor = ExcelProcessor(self.excel_path)
            account_numbers = excel_processor.process_excel()
            self.status.emit(f"Found {len(account_numbers)} account numbers for Myrtle Beach.")
            self.progress.emit(20)

            # Initialize web driver
            self.status.emit("Initializing web browser...")
            self.init_driver()
            self.progress.emit(30)

            # Log in to the website
            self.status.emit("Logging in to Capital IT Files...")
            self.login()
            self.progress.emit(40)

            # Process each account number
            for i, account_number in enumerate(account_numbers):
                self.status.emit(f"Processing account number {account_number} ({i+1}/{len(account_numbers)})...")
                self.process_account(account_number)
                progress = 40 + (i + 1) * (60 / len(account_numbers))
                self.progress.emit(int(progress))

            self.status.emit("CRG Automation completed successfully!")
            self.progress.emit(100)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self.driver:
                self.driver.quit()

    def init_driver(self):
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

    def login(self):
        self.driver.get("https://capitalit.files.com/login")
        
        # Wait for the username field to be visible and enter the username
        username_field = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "form-username"))
        )
        username_field.send_keys(self.username)

        # Enter the password
        password_field = self.driver.find_element(By.ID, "form-password")
        password_field.send_keys(self.password)

        # Click the login button
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()

        # Wait for the login process to complete
        WebDriverWait(self.driver, 10).until(
            EC.url_changes("https://capitalit.files.com/login")
        )

        self.status.emit("Successfully logged in to Capital IT Files.")

    def process_account(self, account_number):
        # Find and fill the search bar
        search_bar = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search files and folders...']"))
        )
        search_bar.clear()
        search_bar.send_keys(str(account_number))
        search_bar.send_keys(Keys.RETURN)

        # Wait for search results and switch to grid view
        time.sleep(2)  # Wait for search results to load
        grid_view_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Grid view']"))
        )
        grid_view_button.click()

        # Select all files
        select_all_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Select all')]"))
        )
        select_all_button.click()

        # Click download button
        download_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "svg.icon-download"))
        )
        download_button.click()

        # Wait for the file save dialog to appear
        time.sleep(2)

        # Handle file save dialog using PyAutoGUI
        save_path = os.path.join(self.save_location, f"{account_number}.zip")
        save_path = os.path.normpath(save_path)
        pyautogui.write(save_path)
        time.sleep(2)
        pyautogui.press('enter')

        # Wait for the download to complete (you may need to adjust this wait time)
        time.sleep(10)

        self.status.emit(f"Files for account {account_number} downloaded successfully as {save_path}")

def main():
    # This function allows you to test the CRGAutomationWorker independently
    excel_path = r"data\raw\capital_ventures\Closing Worksheet SBO-CP-216.xlsm"
    browser = "chrome"
    username = "Kcunningham"
    password = "Capital1234!"
    save_location = r"data\sorted\crg"

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
    main()