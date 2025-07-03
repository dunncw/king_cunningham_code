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

    def process_person(self, person_data, index, total_count):
        """Process a single person through the form - foreclosures specific flow"""
        self.status.emit(f"Processing person {index} of {total_count} - Foreclosures Version")

        # Navigate to form
        self.navigate_to_form()

        # Fill seller section (individual like deedbacks)
        self.status.emit("Filling seller section (individual)...")
        self.fill_seller_section(person_data)
        
        self.status.emit("Clicking Next Step to move to buyer section...")
        self.click_next_step()
        
        # Fill buyer section (business like deedbacks)
        self.status.emit("Filling buyer section (business)...")
        self.fill_buyer_section(person_data)
        
        # Clear additional buyers section (foreclosures requirement)
        self.status.emit("Clearing additional buyers section...")
        self.clear_additional_buyers_if_needed()
        
        self.status.emit("Clicking Next Step to move to property section...")
        self.click_next_step()
        
        # Fill property section (simplified for foreclosures)
        self.status.emit("Filling property section (simplified)...")
        self.fill_property_section(person_data)
        
        self.status.emit("Clicking Next Step to move to tax computation section...")
        self.click_next_step()
        
        self.status.emit("Handling any alerts...")
        self.handle_alert_if_present()
        
        # Fill tax computation section
        self.status.emit("Filling tax computation section...")
        self.fill_financial_section(person_data)
        
        self.status.emit("Clicking Next Step to move to submission...")
        self.click_next_step()
        
        # Submit form and save PDF
        self.status.emit("Submitting form...")
        self.submit_form()
        
        self.status.emit("Generating filename and saving PDF...")
        filename = self.generate_filename(person_data)
        self.save_pdf(filename)
        
        self.status.emit("Completed foreclosures automation flow!")

        # Update progress
        progress = int((index / total_count) * 100)
        self.progress.emit(progress)
        
        self.status.emit(f"Completed automation for foreclosures person {index}")

    def fill_seller_section(self, person_data):
        """Fill seller section for Foreclosures version - Individual seller (same as deedbacks)"""
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

        # Fill address from constants using generic function
        seller_address = self.constants["seller_section"]["address"]
        self.fill_primary_mailing_address(seller_address)
        self.status.emit("Filled seller mailing address from config")

    def fill_buyer_section(self, person_data):
        """Fill buyer section for Foreclosures version - Fixed business buyer"""
        self.status.emit("Filling buyer section - Fixed business buyer")
        
        # Click business radio button
        business_radio = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='businessFlag' and @value='1']"))
        )
        business_radio.click()
        self.status.emit("Selected Business radio button")

        # Fill business name from constants (fixed for foreclosures)
        business_name_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "businessName"))
        )
        buyer_name = self.constants["buyer_section"]["name"]
        business_name_field.send_keys(buyer_name)
        self.status.emit(f"Filled buyer business name: {buyer_name}")

        # Fill address using generic function (same_as_seller means use seller address)
        buyer_address = self.constants["seller_section"]["address"]  # Uses same address
        self.fill_primary_mailing_address(buyer_address)
        self.status.emit("Filled buyer mailing address (same as seller)")

    def clear_additional_buyers_if_needed(self):
        """Clear additional buyers section if it auto-filled"""
        self.status.emit("Checking and clearing additional buyers section...")
        
        try:
            # Check if additional individual radio button is selected
            individual_radio = self.driver.find_element(By.ID, "AdditionalIndividualFlag")
            if individual_radio.is_selected():
                individual_radio.click()  # Unselect it
                self.status.emit("Cleared additional individual radio button")
            
            # Clear additional individual name fields
            additional_fields = [
                "AdditionalFirstName",
                "AdditionalMiddleName", 
                "AdditionalLastName"
            ]
            
            for field_id in additional_fields:
                try:
                    field = self.driver.find_element(By.ID, field_id)
                    if field.get_attribute("value"):  # Only clear if has value
                        field.clear()
                        self.status.emit(f"Cleared field: {field_id}")
                except:
                    pass  # Field might not exist or not accessible
            
            # Check if additional business radio button is selected
            business_radio = self.driver.find_element(By.ID, "AdditionalBusinessFlag")
            if business_radio.is_selected():
                business_radio.click()  # Unselect it
                self.status.emit("Cleared additional business radio button")
            
            # Clear additional business name field
            try:
                business_field = self.driver.find_element(By.ID, "AdditionalBusinessName")
                if business_field.get_attribute("value"):
                    business_field.clear()
                    self.status.emit("Cleared additional business name field")
            except:
                pass
            
            # Clear the additional names list if it has any entries
            try:
                additional_names_select = self.driver.find_element(By.ID, "AdditionalNames")
                # Check if there are any options (other than empty)
                options = additional_names_select.find_elements(By.TAG_NAME, "option")
                if len(options) > 0:
                    # Select and delete any entries
                    for option in options:
                        if option.text.strip() and option.text.strip() != "":  # Not empty
                            option.click()  # Select the option
                            try:
                                delete_button = self.driver.find_element(By.ID, "btnDelete")
                                delete_button.click()
                                self.status.emit(f"Deleted additional name: {option.text}")
                            except:
                                pass
            except:
                pass
            
            self.status.emit("Additional buyers section cleared and ready")
            
        except Exception as e:
            self.status.emit(f"Note: Could not fully clear additional buyers: {str(e)}")
            # Continue anyway - this is not critical to fail on

    def fill_property_section(self, person_data):
        """Fill property section for Foreclosures version - Simplified (date, county, parcel only)"""
        self.status.emit("Filling property section - Foreclosures simplified version")
        
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
        self.status.emit(f"Selected county: {property_config['county_value']}")

        # Fill out map/parcel number
        map_number_field = self.driver.find_element(By.ID, "mapNumber")
        map_number_field.send_keys(property_config["map_parcel"])
        self.status.emit(f"Filled map/parcel: {property_config['map_parcel']}")

    def fill_financial_section(self, person_data):
        """Fill financial section (tax computation) for Foreclosures version"""
        self.status.emit("Filling tax computation section - Foreclosures version")
        
        # Select exempt code - "First Transferee Foreclosure" (value="FTF")
        try:
            exempt_dropdown = Select(self.driver.find_element(By.ID, "exemptCode"))
            exempt_dropdown.select_by_value("FTF")  # Using the option value
            self.status.emit("Selected 'First Transferee Foreclosure' exempt code (FTF)")
        except Exception as e:
            self.status.emit(f"Could not set exempt code: {str(e)}")

        # Fill actual value (sales price) from Excel data
        sales_price_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "actualValue"))
        )
        sales_price_field.send_keys(person_data['sales_price'])
        self.status.emit(f"Filled actual value (sales price): {person_data['sales_price']}")

        # Note: Fair market value and liens fields are auto-filled by website for foreclosures
        self.status.emit("Website will auto-fill fair market value and liens fields")

    def generate_filename(self, person_data):
        """Generate filename for Foreclosures version"""
        # Pattern: {contract_num}_{last_name}_PT61.pdf (different order than other versions)
        contract_num = person_data['contract_number']
        last_name = person_data['individual_name']['last']
        return f"{contract_num}_{last_name}_PT61.pdf"