# File: web_automation/foreclosures_automation.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from .base_automation import BasePT61Automation
from .pt61_config import get_version_config

class ForeclosuresAutomation(BasePT61Automation):
    """PT61 Foreclosures automation implementation"""
    
    def __init__(self, excel_path, browser, username, password, save_location, version):
        super().__init__(excel_path, browser, username, password, save_location, version)
        
        # Get version config
        _, self.config = get_version_config(version)
        self.constants = self.config["constants"]

    def fill_seller_section(self, person_data):
        """Fill seller section for Foreclosures version"""
        # Fill individual name fields
        first_name_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "firstName"))
        )
        first_name_field.send_keys(person_data['individual_name']['first'])
        self.status.emit(f"Filled out first name: {person_data['individual_name']['first']}")

        middle_name_field = self.driver.find_element(By.ID, "middleName")
        middle_name_field.send_keys(person_data['individual_name']['middle'])

        last_name_field = self.driver.find_element(By.ID, "lastName")
        last_name_field.send_keys(person_data['individual_name']['last'])

        # Fill address from constants
        address_field = self.driver.find_element(By.ID, "street1")
        address_line = self.constants["seller_section"]["address"]["line1"]
        address_field.send_keys(address_line)

        city_field = self.driver.find_element(By.ID, "city")
        city = self.constants["seller_section"]["address"]["city"]
        city_field.send_keys(city)

        zip_field = self.driver.find_element(By.ID, "zip")
        zip_code = self.constants["seller_section"]["address"]["zip"]
        zip_field.send_keys(zip_code)

    def fill_buyer_section(self, person_data):
        """Fill buyer section for Foreclosures version"""
        # Click business radio button
        business_radio = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='businessFlag' and @value='1']"))
        )
        business_radio.click()

        # Fill business name from constants
        business_name_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "businessName"))
        )
        buyer_name = self.constants["buyer_section"]["name"]
        business_name_field.send_keys(buyer_name)
        self.status.emit(f"Filled buyer: {buyer_name}")

        # Fill address (same as seller)
        address_field = self.driver.find_element(By.ID, "street1")
        address_line = self.constants["seller_section"]["address"]["line1"]
        address_field.send_keys(address_line)

        city_field = self.driver.find_element(By.ID, "city")
        city = self.constants["seller_section"]["address"]["city"]
        city_field.send_keys(city)

        zip_field = self.driver.find_element(By.ID, "zip")
        zip_code = self.constants["seller_section"]["address"]["zip"]
        zip_field.send_keys(zip_code)

        # Clear additional buyers if auto-filled (specific to foreclosures)
        if self.constants["buyer_section"].get("clear_additional_buyers", False):
            try:
                # Look for additional buyer fields and clear them if they exist
                additional_fields = ["AdditionalFirstName", "AdditionalMiddleName", "AdditionalLastName"]
                for field_id in additional_fields:
                    try:
                        field = self.driver.find_element(By.ID, field_id)
                        field.clear()
                    except:
                        pass  # Field doesn't exist or not accessible
                self.status.emit("Cleared any auto-filled additional buyers")
            except Exception as e:
                self.status.emit(f"Note: Could not clear additional buyers: {str(e)}")

    def fill_property_section(self, person_data):
        """Fill property section for Foreclosures version"""
        # Fill date of sale
        sale_date_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "saleDate"))
        )
        sale_date_field.send_keys(person_data['date_on_deed'])
        self.status.emit(f"Filled out date of sale: {person_data['date_on_deed']}")

        # For foreclosures, only fill county and map/parcel (simplified property section)
        property_config = self.constants["property_section"]
        
        # Select county
        county_dropdown = Select(self.driver.find_element(By.ID, "county"))
        county_dropdown.select_by_value(property_config["county_value"])

        # Fill out map/parcel number
        map_number_field = self.driver.find_element(By.ID, "mapNumber")
        map_number_field.send_keys(property_config["map_parcel"])

    def fill_financial_section(self, person_data):
        """Fill financial section for Foreclosures version"""
        # Fill sales price
        sales_price_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "actualValue"))
        )
        sales_price_field.send_keys(person_data['sales_price'])
        self.status.emit(f"Filled out sales price: {person_data['sales_price']}")

        # Select exempt code - "First Transferee Foreclosure"
        try:
            exempt_dropdown = Select(self.driver.find_element(By.ID, "exemptCode"))
            exempt_dropdown.select_by_visible_text("First Transferee Foreclosure")
            self.status.emit("Selected 'First Transferee Foreclosure' exempt code")
        except Exception as e:
            self.status.emit(f"Could not set exempt code: {str(e)}")

        # Note: Fields 4 & 5 are auto-filled by website according to requirements
        self.status.emit("Website will auto-fill fair market value and liens fields")

    def generate_filename(self, person_data):
        """Generate filename for Foreclosures version"""
        # Pattern: {contract_num}_{last_name}_PT61.pdf (different order than other versions)
        contract_num = person_data['contract_number']
        last_name = person_data['individual_name']['last']
        return f"{contract_num}_{last_name}_PT61.pdf"