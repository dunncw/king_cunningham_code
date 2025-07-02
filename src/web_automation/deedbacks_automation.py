# File: web_automation/deedbacks_automation.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_automation import BasePT61Automation
from .pt61_config import get_version_config

class DeedbacksAutomation(BasePT61Automation):
    """PT-61 Deedbacks automation implementation"""
    
    def __init__(self, excel_path, browser, username, password, save_location, version):
        super().__init__(excel_path, browser, username, password, save_location, version)
        
        # Get version config
        _, self.config = get_version_config(version)
        self.constants = self.config["constants"]

    def fill_seller_section(self, person_data):
        """Fill seller section for Deedbacks version"""
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
        """Fill buyer section for Deedbacks version"""
        # Click business radio button
        business_radio = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='businessFlag' and @value='1']"))
        )
        business_radio.click()

        # Determine buyer based on DB To field
        db_to_value = person_data.get('db_to', '').upper()
        buyer_options = self.constants["buyer_section"]["options"]
        
        # Default to CENTENNIAL if not found
        if db_to_value in buyer_options:
            buyer_name = buyer_options[db_to_value]
        else:
            buyer_name = buyer_options.get("CENTENNIAL", "CENTENNIAL PARK DEVELOPMENT LLC")
            self.status.emit(f"Unknown DB To value '{db_to_value}', defaulting to CENTENNIAL")

        # Fill business name
        business_name_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "businessName"))
        )
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

    def fill_property_section(self, person_data):
        """Fill property section for Deedbacks version"""
        # Fill date of sale
        sale_date_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "saleDate"))
        )
        sale_date_field.send_keys(person_data['date_on_deed'])
        self.status.emit(f"Filled out date of sale: {person_data['date_on_deed']}")

        # Fill standard property fields using constants
        property_config = self.constants["property_section"]
        self.fill_standard_property_fields(
            street_number=property_config["street_number"],
            street_name=property_config["street_name"],
            street_type_value=property_config["street_type_value"],
            post_direction=property_config["post_direction"],
            county_value=property_config["county_value"],
            map_parcel=property_config["map_parcel"]
        )

    def fill_financial_section(self, person_data):
        """Fill financial section for Deedbacks version"""
        financial_config = self.constants["financial_section"]
        self.fill_standard_financial_fields(
            sales_price=person_data['sales_price'],
            fair_market_value=financial_config["fair_market_value"],
            liens_value=financial_config["liens_encumbrances"]
        )

    def generate_filename(self, person_data):
        """Generate filename for Deedbacks version"""
        # Pattern: {last_name}_{contract_num}_PT61.pdf
        last_name = person_data['individual_name']['last']
        contract_num = person_data['contract_number']
        return f"{last_name}_{contract_num}_PT61.pdf"