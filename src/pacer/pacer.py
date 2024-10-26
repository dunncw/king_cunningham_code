# File: pacer/pacer.py
from PyQt6.QtCore import QObject, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import os

# TODO: in the case that we find a open banrucpy we need to take a screen shot of the page and save it with a good file name.

# Handle different import paths for direct execution vs module import
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
        self.wait = None
        
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
            
            # Login to PACER
            self.status.emit("Logging into PACER...")
            if not self.login_to_pacer():
                raise Exception("Failed to login to PACER")
            
            # Process all people from the data
            for row in data:
                for person in row['people']:
                    print(person['last_name'])

                    time.sleep(.1)
                    # Navigate to bankruptcy search page
                    if not self.navigate_to_bankruptcy_search():
                        raise Exception("Failed to navigate to bankruptcy search")
                    
                    # self.status.emit(f"Searching SSN for {person['last_name']}...")
                    print(f"DEBUG: Searching person - Account: {row['account_number']}, Name: {person['last_name']}, SSN: {person['ssn']}")
                    
                    time.sleep(.1)
                    success, message = self.handle_search_attempt(person, row['account_number'])
                    if not success:
                        raise Exception(message)
                    
                    self.status.emit(message)
                    if "Some cases still open" in message:
                        print(f"\033[93mDEBUG: Search result - {message}\033[0m")  # Yellow highlight
                    else:
                        print(f"DEBUG: Search result - {message}")
                    
                    # Wait 5 seconds before next search
                    time.sleep(5)
            
            self.status.emit("All searches completed successfully")
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
        
        # Initialize WebDriverWait with 10 second timeout
        self.wait = WebDriverWait(self.driver, 10)

    def login_to_pacer(self):
        """Handle the PACER login process"""
        try:
            # Wait for and find username field
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "loginForm:loginName"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find password field
            password_field = self.driver.find_element(By.ID, "loginForm:password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Find and click login button
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'ui-button-text') and text()='Login']"))
            )
            login_button.click()
            
            # Wait for login to complete (you might need to adjust this based on PACER's behavior)
            # For example, wait for a specific element that appears after successful login
            time.sleep(2)  # Temporary wait - replace with proper wait condition
            
            # TODO: Add verification of successful login
            # For example, check for elements that only appear when logged in
            # or check for error messages
            
            return True
            
        except TimeoutException:
            self.error.emit("Timeout waiting for login elements to load")
            return False
        except WebDriverException as e:
            self.error.emit(f"Browser error during login: {str(e)}")
            return False
        except Exception as e:
            self.error.emit(f"Unexpected error during login: {str(e)}")
            return False
    
    def navigate_to_bankruptcy_search(self):
        """Navigate to the bankruptcy search page"""
        try:
            current_url = self.driver.current_url
            
            # If not on welcome page, navigate directly to bankruptcy search
            if "welcome.jsf" not in current_url:
                self.driver.get("https://pcl.uscourts.gov/pcl/pages/welcome.jsf")
            
            # Wait for welcome page to load
            # self.status.emit("Waiting for welcome page...")
            self.wait.until(EC.url_to_be("https://pcl.uscourts.gov/pcl/pages/welcome.jsf"))
            
            # Find and click bankruptcy search link
            bankruptcy_link = self.wait.until(
                EC.element_to_be_clickable((By.ID, "frmSearch:findBankruptcy"))
            )
            bankruptcy_link.click()
            time.sleep(.5)
            
            # Wait for search page to load
            # self.status.emit("Waiting for bankruptcy search page...")
            self.wait.until(EC.url_to_be("https://pcl.uscourts.gov/pcl/pages/search/findBankruptcy.jsf"))
            return True
            
        except TimeoutException:
            self.error.emit("Timeout waiting for bankruptcy search page")
            return False
        except Exception as e:
            self.error.emit(f"Error navigating to bankruptcy search: {str(e)}")
            return False

    # Add this new method to handle SSN search
    def search_ssn(self, ssn):
        """Enter SSN and perform search"""
        try:
            time.sleep(.1)
            # Wait for SSN input field
            ssn_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "frmSearch:txtSSN"))
            )
            ssn_input.clear()
            ssn_input.send_keys(ssn)

            time.sleep(.1)
            
            # Find and click search button
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class, 'ui-button-text') and text()='Search']"))
            )
            search_button.click()
            return True
            
        except TimeoutException:
            self.error.emit(f"Timeout during SSN search for {ssn}")
            return False
        except Exception as e:
            self.error.emit(f"Error during SSN search: {str(e)}")
            return False

    def check_search_results(self):
        """Handle and verify search results"""
        try:
            try:
                spinner = WebDriverWait(self.driver, 120).until(
                    EC.invisibility_of_element_located((By.XPATH, "//img[@alt='wait spinner']"))
                )
            except TimeoutException:
                return "timeout"
            
            # Check for "No Results Found" modal
            try:
                no_results_title = self.driver.find_element(By.ID, "frmSearch:dlgNoResultsFound_title")
                if no_results_title.is_displayed():
                    return "no_results"
            except:
                pass
            
            # Check if redirected to welcome page
            if self.driver.current_url == "https://pcl.uscourts.gov/pcl/pages/welcome.jsf":
                return "welcome_redirect"
                
            # Check if we're on a results page
            if "results/parties.jsf" in self.driver.current_url:
                # Verify "Search Results" link is present
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Search Results')]"))
                    )
                    
                    # Find all date closed values
                    date_cells = self.driver.find_elements(
                        By.XPATH, 
                        "//span[contains(@class, 'pcl-search-results-column pcl-search-results-column-size-6')]"
                    )
                    
                    if not date_cells:
                        raise Exception("Could not find date closed columns")
                    
                    # Check if any dates are empty
                    empty_dates = any(cell.text.strip() == "" for cell in date_cells)
                    
                    return "results_empty_dates" if empty_dates else "results_with_dates"
                    
                except Exception as e:
                    self.error.emit(f"Error processing results page: {str(e)}")
                    return "error"
                    
            return "unknown"
            
        except Exception as e:
            self.error.emit(f"Error checking search results: {str(e)}")
            return "error"

    def handle_search_attempt(self, person_data, account_number, attempt=1):
        """Handle a single search attempt with retry logic"""
        try:
            if not self.search_ssn(person_data['ssn']):
                return False, "Failed to perform search"
                    
            result_type = self.check_search_results()
            
            if result_type == "no_results":
                return True, f"No bankruptcy records found for {person_data['last_name']} (SSN: {person_data['ssn']})"
                        
            elif result_type == "timeout" or result_type == "welcome_redirect":
                if attempt < 2:  # Try once more
                    retry_reason = "timeout" if result_type == "timeout" else "redirect"
                    self.status.emit(f"Search failed due to {retry_reason}, attempting retry...")
                    
                    # If we got redirected to welcome page, we need to navigate back to search
                    if result_type == "welcome_redirect":
                        if not self.navigate_to_bankruptcy_search():
                            return False, f"Failed to navigate back to search page after redirect for {person_data['last_name']}"
                    
                    return self.handle_search_attempt(person_data, attempt + 1)
                else:
                    failure_reason = "timeout" if result_type == "timeout" else "redirect"
                    return False, f"Search failed after retry ({failure_reason}) for {person_data['last_name']} (SSN: {person_data['ssn']})"
                        
            elif result_type == "results_with_dates":
                return True, f"Bankruptcy records found for {person_data['last_name']} (SSN: {person_data['ssn']}) - All cases closed"
                    
            elif result_type == "results_empty_dates":
                # Take screenshot for open cases
                try:
                    screenshot_path = os.path.join(self.save_location, f"{account_number}_{person_data['ssn'][-4:]}.png")
                    screenshot_path = os.path.normpath(screenshot_path)
                    print(screenshot_path)
                    self.driver.save_screenshot(screenshot_path)
                    self.status.emit(f"Screenshot saved to {screenshot_path}")
                    print(f"Screenshot saved to {screenshot_path}")
                except Exception as e:
                    self.status.emit(f"Failed to save screenshot: {str(e)}")
                    print(e)
                
                return True, f"🚨 ⚠️ 🚨 ⚠️ Bankruptcy records found for {person_data['last_name']} (SSN: {person_data['ssn']}) - Some cases still open 🚨 ⚠️ 🚨 ⚠️"
                    
            else:
                return False, f"Unexpected result type ({result_type}) for {person_data['last_name']}"
                    
        except Exception as e:
            return False, f"Error during search: {str(e)}"


def main():
    # Test parameters
    excel_path = r"D:\repositorys\KC_appp\task\pacer_scra\data\in\z SSN Example copy.xlsx"
    browser = "Chrome"
    username = "KingC123"
    password = "Froglegs12#$"
    save_location = r"D:\repositorys\KC_appp\task\pacer_scra\data\out_pacer"
    # exmple of 'date closed' - 260042387
    # example of 'no close date' - 402082344
    
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
    
    # print("\nProcessed Excel data:")
    # for row in data:
    #     print(f"\nAccount #: {row['account_number']}")
    #     for person in row['people']:
    #         print(f"Person: {person['last_name']}, SSN: {person['ssn']}")
    
    # Run the automation
    try:
        print("\nStarting browser automation...")
        worker.run()
        print("Browser automation completed successfully")
    except Exception as e:
        print(f"Error during browser automation: {str(e)}")

if __name__ == "__main__":
    main()