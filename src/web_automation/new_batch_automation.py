# File: web_automation/new_batch_automation.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_automation import BasePT61Automation
from .pt61_config import get_version_config

class NewBatchAutomation(BasePT61Automation):
    """PT-61 New Batch automation implementation"""
    
    def __init__(self, excel_path, browser, username, password, save_location, version):
        super().__init__(excel_path, browser, username, password, save_location, version)
        
        # Get version config
        _, self.config = get_version_config(version)
        self.constants = self.config["constants"]

    def fill_seller_section(self, person_data):
        """Fill seller section for New Batch version"""
        # Click business radio button
        business_radio = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='businessFlag' and @value='1']"))
        )
        business_radio.click()

        # Fill business name
        business_name_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "businessName"))
        )
        business_name = self.constants["seller_section"]["address"]["line1"]
        business_name_field.send_keys(business_name)

        # Fill address
        address_field = self.driver.find_element(By.ID, "street1")
        address_line = self.constants["seller_section"]["address"]["line2"]
        address_field.send_keys(address_line)

        # Fill city
        city_field = self.driver.find_element(By.ID, "city")
        city = self.constants["seller_section"]["address"]["city"]
        city_field.send_keys(city)

        # Fill zip code
        zip_field = self.driver.find_element(By.ID, "zip")
        zip_code = self.constants["seller_section"]["address"]["zip"]
        zip_field.send_keys(zip_code)

    def fill_buyer_section(self, person_data):
        """Fill buyer section for New Batch version"""
        # Fill individual name fields
        first_name_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "firstName"))
        )
        first_name_field.send_keys(person_data['individual_name']['first'])
        self.status.emit(f"Filled out first name: {person_data['individual_name']['first']}")

        middle_name_field = self.driver.find_element(By.ID, "middleName")
        middle_name_field.send_keys(person_data['individual_name']['middle'])
        self.status.emit(f"Filled out middle name: {person_data['individual_name']['middle']}")

        last_name_field = self.driver.find_element(By.ID, "lastName")
        last_name_field.send_keys(person_data['individual_name']['last'])
        self.status.emit(f"Filled out last name: {person_data['individual_name']['last']}")

        # Fill address from constants
        address_field = self.driver.find_element(By.ID, "street1")
        address_line = self.constants["seller_section"]["address"]["line2"]
        address_field.send_keys(address_line)

        city_field = self.driver.find_element(By.ID, "city")
        city = self.constants["seller_section"]["address"]["city"]
        city_field.send_keys(city)

        zip_field = self.driver.find_element(By.ID, "zip")
        zip_code = self.constants["seller_section"]["address"]["zip"]
        zip_field.send_keys(zip_code)

        # Handle additional sellers if present
        if ('additional_name' in person_data and 
            person_data['additional_name'] and 
            any(person_data['additional_name'].values())):
            try:
                # Fill out additional first name
                additional_first_name_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "AdditionalFirstName"))
                )
                additional_first_name_field.send_keys(person_data['additional_name']['first'])
                self.status.emit(f"Filled out additional first name: {person_data['additional_name']['first']}")

                # Fill out additional middle name
                additional_middle_name_field = self.driver.find_element(By.ID, "AdditionalMiddleName")
                additional_middle_name_field.send_keys(person_data['additional_name']['middle'])
                self.status.emit(f"Filled out additional middle name: {person_data['additional_name']['middle']}")

                # Fill out additional last name
                additional_last_name_field = self.driver.find_element(By.ID, "AdditionalLastName")
                additional_last_name_field.send_keys(person_data['additional_name']['last'])
                self.status.emit(f"Filled out additional last name: {person_data['additional_name']['last']}")

                # Click "Add to Additional Names" button
                add_additional_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btnAdd"))
                )
                add_additional_button.click()
                self.status.emit("Added additional name successfully")
            except Exception as e:
                self.status.emit(f"Error adding additional name: {str(e)}")
        else:
            self.status.emit("No additional name to process, skipping this part")

    def fill_property_section(self, person_data):
        """Fill property section for New Batch version"""
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
        """Fill financial section for New Batch version"""
        financial_config = self.constants["financial_section"]
        self.fill_standard_financial_fields(
            sales_price=person_data['sales_price'],
            fair_market_value=financial_config["fair_market_value"],
            liens_value=financial_config["liens_encumbrances"]
        )

    def generate_filename(self, person_data):
        """Generate filename for New Batch version"""
        # Pattern: {last_name}_{contract_num}_PT61.pdf
        last_name = person_data['individual_name']['last']
        contract_num = person_data['contract_number']
        return f"{last_name}_{contract_num}_PT61.pdf"