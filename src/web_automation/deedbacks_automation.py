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

    def process_person(self, person_data, index, total_count):
        """Process a single person through the form - deedbacks specific flow"""
        self.status.emit(f"Processing person {index} of {total_count} - Deedbacks Version")

        # Navigate to form
        self.navigate_to_form()

        # DEVELOPMENT PAUSE: Now we'll fill seller section and move to buyer section
        self.status.emit("🚀 DEV: Filling seller section...")
        self.fill_seller_section(person_data)
        
        self.status.emit("🚀 DEV: Clicking Next Step to move to buyer section...")
        self.click_next_step()
        
        self.status.emit("🛑 DEV: Reached buyer section - ready for HTML collection")
        self.status.emit("Please inspect the buyer section HTML and press Enter to continue...")
        input("Press Enter after collecting buyer section HTML structure to continue...")

        # Future implementation will go here:
        # self.fill_seller_section(person_data)
        # self.click_next_step()
        # self.fill_buyer_section(person_data)
        # self.click_next_step()
        # self.fill_property_section(person_data)
        # self.click_next_step()
        # self.handle_alert_if_present()
        # self.fill_financial_section(person_data)
        # self.click_next_step()
        # self.submit_form()
        # filename = self.generate_filename(person_data)
        # self.save_pdf(filename)

        # Update progress
        progress = int((index / total_count) * 100)
        self.progress.emit(progress)
        
        self.status.emit(f"✅ DEV: Completed development pause for person {index}")

    def fill_seller_section(self, person_data):
        """Fill seller section for Deedbacks version - Individual seller"""
        self.status.emit("Filling seller section - Individual seller")
        
        # Fill individual name fields (Individual radio button is pre-selected)
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

        # Fill address from constants (same as new batch address handling)
        address_field = self.driver.find_element(By.ID, "street1")
        address_line = self.constants["seller_section"]["address"]["line1"]
        address_field.send_keys(address_line)
        self.status.emit(f"Filled address: {address_line}")

        city_field = self.driver.find_element(By.ID, "city")
        city = self.constants["seller_section"]["address"]["city"]
        city_field.send_keys(city)

        zip_field = self.driver.find_element(By.ID, "zip")
        zip_code = self.constants["seller_section"]["address"]["zip"]
        zip_field.send_keys(zip_code)

    def fill_buyer_section(self, person_data):
        """Fill buyer section for Deedbacks version - Dynamic business buyer"""
        # TODO: Implement after seller section is complete
        self.status.emit("🚧 Buyer section implementation pending...")
        pass

    def fill_property_section(self, person_data):
        """Fill property section for Deedbacks version"""
        # TODO: Implement after buyer section is complete
        self.status.emit("🚧 Property section implementation pending...")
        pass

    def fill_financial_section(self, person_data):
        """Fill financial section for Deedbacks version"""
        # TODO: Implement after property section is complete
        self.status.emit("🚧 Financial section implementation pending...")
        pass

    def generate_filename(self, person_data):
        """Generate filename for Deedbacks version"""
        # Pattern: {last_name}_{contract_num}_PT61.pdf
        last_name = person_data['individual_name']['last']
        contract_num = person_data['contract_number']
        return f"{last_name}_{contract_num}_PT61.pdf"