# File: web_automation/automation.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from .excel_processor import extract_data_from_excel, print_extracted_data
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class WebAutomationWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, excel_path, browser, username, password):
        super().__init__()
        self.excel_path = excel_path
        self.browser = browser
        self.username = username
        self.password = password

    def run(self):
        try:
            self.run_web_automation()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def run_web_automation(self):
        # Extract data from Excel
        people_data = extract_data_from_excel(self.excel_path)
        self.status.emit(f"Extracted data for {len(people_data)} people from Excel file")

        # Setup WebDriver
        if self.browser == "Chrome":
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service)
        elif self.browser == "Firefox":
            service = FirefoxService(GeckoDriverManager().install())
            driver = webdriver.Firefox(service=service)
        elif self.browser == "Edge":
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

        try:
            # Open the browser and navigate to the specified URL
            url = "https://apps.gsccca.org/pt61efiling/"
            driver.get(url)
            self.status.emit(f"Opened {self.browser} and navigated to {url}")

            # Login process
            login_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login To Save & Retrieve Your Filings')]"))
            )
            login_link.click()
            self.status.emit("Clicked on login link")

            # Fill in username and password
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "txtUserID"))
            )
            username_field.send_keys(self.username)

            password_field = driver.find_element(By.NAME, "txtPassword")
            password_field.send_keys(self.password)

            # Select the checkbox
            checkbox = driver.find_element(By.NAME, "permanent")
            if not checkbox.is_selected():
                checkbox.click()

            # Click login button
            login_button = driver.find_element(By.XPATH, "//a[contains(@href, 'javascript:document.frmLogin.submit();')]")
            login_button.click()
            self.status.emit("Attempted to log in")

            # Wait for the logout link to appear, indicating successful login
            logout_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "logout"))
            )
            self.status.emit("Logged in successfully")

            # Loop through each person's data and submit the form
            for i, person in enumerate(people_data):
                self.status.emit(f"Processing person {i + 1} of {len(people_data)}")

                # Navigate to the form page
                driver.get("https://apps.gsccca.org/pt61efiling/PT61.asp")
                
                # Fill out the form using the person's data
                # (Fill in the form fields here)

                # Click "Next Step" button
                next_step_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnNext"))
                )
                next_step_button.click()
                self.status.emit(f"Submitted form for person {i + 1}")

                # Update progress
                self.progress.emit(int((i + 1) / len(people_data) * 100))

                # Add a small delay between submissions
                time.sleep(2)

            self.status.emit("All forms submitted. Browser will remain open.")
            
            # Wait for user input to close the browser
            input("Press Enter to close the browser...")

        finally:
            driver.quit()
            self.status.emit("Browser closed.")

def run_web_automation_thread(excel_path, browser, username, password):
    thread = QThread()
    worker = WebAutomationWorker(excel_path, browser, username, password)
    worker.moveToThread(thread)
    
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    return thread, worker

if __name__ == "__main__":
    # This block is for testing purposes only
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    test_browser = "Chrome"
    test_username = "your_username"
    test_password = "your_password"

    thread, worker = run_web_automation_thread(test_excel_path, test_browser, test_username, test_password)
    
    worker.status.connect(print)  # Print status updates to console
    worker.progress.connect(lambda p: print(f"Progress: {p}%"))
    worker.error.connect(lambda e: print(f"Error: {e}"))

    thread.start()

    sys.exit(app.exec())