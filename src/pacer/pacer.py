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

    def __init__(self, excel_path: str, username: str, password: str, save_location: str, 
                 use_4digit_mode: bool = False, environment: str = "prod"):
        super().__init__()
        self.excel_path = excel_path
        self.username = username
        self.password = password
        self.save_location = save_location
        self.use_4digit_mode = use_4digit_mode
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
        if not last_name or not isinstance(last_name, str):
            return ""
            
        name = last_name.strip().upper()
        
        suffixes = [
            "JR", "JR.", "SR", "SR.", "II", "III", "IV", 
            "V", "VI", "VII", "VIII", "IX", "X"
        ]
        
        for suffix in suffixes:
            if name.endswith(f" {suffix}"):
                name = name[:-(len(suffix) + 1)].strip()
        
        if "-" in name:
            name = name.split("-")[-1].strip()
        
        for char in ",.":
            name = name.replace(char, " ")
        
        special_chars = r"'`\"&@#$%*()[]{}\/|:;?!+=<>"
        for char in special_chars:
            name = name.replace(char, "")
        
        name = " ".join(name.split())
        
        return name

    def search_by_ssn9(self, ssn: str, last_name: str) -> Optional[Dict[str, Any]]:
        if not self.auth_token:
            self.error.emit("Not authenticated. Authentication required.")
            return None
            
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
                self.api_responses.append({
                    "searchMode": "9-digit",
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

    def search_by_ssn4(self, ssn4: str, last_name: str, first_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.auth_token:
            self.error.emit("Not authenticated. Authentication required.")
            return None
            
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
            "ssn4": ssn4,
            "jurisdictionType": "bk"
        }
        
        try:
            response = requests.post(url, headers=headers, json=search_data)
            
            if response.status_code == 200:
                result = response.json()
                self.api_responses.append({
                    "searchMode": "4-digit",
                    "ssn4": ssn4,
                    "originalLastName": last_name,
                    "sanitizedLastName": sanitized_last_name,
                    "excelFirstName": first_name,
                    "timestamp": datetime.now().isoformat(),
                    "matchCount": len(result.get("content", [])),
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
        try:
            if not response or "content" not in response or "pageInfo" not in response:
                return "FAILED: Invalid API Response"

            if (not response["content"] and 
                response["pageInfo"]["totalElements"] == 0):
                return "No Bankruptcy"

            for case in response["content"]:
                court_case = case.get("courtCase", {})
                effective_date_closed = court_case.get("effectiveDateClosed")
                
                if not effective_date_closed:
                    return "OPEN Bankruptcy Found"

            return "Closed Bankruptcy"

        except Exception as e:
            return "FAILED: Invalid API Response"

    def format_multiple_matches(self, response: Dict[str, Any]) -> str:
        try:
            content = response.get("content", [])
            match_count = len(content)
            
            if match_count == 0:
                return "No Bankruptcy"
            
            result_lines = [f"REVIEW REQUIRED - {match_count} Match{'es' if match_count > 1 else ''}"]
            
            for idx, case in enumerate(content, 1):
                court_case = case.get("courtCase", {})
                
                first_name = case.get("firstName", "")
                middle_name = case.get("middleName", "")
                last_name = case.get("lastName", "")
                
                full_name_parts = [first_name, middle_name, last_name]
                full_name = " ".join([p for p in full_name_parts if p]).strip()
                
                case_number = court_case.get("caseNumberFull", "Unknown")
                date_filed = court_case.get("dateFiled", "Unknown")
                effective_date_closed = court_case.get("effectiveDateClosed")
                
                status = "OPEN" if not effective_date_closed else f"Closed {effective_date_closed}"
                
                match_line = f"\n{idx}. {full_name} | Case: {case_number} | Filed: {date_filed} | Status: {status}"
                result_lines.append(match_line)
            
            return "".join(result_lines)
            
        except Exception as e:
            return f"FAILED: Error formatting results - {str(e)}"

    def process_single_person(self, person: Dict, account_number: str, row_index: int) -> bool:
        try:
            original_last_name = person['last_name']
            sanitized_last_name = self.sanitize_last_name(original_last_name)
            ssn_value = person['ssn']
            
            status_msg = f"Searching for {sanitized_last_name} (SSN: {'****' if self.use_4digit_mode else ssn_value[-4:]})..."
            if sanitized_last_name != original_last_name:
                status_msg = f"Searching for {sanitized_last_name} (original: {original_last_name}) (SSN: {'****' if self.use_4digit_mode else ssn_value[-4:]})..."
            
            if self.use_4digit_mode:
                response = self.search_by_ssn4(ssn_value, person['last_name'], person.get('first_name'))
            else:
                response = self.search_by_ssn9(ssn_value, person['last_name'])
            
            if response is None:
                error_msg = f"Failed to get API response for {sanitized_last_name}"
                self.failed_searches.append((person, error_msg))
                self.update_excel_with_failure(row_index, person, "FAILED: API Error")
                self.status.emit(f"{status_msg} FAILED: API Error")
                return False

            if self.use_4digit_mode:
                match_count = len(response.get("content", []))
                
                if match_count == 0:
                    result_status = "No Bankruptcy"
                elif match_count == 1:
                    result_status = self.interpret_bankruptcy_status(response)
                else:
                    result_status = self.format_multiple_matches(response)
            else:
                result_status = self.interpret_bankruptcy_status(response)
            
            if result_status == "OPEN Bankruptcy Found":
                output_msg = f"{status_msg} OPEN Bankruptcy Found"
            else:
                output_msg = f"{status_msg} {result_status}"
            
            self.status.emit(output_msg)
            
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
        failure_msg = f"FAILED: {error_msg}"
        self.excel_processor.update_results(
            row_index,
            person['person_number'],
            failure_msg
        )

    def save_api_responses(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_suffix = "4digit" if self.use_4digit_mode else "9digit"
            filename = f"pacer_api_responses_{mode_suffix}_{timestamp}.json"
            filepath = os.path.join(self.save_location, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.api_responses, f, indent=2)
            
            self.status.emit(f"API responses saved to {filepath}")
            return True
        except Exception as e:
            self.error.emit(f"Failed to save API responses: {str(e)}")
            return False

    def run(self):
        try:
            from .excel_processor import PACERExcelProcessor
            
            try:
                self.excel_processor = PACERExcelProcessor(self.excel_path, self.use_4digit_mode)
            except TypeError as e:
                self.error.emit(f"Excel processor initialization failed: {str(e)}. Make sure you've updated excel_processor.py with the new code.")
                self.finished.emit()
                return
            
            mode_text = "4-digit SSN" if self.use_4digit_mode else "9-digit SSN"
            self.status.emit(f"Processing Excel file ({mode_text} mode)...")
            
            try:
                success, data = self.excel_processor.process_excel()
            except Exception as e:
                self.error.emit(f"Excel file processing error: {str(e)}")
                self.finished.emit()
                return

            if not success:
                self.error.emit(f"Excel processing failed: {data}")
                self.finished.emit()
                return

            if not data:
                self.status.emit("No new records to process.")
                self.finished.emit()
                return

            self.status.emit("Authenticating with PACER...")
            if not self.authenticate():
                self.finished.emit()
                return

            total_searches = sum(len(row['people']) for row in data)
            completed_searches = 0

            for row in data:
                for person in row['people']:
                    try:
                        self.process_single_person(person, row['account_number'], row['excel_row_index'])
                    except Exception as e:
                        error_msg = f"Error processing {person.get('last_name', 'Unknown')}: {str(e)}"
                        self.status.emit(error_msg)
                        self.failed_searches.append((person, error_msg))
                    
                    completed_searches += 1
                    progress_percentage = int((completed_searches / total_searches) * 100)
                    self.progress.emit(progress_percentage)

            try:
                self.excel_processor.apply_highlighting()
            except Exception as e:
                self.status.emit(f"Warning: Could not apply highlighting: {str(e)}")

            try:
                self.save_api_responses()
            except Exception as e:
                self.status.emit(f"Warning: Could not save API responses: {str(e)}")

            if self.failed_searches:
                failure_message = f"\n\nFAILED SEARCHES ({len(self.failed_searches)}):"
                for person, error in self.failed_searches:
                    failure_message += f"\n- {person.get('last_name', 'Unknown')} (SSN: {person.get('ssn', 'Unknown')}): {error}"
                self.status.emit(f"Completed with {len(self.failed_searches)} failed searches.{failure_message}")
            else:
                self.status.emit("All searches completed successfully")

            self.finished.emit()

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            self.error.emit(f"Critical error during automation:\n\n{str(e)}\n\nFull trace:\n{error_detail}")
            self.finished.emit()