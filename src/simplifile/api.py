import requests
import base64
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Default parties that are always added
DEFAULT_GRANTORS = [
    {"nameUnparsed": "KING CUNNINGHAM LLC TR", "type": "Organization"},
    {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "Organization"}
]

DEFAULT_GRANTEES = [
    {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "Organization"}
]

class SimplifileAPI(QObject):
    """Class for interacting with the Simplifile API"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, api_token, submitter_id, recipient_id):
        super().__init__()
        self.api_token = api_token
        self.submitter_id = submitter_id
        self.recipient_id = recipient_id
        self.base_url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{submitter_id}/packages/create"
    
    def encode_file(self, file_path):
        """Convert a file to base64 encoding"""
        try:
            with open(file_path, "rb") as file:
                encoded_data = base64.b64encode(file.read()).decode('utf-8')
                return encoded_data
        except Exception as e:
            self.error.emit(f"Error encoding file {os.path.basename(file_path)}: {str(e)}")
            return None
    
    def format_person(self, person_data, entity_type="Individual"):
        """Format person data according to API requirements"""
        if entity_type == "Individual":
            return {
                "firstName": person_data.get("first_name", "").upper(),
                "middleName": person_data.get("middle_name", "").upper(),
                "lastName": person_data.get("last_name", "").upper(),
                "nameSuffix": person_data.get("suffix", "").upper(),
                "type": "Individual"
            }
        else:
            return {
                "nameUnparsed": person_data.get("name", "").upper(),
                "type": "Organization"
            }
    
    def format_legal_description(self, description_data):
        """Format legal description according to API requirements"""
        result = {
            "description": description_data.get("description", "").upper(),
            "parcelId": description_data.get("parcel_id", "").upper()
        }
        
        if "unit_number" in description_data and description_data["unit_number"] is not None:
            result["unitNumber"] = description_data["unit_number"]
            
        return result
    
    def format_reference_information(self, reference_data):
        """Format reference information according to API requirements"""
        return {
            "documentType": reference_data.get("document_type", ""),
            "book": reference_data.get("book", ""),
            "page": int(reference_data.get("page", 0))
        }
    
    def create_document_payload(self, doc_data):
        """Create a document entry for the API payload"""
        # Start with default grantors and grantees
        grantors = DEFAULT_GRANTORS.copy()
        grantees = DEFAULT_GRANTEES.copy()
        
        # Add additional person grantors if provided
        if "person_grantors" in doc_data and doc_data["person_grantors"]:
            for person in doc_data["person_grantors"]:
                grantors.append(self.format_person(person, "Individual"))
        
        # Add additional organization grantors if provided
        if "org_grantors" in doc_data and doc_data["org_grantors"]:
            for org in doc_data["org_grantors"]:
                grantors.append(self.format_person(org, "Organization"))
        
        # Add additional person grantees if provided
        if "person_grantees" in doc_data and doc_data["person_grantees"]:
            for person in doc_data["person_grantees"]:
                grantees.append(self.format_person(person, "Individual"))
        
        # Add additional organization grantees if provided
        if "org_grantees" in doc_data and doc_data["org_grantees"]:
            for org in doc_data["org_grantees"]:
                grantees.append(self.format_person(org, "Organization"))
        
        # Format legal descriptions
        legal_descriptions = []
        if "legal_descriptions" in doc_data and doc_data["legal_descriptions"]:
            for desc in doc_data["legal_descriptions"]:
                legal_descriptions.append(self.format_legal_description(desc))
        else:
            # Add default legal description
            legal_descriptions.append({
                "description": doc_data.get("legal_description", "").upper(),
                "parcelId": doc_data.get("parcel_id", "").upper()
            })
        
        # Format reference information
        reference_information = []
        if "reference_information" in doc_data and doc_data["reference_information"]:
            for ref in doc_data["reference_information"]:
                reference_information.append(self.format_reference_information(ref))
        elif "document_type" in doc_data or "book" in doc_data or "page" in doc_data:
            # Add single reference information entry
            reference_information.append({
                "documentType": doc_data.get("document_type", "Deed - Timeshare"),
                "book": doc_data.get("book", ""),
                "page": int(doc_data.get("page", 0))
            })
        
        # Encode document
        encoded_file = self.encode_file(doc_data["file_path"])
        if not encoded_file:
            return None
        
        # Create document entry
        document = {
            "submitterDocumentID": doc_data.get("document_id", f"D-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "name": doc_data.get("name", os.path.basename(doc_data["file_path"])).upper(),
            "kindOfInstrument": [doc_data.get("type", "Deed - Timeshare")],
            "indexingData": {
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions
            },
            "fileBytes": [encoded_file]
        }
        
        # Add optional fields
        if "consideration" in doc_data:
            document["indexingData"]["consideration"] = float(doc_data.get("consideration", 0.0))
        
        # Format execution date in YYYY-MM-DD format
        if "execution_date" in doc_data:
            try:
                # Try to parse and reformat the date
                date_str = doc_data.get("execution_date")
                if isinstance(date_str, str):
                    # Try to parse MM/DD/YYYY first
                    try:
                        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        # Try other formats or keep as is
                        formatted_date = date_str
                else:
                    formatted_date = datetime.now().strftime('%Y-%m-%d')
                
                document["indexingData"]["executionDate"] = formatted_date
            except:
                document["indexingData"]["executionDate"] = datetime.now().strftime('%Y-%m-%d')
        else:
            document["indexingData"]["executionDate"] = datetime.now().strftime('%Y-%m-%d')
        
        if reference_information:
            document["indexingData"]["referenceInformation"] = reference_information
        
        return document
    
    def get_package_operations(self, package_data):
        """Get package operations based on package data"""
        return {
            "draftOnErrors": package_data.get("draft_on_errors", True),
            "submitImmediately": package_data.get("submit_immediately", False),
            "verifyPageMargins": package_data.get("verify_page_margins", True)
        }
    
    def upload_package(self, package_data, document_files):
        """Upload a package with documents to Simplifile"""
        self.status.emit("Starting upload process...")
        self.progress.emit(10)
        
        try:
            # Create payload structure
            payload = {
                "documents": [],
                "recipient": self.recipient_id,
                "submitterPackageID": package_data.get("package_id", f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "name": package_data.get("package_name", f"Package {datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "operations": self.get_package_operations(package_data)
            }
            
            # Process each document
            total_docs = len(document_files)
            for i, doc_data in enumerate(document_files):
                self.status.emit(f"Processing document {i+1} of {total_docs}: {os.path.basename(doc_data['file_path'])}")
                self.progress.emit(10 + (i * 70 // total_docs))
                
                document = self.create_document_payload(doc_data)
                if document:
                    payload["documents"].append(document)
            
            # Make API request
            self.status.emit("Sending package to Simplifile...")
            self.progress.emit(80)
            
            headers = {
                "Content-Type": "application/json",
                "api_token": self.api_token
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=300  # 5 minute timeout for large packages
            )
            
            self.progress.emit(90)
            
            # Process response
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("resultCode") == "SUCCESS":
                    self.status.emit("Package uploaded successfully!")
                    self.progress.emit(100)
                    self.finished.emit(response_data)
                    return True
                else:
                    error_msg = response_data.get("message", "Unknown API error")
                    self.error.emit(f"API Error: {error_msg}")
                    self.finished.emit(response_data)
                    return False
            else:
                self.error.emit(f"API request failed with status code: {response.status_code}")
                try:
                    error_data = response.json()
                    self.status.emit(f"Error details: {json.dumps(error_data, indent=2)}")
                    self.finished.emit(error_data)
                except:
                    self.status.emit(f"Response text: {response.text}")
                    self.finished.emit({"error": response.text})
                return False
        
        except Exception as e:
            self.error.emit(f"Error in upload process: {str(e)}")
            self.finished.emit({"error": str(e)})
            return False
    
    def get_recipient_requirements(self):
        """Fetch recipient requirements from Simplifile API"""
        try:
            url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{self.submitter_id}/recipients/{self.recipient_id}/requirements"
            
            headers = {
                "Content-Type": "application/json",
                "api_token": self.api_token
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.error.emit(f"Failed to get recipient requirements. Status code: {response.status_code}")
                return None
        except Exception as e:
            self.error.emit(f"Error fetching recipient requirements: {str(e)}")
            return None
    
    def validate_document(self, document_data, instrument_type):
        """Validate document data against recipient requirements for specific instrument type"""
        # Get recipient requirements
        requirements = self.get_recipient_requirements()
        if not requirements:
            return False, "Could not retrieve requirements for validation"
        
        # Find requirements for the specified instrument type
        instrument_reqs = None
        for instr in requirements.get("recipientRequirements", {}).get("instruments", []):
            if instr.get("instrument") == instrument_type:
                instrument_reqs = instr.get("requirements", [])
                break
        
        if not instrument_reqs:
            return False, f"No requirements found for instrument type: {instrument_type}"
        
        # Check required fields
        missing_fields = []
        for req in instrument_reqs:
            if req.get("required") == "ALWAYS":
                path = req.get("path")
                field_name = req.get("label")
                
                # Check if field exists in document_data
                parts = path.split("[].")
                if len(parts) > 1:
                    # Handle array paths like grantors[].type
                    array_name = parts[0]
                    field_name_in_array = parts[1]
                    
                    # Check if array exists and has at least one item with the required field
                    if array_name not in document_data or not document_data[array_name]:
                        missing_fields.append(f"{field_name} ({path})")
                    else:
                        # Check if any item in the array has the required field
                        has_field = False
                        for item in document_data[array_name]:
                            if field_name_in_array in item and item[field_name_in_array]:
                                has_field = True
                                break
                        
                        if not has_field:
                            missing_fields.append(f"{field_name} ({path})")
                else:
                    # Handle simple paths
                    if path not in document_data or not document_data[path]:
                        missing_fields.append(f"{field_name} ({path})")
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, "Document is valid"
    
    def create_document_from_data(self, document_data, file_path, instrument_type):
        """Create a document payload based on structured data and instrument type"""
        # Validate document data
        is_valid, message = self.validate_document(document_data, instrument_type)
        if not is_valid:
            self.error.emit(message)
            return None
        
        # Create basic document structure
        doc = {
            "file_path": file_path,
            "type": instrument_type,
            "name": document_data.get("name", os.path.basename(file_path)).upper()
        }
        
        # Extract grantors and grantees
        if "grantors" in document_data:
            person_grantors = []
            org_grantors = []
            
            for grantor in document_data["grantors"]:
                if grantor.get("type") == "Individual":
                    person_grantors.append({
                        "first_name": grantor.get("firstName", ""),
                        "middle_name": grantor.get("middleName", ""),
                        "last_name": grantor.get("lastName", ""),
                        "suffix": grantor.get("nameSuffix", "")
                    })
                else:
                    org_grantors.append({
                        "name": grantor.get("nameUnparsed", "")
                    })
            
            doc["person_grantors"] = person_grantors
            doc["org_grantors"] = org_grantors
        
        if "grantees" in document_data:
            person_grantees = []
            org_grantees = []
            
            for grantee in document_data["grantees"]:
                if grantee.get("type") == "Individual":
                    person_grantees.append({
                        "first_name": grantee.get("firstName", ""),
                        "middle_name": grantee.get("middleName", ""),
                        "last_name": grantee.get("lastName", ""),
                        "suffix": grantee.get("nameSuffix", "")
                    })
                else:
                    org_grantees.append({
                        "name": grantee.get("nameUnparsed", "")
                    })
            
            doc["person_grantees"] = person_grantees
            doc["org_grantees"] = org_grantees
        
        # Extract legal descriptions
        if "legalDescriptions" in document_data:
            legal_descriptions = []
            
            for desc in document_data["legalDescriptions"]:
                legal_descriptions.append({
                    "description": desc.get("description", ""),
                    "parcel_id": desc.get("parcelId", ""),
                    "unit_number": desc.get("unitNumber", "")
                })
            
            doc["legal_descriptions"] = legal_descriptions
        else:
            doc["legal_description"] = ""
            doc["parcel_id"] = ""
        
        # Extract reference information
        if "referenceInformation" in document_data:
            reference_information = []
            
            for ref in document_data["referenceInformation"]:
                reference_information.append({
                    "document_type": ref.get("documentType", ""),
                    "book": ref.get("book", ""),
                    "page": ref.get("page", "")
                })
            
            doc["reference_information"] = reference_information
        
        # Extract other fields
        if "consideration" in document_data:
            doc["consideration"] = document_data["consideration"]
        
        if "executionDate" in document_data:
            doc["execution_date"] = document_data["executionDate"]
        
        return doc

def run_simplifile_thread(api_token, submitter_id, recipient_id, package_data, document_files):
    """Create and run a thread for Simplifile API operations"""
    thread = QThread()
    worker = SimplifileAPI(api_token, submitter_id, recipient_id)
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(lambda: worker.upload_package(package_data, document_files))
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker