# File: pacer/pacer.py
from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time

if __name__ == "__main__":
    from excel_processor import PACERExcelProcessor
else:
    from .excel_processor import PACERExcelProcessor

class PACERAutomationWorker(QObject):
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
        
    def process_data(self):
        """Process the Excel file and return the data"""
        processor = PACERExcelProcessor(self.excel_path)
        return processor.process_excel()

    def run(self):
        try:
            # Process Excel file
            self.status.emit("Processing Excel file...")
            success, data = self.process_data()
            if not success:
                raise Exception(f"Excel processing failed: {data}")
            
            # Initialize web driver
            self.status.emit("Initializing web browser...")
            self.init_driver()
            
            # Navigate to PACER
            self.status.emit("Navigating to PACER...")
            self.driver.get("https://pacer.login.uscourts.gov/csologin/login.jsf?pscCourtId=PCL")
            
            # Wait for page to load
            time.sleep(2)  # Add proper wait conditions later
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self.driver:
                self.driver.quit()

    def init_driver(self):
        if self.browser.lower() == "chrome":
            options = ChromeOptions()
            self.driver = webdriver.Chrome(options=options)
        elif self.browser.lower() == "firefox":
            options = FirefoxOptions()
            self.driver = webdriver.Firefox(options=options)
        elif self.browser.lower() == "edge":
            options = EdgeOptions()
            self.driver = webdriver.Edge(options=options)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")
        
        self.driver.maximize_window()

def main():
    # Test parameters
    excel_path = r"D:\repositorys\KC_appp\task\pacer_scra\data\in\z SSN Example.xlsx"
    browser = "Chrome"
    username = "test_user"
    password = "test_pass"
    save_location = r"D:\repositorys\KC_appp\task\pacer_scra\data\out_pacer"
    
    print(f"Starting PACER automation test")
    print(f"Excel file: {excel_path}")
    print(f"Save location: {save_location}")
    print(f"Browser: {browser}")
    
    # Create worker instance
    worker = PACERAutomationWorker(excel_path, browser, username, password, save_location)
    
    # Process Excel file first
    success, data = worker.process_data()
    if not success:
        print(f"Error processing Excel file: {data}")
        return
    
    print("\nProcessed Excel data:")
    for row in data:
        print(f"\nAccount #: {row['account_number']}")
        for person in row['people']:
            print(f"Person: {person['last_name']}, SSN: {person['ssn']}")
    
    # Run the automation
    try:
        print("\nStarting browser automation...")
        worker.run()
        print("Browser automation completed successfully")
    except Exception as e:
        print(f"Error during browser automation: {str(e)}")

if __name__ == "__main__":
    main()