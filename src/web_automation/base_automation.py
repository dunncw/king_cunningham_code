# File: web_automation/base_automation.py

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    UnexpectedAlertPresentException, 
    NoAlertPresentException,
    TimeoutException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from PyQt6.QtCore import QObject, pyqtSignal
import pyautogui
from .pdf_stacker import PT61PDFStacker

class BasePT61Automation(QObject):
    """Base class for PT61 automation with shared functionality"""
    
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, excel_path, browser, username, password, save_location, version, document_stacking=False):
        super().__init__()
        self.excel_path = excel_path
        self.browser = browser
        self.username = username
        self.password = password
        self.save_location = save_location
        self.version = version
        self.document_stacking = document_stacking
        self.driver = None
        self.keep_browser_open_on_error = False
        
        self.pdf_stacker = PT61PDFStacker()
        self.pdf_stacker.progress_update.connect(self.status.emit)

    def log_browser_state(self, context=""):
        """Log current browser state for debugging - concise output"""
        print(f"\n[DEBUG] {context}")
        print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
        
        if not self.driver:
            print("  Driver: None")
            return
        
        try:
            print(f"  URL: {self.driver.current_url}")
            print(f"  Title: {self.driver.title}")
        except Exception as e:
            print(f"  URL/Title: Error - {e}")
        
        try:
            alert = self.driver.switch_to.alert
            print(f"  ALERT PRESENT: {alert.text}")
        except NoAlertPresentException:
            pass
        except Exception:
            pass

    def log_error(self, error_msg, exception=None):
        """Log error with relevant context only"""
        print(f"\n{'!'*60}")
        print(f"ERROR: {error_msg}")
        print(f"  Version: {self.version}")
        print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
        
        if exception:
            exc_type = type(exception).__name__
            exc_msg = str(exception).split('\n')[0][:100]
            print(f"  Exception: {exc_type}: {exc_msg}")
        
        self.log_browser_state("At error")
        print(f"{'!'*60}\n")
        
        self.keep_browser_open_on_error = True

    def check_and_log_alert(self):
        """Check for alert and log its text if present, returns alert text or None"""
        try:
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            print(f"[ALERT] {alert_text}")
            return alert_text
        except NoAlertPresentException:
            return None

    def accept_alert_if_present(self):
        """Accept alert if present, log it, return True if alert was handled"""
        alert_text = self.check_and_log_alert()
        if alert_text:
            self.driver.switch_to.alert.accept()
            self.status.emit(f"Alert accepted: {alert_text[:50]}...")
            return True
        return False

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

    def navigate_to_login(self):
        """Navigate to the PT61 login page"""
        url = "https://apps.gsccca.org/pt61efiling/"
        self.driver.get(url)
        self.status.emit(f"Opened {self.browser} and navigated to {url}")

    def perform_login(self):
        """Perform login to the PT61 system"""
        try:
            login_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Login To Save & Retrieve Your Filings')]"))
            )
            login_link.click()
            self.status.emit("Clicked on login link")

            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "txtUserID"))
            )
            username_field.send_keys(self.username)

            password_field = self.driver.find_element(By.NAME, "txtPassword")
            password_field.send_keys(self.password)

            checkbox = self.driver.find_element(By.NAME, "permanent")
            if not checkbox.is_selected():
                checkbox.click()

            login_button = self.driver.find_element(By.XPATH, "//a[contains(@href, 'javascript:document.frmLogin.submit();')]")
            login_button.click()
            self.status.emit("Submitted login form")

            time.sleep(2)
            
            self.accept_alert_if_present()

            self.handle_announcement_page_if_present()

            self.navigate_back_to_pt61()
            
            self.status.emit("Login and navigation complete")
            
        except UnexpectedAlertPresentException:
            self.status.emit("Unexpected alert during login")
            self.accept_alert_if_present()
        except Exception as e:
            self.log_error("Login failed", e)
            raise

    def handle_announcement_page_if_present(self):
        """Handle the GSCCCA announcement/bulletin page if it appears after login"""
        time.sleep(2)
        
        current_url = self.driver.current_url
        self.status.emit(f"Post-login URL: {current_url}")
        
        if "CustomerCommunicationApi" in current_url or "Announcement" in self.driver.title:
            self.status.emit("Announcement page detected, dismissing...")
            
            try:
                options_dropdown = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "Options"))
                )
                select = Select(options_dropdown)
                select.select_by_value("dismiss")
                self.status.emit("Selected 'Dismiss' option")
                
                continue_button = self.driver.find_element(By.NAME, "Continue")
                continue_button.click()
                self.status.emit("Clicked Continue button")
                
                time.sleep(2)
                
                self.status.emit(f"After dismissing announcement, now at: {self.driver.current_url}")
                
            except Exception as e:
                self.log_error("Failed to dismiss announcement page", e)
                raise
        else:
            self.status.emit("No announcement page detected, continuing...")

    def navigate_back_to_pt61(self):
        """Navigate back to PT-61 efiling page and prepare for form entry"""
        self.status.emit("Navigating back to PT-61 efiling...")
        
        self.driver.get("https://apps.gsccca.org/pt61efiling/")
        time.sleep(2)
        
        self.status.emit(f"Now at: {self.driver.current_url}")
        
        try:
            logout_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "logout"))
            )
            self.status.emit("Confirmed logged in (logout link present)")
        except TimeoutException:
            self.status.emit("Warning: Could not confirm login status, continuing anyway...")

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
        
        time.sleep(1)
        if self.accept_alert_if_present():
            self.status.emit("Alert after Next Step was handled")

    def handle_alert_if_present(self):
        """Handle alert if it appears, otherwise continue"""
        time.sleep(2)
        
        if self.accept_alert_if_present():
            self.status.emit("Alert handled")
        else:
            self.status.emit("No alert detected, proceeding")

    def is_alert_present(self):
        """Check if an alert is present"""
        try:
            self.driver.switch_to.alert
            return True
        except NoAlertPresentException:
            return False

    def fill_primary_mailing_address(self, address_config):
        """Generic function to fill primary mailing address fields"""
        try:
            address_field = self.driver.find_element(By.ID, "street1")
            address_field.send_keys(address_config["line1"])
            self.status.emit(f"Filled address line 1: {address_config['line1']}")

            city_field = self.driver.find_element(By.ID, "city")
            city_field.send_keys(address_config["city"])

            try:
                state_field = self.driver.find_element(By.ID, "state")
                state_field.send_keys(address_config["state"])
            except:
                pass

            zip_field = self.driver.find_element(By.ID, "zip")
            zip_field.send_keys(address_config["zip"])
            
            self.status.emit(f"Completed address: {address_config['city']}, {address_config['state']} {address_config['zip']}")
            
        except Exception as e:
            self.log_error("Error filling address", e)
            raise

    def fill_property_section_standard(self, person_data, property_config):
        """Generic function to fill property section fields using config"""
        try:
            sale_date_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "saleDate"))
            )
            sale_date_field.send_keys(person_data['date_on_deed'])
            self.status.emit(f"Filled date of sale: {person_data['date_on_deed']}")

            street_number_field = self.driver.find_element(By.ID, "houseNumber")
            street_number_field.send_keys(property_config["street_number"])

            street_name_field = self.driver.find_element(By.ID, "houseStreetName")
            street_name_field.send_keys(property_config["street_name"])

            street_type_dropdown = Select(self.driver.find_element(By.ID, "houseStreetType"))
            street_type_dropdown.select_by_value(property_config["street_type_value"])

            post_dir_dropdown = Select(self.driver.find_element(By.ID, "housePostDirection"))
            post_dir_dropdown.select_by_value(property_config["post_direction"])

            county_dropdown = Select(self.driver.find_element(By.ID, "county"))
            county_dropdown.select_by_value(property_config["county_value"])

            map_number_field = self.driver.find_element(By.ID, "mapNumber")
            map_number_field.send_keys(property_config["map_parcel"])
            
            self.status.emit("Completed property section")
            
        except Exception as e:
            self.log_error("Error filling property section", e)
            raise

    def fill_standard_property_fields(self, street_number, street_name, street_type_value, post_direction, county_value, map_parcel):
        """Fill standard property fields - DEPRECATED, use fill_property_section_standard"""
        street_number_field = self.driver.find_element(By.ID, "houseNumber")
        street_number_field.send_keys(street_number)

        street_name_field = self.driver.find_element(By.ID, "houseStreetName")
        street_name_field.send_keys(street_name)

        street_type_dropdown = Select(self.driver.find_element(By.ID, "houseStreetType"))
        street_type_dropdown.select_by_value(street_type_value)

        post_dir_dropdown = Select(self.driver.find_element(By.ID, "housePostDirection"))
        post_dir_dropdown.select_by_value(post_direction)

        county_dropdown = Select(self.driver.find_element(By.ID, "county"))
        county_dropdown.select_by_value(county_value)

        map_number_field = self.driver.find_element(By.ID, "mapNumber")
        map_number_field.send_keys(map_parcel)

    def fill_tax_computation_section(self, person_data, tax_config):
        """Generic function to fill tax computation (financial) section using config"""
        try:
            if "exempt_code" in tax_config and tax_config["exempt_code"] != "None":
                try:
                    exempt_dropdown = Select(self.driver.find_element(By.ID, "exemptCode"))
                    exempt_dropdown.select_by_visible_text(tax_config["exempt_code"])
                    self.status.emit(f"Selected exempt code: {tax_config['exempt_code']}")
                except Exception as e:
                    self.status.emit(f"Could not set exempt code: {str(e)}")
            
            sales_price_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "actualValue"))
            )
            sales_price_field.send_keys(person_data['sales_price'])
            self.status.emit(f"Filled sales price: {person_data['sales_price']}")

            fair_market_value_field = self.driver.find_element(By.ID, "fairMarketValue")
            fair_market_value_field.send_keys(tax_config["fair_market_value"])

            liens_field = self.driver.find_element(By.ID, "liensAndEncumberances")
            liens_field.send_keys(tax_config["liens_encumbrances"])
            
            self.status.emit("Completed tax computation section")
            
        except Exception as e:
            self.log_error("Error filling tax computation section", e)
            raise

    def fill_standard_financial_fields(self, sales_price, fair_market_value="0", liens_value="0"):
        """Fill standard financial fields - DEPRECATED, use fill_tax_computation_section"""
        sales_price_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "actualValue"))
        )
        sales_price_field.send_keys(sales_price)
        self.status.emit(f"Filled sales price: {sales_price}")

        fair_market_value_field = self.driver.find_element(By.ID, "fairMarketValue")
        fair_market_value_field.send_keys(fair_market_value)

        liens_field = self.driver.find_element(By.ID, "liensAndEncumberances")
        liens_field.send_keys(liens_value)

    def submit_form(self):
        """Submit the PT-61 form"""
        checkboxes = ["chkCounty", "chkAccept", "chkTaxAccept"]
        for checkbox_id in checkboxes:
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, checkbox_id))
            )
            checkbox.click()

        submit_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnSubmitPT61"))
        )
        submit_button.click()
        self.status.emit("Clicked 'Submit PT-61 Form' button")

    def save_pdf(self, filename):
        """Save the generated PDF and optionally add to stack"""
        iframe_locator = (By.CSS_SELECTOR, "#dvPT61IFrame iframe")
        WebDriverWait(self.driver, 30).until(EC.presence_of_element_located(iframe_locator))
        self.status.emit("PT-61 iframe found")

        iframe = self.driver.find_element(*iframe_locator)

        iframe_src = iframe.get_attribute('src')
        self.status.emit(f"Iframe src: {iframe_src}")

        self.driver.execute_script(f"window.open('{iframe_src}', '_blank');")

        self.driver.switch_to.window(self.driver.window_handles[-1])

        time.sleep(5)

        file_path = os.path.join(self.save_location, filename)
        file_path = os.path.normpath(file_path)

        pyautogui.hotkey('ctrl', 's')
        time.sleep(2)
        pyautogui.write(file_path)
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(2)

        self.status.emit(f"Saved PDF as: {filename}")

        if self.document_stacking:
            self.pdf_stacker.add_pdf(file_path)
            self.status.emit(f"Added to document stack: {filename}")

        self.driver.close()

        self.driver.switch_to.window(self.driver.window_handles[0])

    def finalize_document_stacking(self):
        """Create the combined PDF if document stacking is enabled"""
        if self.document_stacking:
            try:
                self.status.emit("Starting document stacking process...")
                
                stack_info = self.pdf_stacker.get_stack_info()
                self.status.emit(f"Processing {stack_info['total_files']} PDF files for stacking")
                
                if stack_info['total_files'] == 0:
                    self.status.emit("No PDF files to stack")
                    return
                
                combined_pdf_path = self.pdf_stacker.create_stacked_pdf(
                    self.save_location, 
                    self.version
                )
                
                self.status.emit(f"Document stacking completed!")
                self.status.emit(f"Combined PDF: {os.path.basename(combined_pdf_path)}")
                
            except Exception as e:
                self.status.emit(f"Error during document stacking: {str(e)}")
                self.status.emit("Individual PDF files are still available")

    def cleanup(self):
        """Clean up resources"""
        if self.document_stacking:
            self.finalize_document_stacking()
        
        if self.driver:
            if self.keep_browser_open_on_error:
                self.status.emit("ERROR - Browser left open for inspection")
                print("\n" + "*"*60)
                print("BROWSER LEFT OPEN FOR DEBUGGING")
                print("Copy the page HTML and share it for troubleshooting.")
                print("*"*60 + "\n")
            else:
                self.driver.quit()
                self.status.emit("Browser closed.")

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
        """Generate filename for PDF using config pattern"""
        try:
            file_naming = self.config["constants"]["file_naming"]
            pattern = file_naming["pattern"]
            
            filename = pattern.format(
                last_name=person_data['individual_name']['last'],
                contract_num=person_data['contract_number'],
                contract_number=person_data['contract_number'],
                first_name=person_data['individual_name']['first'],
                middle_name=person_data['individual_name']['middle']
            )
            
            import re
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            return filename
            
        except Exception as e:
            self.status.emit(f"Warning: Using fallback filename pattern: {str(e)}")
            last_name = person_data['individual_name']['last']
            contract_num = person_data['contract_number']
            return f"{last_name}_{contract_num}_PT61.pdf"

    def process_person(self, person_data, index, total_count):
        """Process a single person through the form - template method"""
        self.status.emit(f"Processing person {index} of {total_count}")

        try:
            self.navigate_to_form()

            self.fill_seller_section(person_data)
            self.click_next_step()

            self.fill_buyer_section(person_data)
            self.click_next_step()

            self.fill_property_section(person_data)
            self.click_next_step()

            self.handle_alert_if_present()

            self.fill_financial_section(person_data)
            self.click_next_step()

            self.submit_form()
            filename = self.generate_filename(person_data)
            self.save_pdf(filename)

            progress = int((index / total_count) * 100)
            self.progress.emit(progress)
            
        except Exception as e:
            self.log_error(f"Error processing person {index}", e)
            raise