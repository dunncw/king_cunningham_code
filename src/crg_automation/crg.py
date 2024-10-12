from PyQt6.QtCore import QObject, pyqtSignal
from .excel_processor import ExcelProcessor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
            self.progress.emit(30)

            # Initialize web driver
            self.status.emit("Initializing web browser...")
            self.init_driver()
            self.progress.emit(40)

            # Log in to the website
            self.status.emit("Logging in to Capital IT Files...")
            self.login()
            self.progress.emit(50)

            # TODO: Implement further automation steps here

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
            self.driver = webdriver.Chrome()
        elif self.browser.lower() == "firefox":
            self.driver = webdriver.Firefox()
        elif self.browser.lower() == "edge":
            self.driver = webdriver.Edge()
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

        # Wait for the login process to complete (you may need to adjust this based on the actual behavior of the website)
        WebDriverWait(self.driver, 10).until(
            EC.url_changes("https://capitalit.files.com/login")
        )

        self.status.emit("Successfully logged in to Capital IT Files.")