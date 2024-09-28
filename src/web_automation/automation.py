import time
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class alert_is_present_or_element(object):
    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        try:
            alert = driver.switch_to.alert
            return alert
        except NoAlertPresentException:
            try:
                return EC.presence_of_element_located(self.locator)(driver)
            except:
                return False

def is_alert_present(driver):
    try:
        driver.switch_to.alert
        return True
    except NoAlertPresentException:
        return False

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
        # Define local variables
        business_name = 'CENTENNIAL PARK DEVELOPMENT LLC'
        address_1 = 'C/O 115 CENTENNIAL OLYMPIC PARK DRIVE NW'
        city = 'ATLANTA'
        zip_code = '30313'
        street = '155'
        street_name = 'Centennial Olympic Park'
        map_pn = "14-0078-0007-096-9"

        # Extract data from Excel
        people_data = extract_data_from_excel(self.excel_path)
        self.status.emit(f"Extracted data for {len(people_data)} people from Excel file")

        # Print out the first row of extracted data
        if people_data:
            first_person = people_data[0]
            self.status.emit("First row of extracted data:")
            for key, value in first_person.items():
                self.status.emit(f"{key}: {value}")
        else:
            self.status.emit("No data found in the Excel file")

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

            # Navigate to the form page
            driver.get("https://apps.gsccca.org/pt61efiling/PT61.asp")
            self.status.emit("Navigated to PT-61 form page")

            # On the next page, click the radio button
            business_radio = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@name='businessFlag' and @value='1']"))
            )
            business_radio.click()
            self.status.emit("Selected business radio button")

            # Fill out the business name field
            business_name_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "businessName"))
            )
            business_name_field.send_keys(business_name)
            self.status.emit("Filled out business name")

            # Fill out the address field
            address_field = driver.find_element(By.ID, "street1")
            address_field.send_keys(address_1)
            self.status.emit("Filled out address")

            # Fill out the city field
            city_field = driver.find_element(By.ID, "city")
            city_field.send_keys(city)
            self.status.emit("Filled out city")

            # Fill out the zip code field
            zip_field = driver.find_element(By.ID, "zip")
            zip_field.send_keys(zip_code)
            self.status.emit("Filled out zip code")

            # Click "Next Step" button
            next_step_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "btnNext"))
            )
            next_step_button.click()
            self.status.emit("Clicked 'Next Step' button")

            # Fill out additional fields on the next page
            if people_data:
                person = people_data[0]
                
                # Fill out first name
                first_name_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "firstName"))
                )
                first_name_field.send_keys(person['individual_name']['first'])
                self.status.emit(f"Filled out first name: {person['individual_name']['first']}")

                # Fill out middle name
                middle_name_field = driver.find_element(By.ID, "middleName")
                middle_name_field.send_keys(person['individual_name']['middle'])
                self.status.emit(f"Filled out middle name: {person['individual_name']['middle']}")

                # Fill out last name
                last_name_field = driver.find_element(By.ID, "lastName")
                last_name_field.send_keys(person['individual_name']['last'])
                self.status.emit(f"Filled out last name: {person['individual_name']['last']}")

                # Fill out address
                address_field = driver.find_element(By.ID, "street1")
                address_field.send_keys(address_1)
                self.status.emit(f"Filled out address: {address_1}")

                # Fill out city
                city_field = driver.find_element(By.ID, "city")
                city_field.send_keys(city)
                self.status.emit(f"Filled out city: {city}")

                # Fill out zip code
                zip_field = driver.find_element(By.ID, "zip")
                zip_field.send_keys(zip_code)
                self.status.emit(f"Filled out zip code: {zip_code}")

                # Check for additional name
                if 'additional_name' in person and person['additional_name']:
                    # Fill out additional first name
                    additional_first_name_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "AdditionalFirstName"))
                    )
                    additional_first_name_field.send_keys(person['additional_name']['first'])
                    self.status.emit(f"Filled out additional first name: {person['additional_name']['first']}")

                    # Fill out additional middle name
                    additional_middle_name_field = driver.find_element(By.ID, "AdditionalMiddleName")
                    additional_middle_name_field.send_keys(person['additional_name']['middle'])
                    self.status.emit(f"Filled out additional middle name: {person['additional_name']['middle']}")

                    # Fill out additional last name
                    additional_last_name_field = driver.find_element(By.ID, "AdditionalLastName")
                    additional_last_name_field.send_keys(person['additional_name']['last'])
                    self.status.emit(f"Filled out additional last name: {person['additional_name']['last']}")

                    # Click "Add to Additional Names" button
                    add_additional_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "btnAdd"))
                    )
                    add_additional_button.click()
                    self.status.emit("Clicked 'Add to Additional Names' button")
                else:
                    self.status.emit("No additional name found in the data")

                # Click "Next Step" button
                next_step_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnNext"))
                )
                next_step_button.click()
                self.status.emit("Clicked 'Next Step' button")

                 # Fill out the date of sale
                sale_date_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "saleDate"))
                )
                sale_date_field.send_keys(person['date_on_deed'])
                self.status.emit(f"Filled out date of sale: {person['date_on_deed']}")

                # Fill out street number
                street_number_field = driver.find_element(By.ID, "houseNumber")
                street_number_field.send_keys(street)
                self.status.emit(f"Filled out street number: {street}")

                # Fill out street name
                street_name_field = driver.find_element(By.ID, "houseStreetName")
                street_name_field.send_keys(street_name)
                self.status.emit(f"Filled out street name: {street_name}")

                # Select 'Drive' from street type dropdown
                street_type_dropdown = Select(driver.find_element(By.ID, "houseStreetType"))
                street_type_dropdown.select_by_value("DR")
                self.status.emit("Selected 'Drive' as street type")

                # Select post direction
                post_dir_dropdown = Select(driver.find_element(By.ID, "housePostDirection"))
                post_dir_dropdown.select_by_value("NW")
                self.status.emit(f"Selected post direction: {"NW"}")

                # Select county
                county_dropdown = Select(driver.find_element(By.ID, "county"))
                county_dropdown.select_by_value("60")
                self.status.emit(f"Selected county: {"Fulton"}")

                # Fill out map/parcel number
                map_number_field = driver.find_element(By.ID, "mapNumber")
                map_number_field.send_keys(map_pn)
                self.status.emit(f"Filled out map/parcel number: {map_pn}")

                # Click "Next Step" button
                next_step_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnNext"))
                )
                next_step_button.click()
                self.status.emit("Clicked 'Next Step' button")

                # Wait for a short time to allow the alert to appear if it's going to
                time.sleep(2)

                # Check for alert
                if is_alert_present(driver):
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    self.status.emit(f"Alert detected: {alert_text}")
                    alert.accept()
                    self.status.emit("Alert accepted")
                else:
                    self.status.emit("No alert detected, proceeding with form fill")

                # Wait for the sales price field to be present
                sales_price_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "actualValue"))
                )
                sales_price_field.send_keys(person['sales_price'])
                self.status.emit(f"Filled out sales price: {person['sales_price']}")

                # Set fair market value to zero
                fair_market_value_field = driver.find_element(By.ID, "fairMarketValue")
                fair_market_value_field.send_keys("0")
                self.status.emit("Set fair market value to zero")

                # Set liens and encumbrances to zero
                liens_field = driver.find_element(By.ID, "liensAndEncumberances")
                liens_field.send_keys("0")
                self.status.emit("Set liens and encumbrances to zero")

                # Click "Next Step" button
                next_step_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnNext"))
                )
                next_step_button.click()
                self.status.emit("Clicked 'Next Step' button")

                # Click the checkboxes
                checkboxes = ["chkCounty", "chkAccept", "chkTaxAccept"]
                for checkbox_id in checkboxes:
                    checkbox = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, checkbox_id))
                    )
                    checkbox.click()
                    self.status.emit(f"Clicked checkbox: {checkbox_id}")

                # Update progress
                self.progress.emit(100)

                self.status.emit("Form filled out completely. Waiting for user input.")
                self.status.emit("Press Enter in the console to close the browser...")
                input("Press Enter to close the browser...")

        except UnexpectedAlertPresentException as uae:
            self.status.emit(f"Unexpected alert appeared: {uae.alert_text}")
            self.status.emit("Attempting to accept the alert...")
            try:
                driver.switch_to.alert.accept()
                self.status.emit("Alert accepted")
            except:
                self.status.emit("Failed to accept the alert")

        except Exception as e:
            self.error.emit(str(e))
            self.status.emit("An error occurred. Press Enter in the console to close the browser...")
            input("Press Enter to close the browser...")

        finally:
            if 'driver' in locals():
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
    from excel_processor import extract_data_from_excel, print_extracted_data
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    test_browser = "Chrome"
    test_username = "jcunningham@kingcunningham.com"
    test_password = "Kc123!@#"

    thread, worker = run_web_automation_thread(test_excel_path, test_browser, test_username, test_password)
    
    worker.status.connect(print)  # Print status updates to console
    worker.progress.connect(lambda p: print(f"Progress: {p}%"))
    worker.error.connect(lambda e: print(f"Error: {e}"))

    thread.start()

    sys.exit(app.exec())
else:
    # When imported as a module
    from .excel_processor import extract_data_from_excel, print_extracted_data