# File: pacer/pacer.py
from PyQt6.QtCore import QObject, pyqtSignal
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import requests

class PACERAutomationWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, excel_path: str, username: str, password: str, save_location: str, environment: str = "prod"):
        super().__init__()
        self.excel_path = excel_path
        self.username = username
        self.password = password
        self.save_location = save_location
        self.environment = environment
        self.excel_processor = None
        self.failed_searches = []
        self.api_responses = []
        self.auth_token = None
        self.base_urls = {
            "qa": {
                "auth": "https://qa-login.uscourts.gov",
                "api": "https://qa-pcl.uscourts.gov/pcl-public-api/rest"
            },
            "prod": {
                "auth": "https://pacer.login.uscourts.gov",
                "api": "https://pcl.uscourts.gov/pcl-public-api/rest"
            }
        }

    def authenticate(self) -> bool:
        """Authenticate with PACER and get token"""
        auth_url = f"{self.base_urls[self.environment]['auth']}/services/cso-auth"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        auth_data = {
            "loginId": self.username,
            "password": self.password,
            "redactFlag": "1"
        }
        
        try:
            response = requests.post(auth_url, headers=headers, json=auth_data)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("loginResult") == "0":
                self.auth_token = response_data.get("nextGenCSO")
                return True
            else:
                self.error.emit(f"Authentication failed: {response_data.get('errorDescription')}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"Authentication request failed: {str(e)}")
            return False

    def sanitize_last_name(self, last_name: str) -> str:
        """
        Sanitize last name for PACER API requirements.
        Handles suffixes, prefixes, hyphenated names, and special characters.
        """
        if not last_name or not isinstance(last_name, str):
            return ""
            
        # Convert to uppercase and trim whitespace
        name = last_name.strip().upper()
        
        # List of suffixes to remove
        suffixes = [
            "JR", "JR.", "SR", "SR.", "II", "III", "IV", 
            "V", "VI", "VII", "VIII", "IX", "X"
        ]
        
        # Remove suffixes
        for suffix in suffixes:
            if name.endswith(f" {suffix}"):
                name = name[:-(len(suffix) + 1)].strip()
        
        # Handle hyphenated names - take the last part
        if "-" in name:
            name = name.split("-")[-1].strip()
        
        # Replace commas and periods with spaces
        for char in ",.":
            name = name.replace(char, " ")
        
        # Remove all other special characters
        special_chars = r"'`\"&@#$%*()[]{}\/|:;?!+=<>"
        for char in special_chars:
            name = name.replace(char, "")
        
        # Collapse multiple spaces into single space
        name = " ".join(name.split())
        
        return name

    def search_bankruptcy_by_ssn(self, ssn: str, last_name: str) -> Optional[Dict[str, Any]]:
        """Search for bankruptcy cases by SSN and last name"""
        if not self.auth_token:
            self.error.emit("Not authenticated. Authentication required.")
            return None
            
        # Sanitize the last name before making the API call
        sanitized_last_name = self.sanitize_last_name(last_name)
        
        if not sanitized_last_name:
            self.error.emit("Invalid last name after sanitization")
            return None
            
        url = f"{self.base_urls[self.environment]['api']}/parties/find"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-NEXT-GEN-CSO": self.auth_token
        }
        
        search_data = {
            "lastName": sanitized_last_name,
            "ssn": ssn,
            "jurisdictionType": "bk"
        }
        
        try:
            response = requests.post(url, headers=headers, json=search_data)
            
            if response.status_code == 200:
                result = response.json()
                # Store the API response with both original and sanitized names
                self.api_responses.append({
                    "ssn": ssn,
                    "originalLastName": last_name,
                    "sanitizedLastName": sanitized_last_name,
                    "timestamp": datetime.now().isoformat(),
                    "response": result
                })
                return result
            else:
                error_msg = f"API request failed with status {response.status_code}"
                self.error.emit(error_msg)
                return None
                
        except requests.exceptions.RequestException as e:
            self.error.emit(f"API request failed: {str(e)}")
            return None

    def interpret_bankruptcy_status(self, response: Dict[str, Any]) -> str:
        """
        Interpret the bankruptcy status from API response
        
        Returns one of:
        - "No Bankruptcy"
        - "Closed Bankruptcy"
        - "OPEN Bankruptcy Found"
        - "FAILED: Invalid API Response"
        """
        try:
            # Check for valid response structure
            if not response or "content" not in response or "pageInfo" not in response:
                print("DEBUG: Invalid response structure")
                return "FAILED: Invalid API Response"

            # Check for No Bankruptcy
            if (not response["content"] and 
                response["pageInfo"]["totalElements"] == 0):
                print("DEBUG: No bankruptcy cases found")
                return "No Bankruptcy"

            print(f"DEBUG: Found {len(response['content'])} case(s)")
            
            # Check each case for open status
            for case_idx, case in enumerate(response["content"]):
                court_case = case.get("courtCase", {})
                case_number = court_case.get("caseNumberFull", "Unknown")
                effective_date_closed = court_case.get("effectiveDateClosed")
                
                print(f"\nDEBUG: Analyzing case {case_number}")
                print(f"  - Filed: {court_case.get('dateFiled')}")
                print(f"  - Effective Date Closed: {effective_date_closed}")
                
                # If any case lacks an effectiveDateClosed, it's open
                if not effective_date_closed:
                    print(f"DEBUG: Case {case_number} is OPEN - no effective close date")
                    return "OPEN Bankruptcy Found"

            print("\nDEBUG: All cases have effective close dates - marking as Closed")
            return "Closed Bankruptcy"

        except Exception as e:
            print(f"DEBUG: Error interpreting bankruptcy status: {str(e)}")
            return "FAILED: Invalid API Response"

    def process_single_person(self, person: Dict, account_number: str, row_index: int) -> bool:
        """Process a single person's bankruptcy search"""
        try:
            original_last_name = person['last_name']
            sanitized_last_name = self.sanitize_last_name(original_last_name)
            
            # Modified status message to focus on sanitized name
            status_msg = f"Searching for {sanitized_last_name} (SSN: {person['ssn']})..."
            if sanitized_last_name != original_last_name:
                status_msg = f"Searching for {sanitized_last_name} (original: {original_last_name}) (SSN: {person['ssn']})..."
            
            response = self.search_bankruptcy_by_ssn(person['ssn'], person['last_name'])
            if response is None:
                error_msg = f"Failed to get API response for {sanitized_last_name}"
                self.failed_searches.append((person, error_msg))
                self.update_excel_with_failure(row_index, person, "FAILED: API Error")
                self.status.emit(f"{status_msg} FAILED: API Error")
                return False

            result_status = self.interpret_bankruptcy_status(response)
            
            # Format output message based on status
            if result_status == "OPEN Bankruptcy Found":
                output_msg = f"{status_msg} 🚨 {result_status} 🚨"
            else:
                output_msg = f"{status_msg} {result_status}"
            
            self.status.emit(output_msg)
            
            # Update Excel with results
            update_success, _ = self.excel_processor.update_results(
                row_index,
                person['person_number'],
                result_status
            )
            
            if not update_success:
                self.status.emit(f"Warning: Failed to update Excel for {sanitized_last_name}")
            
            return True

        except Exception as e:
            error_msg = f"Error processing {sanitized_last_name}: {str(e)}"
            self.failed_searches.append((person, error_msg))
            self.update_excel_with_failure(row_index, person, error_msg)
            self.status.emit(f"{status_msg} FAILED: {str(e)}")
            return False

    def update_excel_with_failure(self, row_index: int, person: Dict, error_msg: str):
        """Update Excel file with failure message"""
        failure_msg = f"FAILED: {error_msg}"
        self.excel_processor.update_results(
            row_index,
            person['person_number'],
            failure_msg
        )

    def save_api_responses(self):
        """Save all API responses to a JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pacer_api_responses_{timestamp}.json"
            filepath = os.path.join(self.save_location, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.api_responses, f, indent=2)
            
            self.status.emit(f"API responses saved to {filepath}")
            return True
        except Exception as e:
            self.error.emit(f"Failed to save API responses: {str(e)}")
            return False

    def run(self):
        """Main execution method"""
        try:
            # Process Excel file
            from .excel_processor import PACERExcelProcessor
            self.excel_processor = PACERExcelProcessor(self.excel_path)
            
            self.status.emit("Processing Excel file...")
            success, data = self.excel_processor.process_excel()

            if not success:
                self.error.emit(f"Excel processing failed: {data}")
                return

            if not data:
                self.status.emit("No new records to process.")
                self.finished.emit()
                return

            # Authenticate with PACER
            self.status.emit("Authenticating with PACER...")
            if not self.authenticate():
                return

            total_searches = sum(len(row['people']) for row in data)
            completed_searches = 0

            # Process all people from the data
            for row in data:
                for person in row['people']:
                    self.process_single_person(person, row['account_number'], row['excel_row_index'])
                    
                    completed_searches += 1
                    progress_percentage = int((completed_searches / total_searches) * 100)
                    self.progress.emit(progress_percentage)

            # Apply highlighting to all marked cells at once
            self.excel_processor.apply_highlighting()

            # Save API responses
            self.save_api_responses()

            if self.failed_searches:
                failure_message = "\n\nFAILED SEARCHES:"
                for person, error in self.failed_searches:
                    failure_message += f"\n- {person['last_name']} (SSN: {person['ssn']}): {error}"
                self.status.emit(f"Completed with {len(self.failed_searches)} failed searches.{failure_message}")
            else:
                self.status.emit("All searches completed successfully")

            self.finished.emit()

        except Exception as e:
            self.error.emit(f"Error during automation: {str(e)}")