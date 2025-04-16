# api.py - Updated to use centralized models
import requests
import base64
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from .models import SimplifilePackage, SimplifileDocument, Party, LegalDescription, ReferenceInformation

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

    def upload_package(self, package_data, document_files):
        """Upload a package with documents to Simplifile, using the new model structure"""
        self.status.emit("Starting upload process...")
        self.progress.emit(10)
        
        try:
            # Create package object from data
            package = SimplifilePackage()
            package.package_id = package_data.get("package_id", f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            package.package_name = package_data.get("package_name", f"Package {datetime.now().strftime('%Y%m%d%H%M%S')}")
            package.draft_on_errors = package_data.get("draft_on_errors", True)
            package.submit_immediately = package_data.get("submit_immediately", False)
            package.verify_page_margins = package_data.get("verify_page_margins", True)
            
            # Process each document
            total_docs = len(document_files)
            for i, doc_data in enumerate(document_files):
                self.status.emit(f"Processing document {i+1} of {total_docs}: {os.path.basename(doc_data['file_path'])}")
                self.progress.emit(10 + (i * 70 // total_docs))
                
                # Create document object
                document = self.create_document_from_data(doc_data)
                if document:
                    package.add_document(document)
            
            # Make API request
            self.status.emit("Sending package to Simplifile...")
            self.progress.emit(80)
            
            # Create API payload
            api_payload = package.to_api_dict()
            api_payload["recipient"] = self.recipient_id
            
            headers = {
                "Content-Type": "application/json",
                "api_token": self.api_token
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                data=json.dumps(api_payload),
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

    def create_document_from_data(self, doc_data):
        """Create a SimplifileDocument from dictionary data"""
        try:
            document = SimplifileDocument()
            
            # Set basic document info
            document.document_id = doc_data.get("document_id", f"D-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            document.name = doc_data.get("name", os.path.basename(doc_data["file_path"])).upper()
            document.type = doc_data.get("type", "Deed - Timeshare")
            document.file_path = doc_data.get("file_path", "")
            document.execution_date = doc_data.get("execution_date", datetime.now().strftime('%m/%d/%Y'))
            
            # Set consideration if provided
            if "consideration" in doc_data:
                document.consideration = doc_data.get("consideration", "0.00")
            
            # Add grantors
            # First determine which grantors to add based on document type
            if document.type == "Deed - Timeshare":
                # For deeds, we need to add the standard organization
                document.grantors.append(Party(name="KING CUNNINGHAM LLC TR", is_organization=True))
                
                # Add grantor/grantee
                if "grantor_grantee" in doc_data and doc_data["grantor_grantee"]:
                    document.grantors.append(Party(name=doc_data["grantor_grantee"], is_organization=True))
            
            # Add person grantors if provided
            if "person_grantors" in doc_data and doc_data["person_grantors"]:
                for person in doc_data["person_grantors"]:
                    # Check if organization by "ORG:" prefix
                    if "last_name" in person and person["last_name"].startswith("ORG:"):
                        document.grantors.append(Party(
                            name=person["first_name"],
                            is_organization=True
                        ))
                    else:
                        document.grantors.append(Party(
                            first_name=person.get("first_name", ""),
                            middle_name=person.get("middle_name", ""),
                            last_name=person.get("last_name", ""),
                            suffix=person.get("suffix", ""),
                            is_organization=False
                        ))
            
            # Add organization grantors if provided
            if "org_grantors" in doc_data and doc_data["org_grantors"]:
                for org in doc_data["org_grantors"]:
                    document.grantors.append(Party(
                        name=org.get("name", ""),
                        is_organization=True
                    ))
            
            # Add grantees - default to grantor_grantee
            if "grantor_grantee" in doc_data and doc_data["grantor_grantee"]:
                document.grantees.append(Party(
                    name=doc_data["grantor_grantee"],
                    is_organization=True
                ))
            
            # Add person grantees if provided
            if "person_grantees" in doc_data and doc_data["person_grantees"]:
                for person in doc_data["person_grantees"]:
                    # Check if organization by "ORG:" prefix
                    if "last_name" in person and person["last_name"].startswith("ORG:"):
                        document.grantees.append(Party(
                            name=person["first_name"],
                            is_organization=True
                        ))
                    else:
                        document.grantees.append(Party(
                            first_name=person.get("first_name", ""),
                            middle_name=person.get("middle_name", ""),
                            last_name=person.get("last_name", ""),
                            suffix=person.get("suffix", ""),
                            is_organization=False
                        ))
            
            # Add organization grantees if provided
            if "org_grantees" in doc_data and doc_data["org_grantees"]:
                for org in doc_data["org_grantees"]:
                    document.grantees.append(Party(
                        name=org.get("name", ""),
                        is_organization=True
                    ))
            
            # Add legal descriptions
            if "legal_descriptions" in doc_data and doc_data["legal_descriptions"]:
                for desc in doc_data["legal_descriptions"]:
                    document.legal_descriptions.append(LegalDescription(
                        description=desc.get("description", ""),
                        parcel_id=desc.get("parcelId", ""),
                        unit_number=desc.get("unitNumber", None)
                    ))
            else:
                # Use simple legal description and parcel_id fields if available
                document.legal_descriptions.append(LegalDescription(
                    description=doc_data.get("legal_description", ""),
                    parcel_id=doc_data.get("parcel_id", "")
                ))
            
            # Add reference information
            if "reference_information" in doc_data and doc_data["reference_information"]:
                for ref in doc_data["reference_information"]:
                    document.reference_information.append(ReferenceInformation(
                        document_type=ref.get("documentType", document.type),
                        book=ref.get("book", ""),
                        page=ref.get("page", "")
                    ))
            elif "book" in doc_data or "page" in doc_data or "reference_book" in doc_data or "reference_page" in doc_data:
                # Use simple book and page fields if available
                book = doc_data.get("book", doc_data.get("reference_book", ""))
                page = doc_data.get("page", doc_data.get("reference_page", ""))
                if book or page:
                    document.reference_information.append(ReferenceInformation(
                        document_type=document.type,
                        book=book,
                        page=page
                    ))
            
            return document
            
        except Exception as e:
            self.error.emit(f"Error creating document: {str(e)}")
            return None

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

    def validate_document(self, document, instrument_type):
        """Validate document data against recipient requirements for specific instrument type"""
        # Get recipient requirements
        requirements = self.get_recipient_requirements()
        if not requirements:
            return False, "Could not retrieve county requirements. This could be due to invalid API credentials, network issues, or the selected county not being properly configured."
        
        # Check if the instrument type is recognized by Simplifile
        valid_instruments = [
            "Deed - Timeshare", "Mortgage Satisfaction"
        ]
        
        if instrument_type not in valid_instruments:
            return False, f"The instrument type '{instrument_type}' may not be recognized by Simplifile. Valid types include: 'Deed', 'Deed - Timeshare', 'Mortgage Satisfaction', etc. Please check that you're using the correct instrument type."
        
        # Find requirements for the specified instrument type
        instrument_reqs = None
        for instr in requirements.get("recipientRequirements", {}).get("instruments", []):
            if instr.get("instrument") == instrument_type:
                instrument_reqs = instr.get("requirements", [])
                break
        
        if not instrument_reqs:
            # More informative error about missing requirements
            compatible_instruments = []
            for instr in requirements.get("recipientRequirements", {}).get("instruments", []):
                compatible_instruments.append(instr.get("instrument"))
            
            if compatible_instruments:
                return False, f"No requirements found for instrument type: {instrument_type}. This county may not accept this document type. Compatible types are: {', '.join(compatible_instruments)}"
            else:
                return False, f"No requirements found for instrument type: {instrument_type}. This county may not accept electronic recordings for this document type."
        
        # Now that we have requirements, validate the document against them
        missing_fields = []
        
        # Get document data as dictionary for validation
        doc_data = {}
        if isinstance(document, SimplifileDocument):
            # If it's our model object, extract relevant fields
            doc_data = document.to_api_dict()
        elif isinstance(document, dict):
            # If it's already a dictionary, use it directly
            doc_data = document
        
        # Check required fields
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
                    if array_name not in doc_data or not doc_data[array_name]:
                        missing_fields.append(f"{field_name} ({path})")
                    else:
                        # Check if any item in the array has the required field
                        has_field = False
                        for item in doc_data[array_name]:
                            if field_name_in_array in item and item[field_name_in_array]:
                                has_field = True
                                break
                        
                        if not has_field:
                            missing_fields.append(f"{field_name} ({path})")
                else:
                    # Handle simple paths
                    if path not in doc_data or not doc_data[path]:
                        missing_fields.append(f"{field_name} ({path})")
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, "Document is valid"

    def test_connection(self):
        """Test API connection with provided credentials"""
        try:
            # Build API URL for recipient requirements - this is a lightweight endpoint to test
            url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{self.submitter_id}/recipients"
            
            headers = {
                "Content-Type": "application/json",
                "api_token": self.api_token
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, "Connection successful!"
            else:
                error_msg = f"API connection failed with status code: {response.status_code}"
                try:
                    error_data = response.json()
                    error_details = error_data.get("message", "Unknown error")
                    result_code = error_data.get("resultCode", "")
                    
                    if response.status_code == 401 or result_code == "UNAUTHORIZED":
                        error_msg = "Authentication failed: Invalid API token or submitter ID"
                    else:
                        error_msg += f" - {error_details}"
                except:
                    error_msg += f" - {response.text[:100]}"
                
                # Only emit status, not error since we're handling everything through the return value
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Error testing API connection: {str(e)}"
            # Only emit status, not error
            return False, error_msg


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

def run_simplifile_connection_test(api_token, submitter_id):
    """Create and run a thread for testing Simplifile API connection"""
    thread = QThread()
    worker = SimplifileAPI(api_token, submitter_id, "")  # Empty recipient ID is fine for connection test
    worker.moveToThread(thread)
    
    # Store the original method to avoid multiple signal emissions
    original_test_connection = worker.test_connection
    
    def wrapped_test_connection():
        success, message = original_test_connection()
        
        # Only emit the finished signal, don't emit error separately if there's an error
        # since we'll handle everything through the finished signal
        result_dict = {
            "resultCode": "SUCCESS" if success else "ERROR",
            "message": message,
            "test_result": (success, message)
        }
        worker.finished.emit(result_dict)
        return success, message
    
    worker.test_connection = wrapped_test_connection
    
    # Connect signals - avoid connecting the error signal
    thread.started.connect(worker.test_connection)
    
    # Clean up
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker