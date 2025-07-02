# File: web_automation/base_automation.py

import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from PyQt6.QtCore import QObject, pyqtSignal
import pyautogui

class BasePT61Automation(QObject):
    """Base class for PT61 automation with shared functionality"""
    
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, excel_path, browser, username, password, save_location, version):
        super().__init__()
        self.excel_path = excel_path
        self.browser = browser
        self.username = username
        self.password = password
        self.save_location = save_location
        self.version = version
        self.driver = None

    def setup_webdriver(self):
        """Setup WebDriver based on browser choice"""
        if self.browser == "Chrome":
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
        elif self.browser == "Firefox":
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service)
        elif self.browser == "Edge":
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")

    def navigate_to_login(self):
        """Navigate to the PT61 login page"""
        url = "https://apps.gsccca.org/pt61efiling/"
        self.driver.get(url)
        self.status.emit(f"Opened {self.browser} and navigated to {url}")

    def perform_login(self):
        """Perform login to the PT61 system"""
        # Click login link
        login_link = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login To Save & Retrieve Your Filings')]"))
        )
        login_link.click()
        self.status.emit("Clicked on login link")

        # Fill in username and password
        username_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "txtUserID"))
        )
        username_field.send_keys(self.username)

        password_field = self.driver.find_element(By.NAME, "txtPassword")
        password_field.send_keys(self.password)

        # Select the checkbox
        checkbox = self.driver.find_element(By.NAME, "permanent")
        if not checkbox.is_selected():
            checkbox.click()

        # Click login button
        login_button = self.driver.find_element(By.XPATH, "//a[contains(@href, 'javascript:document.frmLogin.submit();')]")
        login_button.click()
        self.status.emit("Attempted to log in")

        # Wait for the logout link to appear, indicating successful login
        logout_link = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "logout"))
        )
        self.status.emit("Logged in successfully")

    def navigate_to_form(self):
        """Navigate to the PT-61 form page"""
        self.driver.get("https://apps.gsccca.org/pt61efiling/PT61.asp")
        self.status.emit("Navigated to PT-61 form page")

    def click_next_step(self):
        """Click the Next Step button"""
        next_step_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnNext"))
        )
        next_step_button.click()

    def handle_alert_if_present(self):
        """Handle alert if it appears, otherwise continue"""
        time.sleep(2)  # Wait for potential alert
        
        if self.is_alert_present():
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            self.status.emit(f"Alert detected: {alert_text}")
            alert.accept()
            self.status.emit("Alert accepted")
        else:
            self.status.emit("No alert detected, proceeding with form fill")

    def is_alert_present(self):
        """Check if an alert is present"""
        try:
            self.driver.switch_to.alert
            return True
        except NoAlertPresentException:
            return False

    def fill_standard_property_fields(self, street_number, street_name, street_type_value, post_direction, county_value, map_parcel):
        """Fill standard property fields that are the same across versions"""
        # Fill out street number
        street_number_field = self.driver.find_element(By.ID, "houseNumber")
        street_number_field.send_keys(street_number)

        # Fill out street name
        street_name_field = self.driver.find_element(By.ID, "houseStreetName")
        street_name_field.send_keys(street_name)

        # Select street type from dropdown
        street_type_dropdown = Select(self.driver.find_element(By.ID, "houseStreetType"))
        street_type_dropdown.select_by_value(street_type_value)

        # Select post direction
        post_dir_dropdown = Select(self.driver.find_element(By.ID, "housePostDirection"))
        post_dir_dropdown.select_by_value(post_direction)

        # Select county
        county_dropdown = Select(self.driver.find_element(By.ID, "county"))
        county_dropdown.select_by_value(county_value)

        # Fill out map/parcel number
        map_number_field = self.driver.find_element(By.ID, "mapNumber")
        map_number_field.send_keys(map_parcel)

    def fill_standard_financial_fields(self, sales_price, fair_market_value="0", liens_value="0"):
        """Fill standard financial fields"""
        # Wait for the sales price field to be present
        sales_price_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "actualValue"))
        )
        sales_price_field.send_keys(sales_price)
        self.status.emit(f"Filled out sales price: {sales_price}")

        # Set fair market value
        fair_market_value_field = self.driver.find_element(By.ID, "fairMarketValue")
        fair_market_value_field.send_keys(fair_market_value)

        # Set liens and encumbrances
        liens_field = self.driver.find_element(By.ID, "liensAndEncumberances")
        liens_field.send_keys(liens_value)

    def submit_form(self):
        """Submit the PT-61 form"""
        # Click the checkboxes
        checkboxes = ["chkCounty", "chkAccept", "chkTaxAccept"]
        for checkbox_id in checkboxes:
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, checkbox_id))
            )
            checkbox.click()

        # Click "Submit PT-61 Form" button
        submit_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnSubmitPT61"))
        )
        submit_button.click()
        self.status.emit("Clicked 'Submit PT-61 Form' button")

    def save_pdf(self, filename):
        """Save the generated PDF"""
        # Wait for the specific iframe to be present
        iframe_locator = (By.CSS_SELECTOR, "#dvPT61IFrame iframe")
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located(iframe_locator))
        self.status.emit("PT-61 iframe found")

        # Get the iframe element
        iframe = self.driver.find_element(*iframe_locator)

        # Extract the src attribute
        iframe_src = iframe.get_attribute('src')
        self.status.emit(f"Iframe src: {iframe_src}")

        # Open the PDF in a new tab
        self.driver.execute_script(f"window.open('{iframe_src}', '_blank');")

        # Switch to the new tab
        self.driver.switch_to.window(self.driver.window_handles[-1])

        # Wait for the PDF to load
        time.sleep(5)

        # Generate file path
        file_path = os.path.join(self.save_location, filename)
        file_path = os.path.normpath(file_path)

        # Use pyautogui to save
        pyautogui.hotkey('ctrl', 's')
        time.sleep(2)
        pyautogui.write(file_path)
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)

        self.status.emit(f"Saved PDF as: {filename}")

        # Close the PDF tab
        self.driver.close()

        # Switch back to the original tab
        self.driver.switch_to.window(self.driver.window_handles[0])

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            self.status.emit("Browser closed.")

    # Abstract methods to be implemented by version-specific classes
    def fill_seller_section(self, person_data):
        """Fill seller section - to be implemented by version classes"""
        raise NotImplementedError("Version classes must implement fill_seller_section")

    def fill_buyer_section(self, person_data):
        """Fill buyer section - to be implemented by version classes"""
        raise NotImplementedError("Version classes must implement fill_buyer_section")

    def fill_property_section(self, person_data):
        """Fill property section - to be implemented by version classes"""
        raise NotImplementedError("Version classes must implement fill_property_section")

    def fill_financial_section(self, person_data):
        """Fill financial section - to be implemented by version classes"""
        raise NotImplementedError("Version classes must implement fill_financial_section")

    def generate_filename(self, person_data):
        """Generate filename for PDF - to be implemented by version classes"""
        raise NotImplementedError("Version classes must implement generate_filename")

    def process_person(self, person_data, index, total_count):
        """Process a single person through the form - template method"""
        self.status.emit(f"Processing person {index} of {total_count}")

        # Navigate to form
        self.navigate_to_form()

        # Fill sections (version-specific implementations)
        self.fill_seller_section(person_data)
        self.click_next_step()

        self.fill_buyer_section(person_data)
        self.click_next_step()

        self.fill_property_section(person_data)
        self.click_next_step()

        self.handle_alert_if_present()

        self.fill_financial_section(person_data)
        self.click_next_step()

        # Submit and save
        self.submit_form()
        filename = self.generate_filename(person_data)
        self.save_pdf(filename)

        # Update progress
        progress = int((index / total_count) * 100)
        self.progress.emit(progress)