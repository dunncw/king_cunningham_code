import requests
import base64
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime

# Default parties that are always added
DEFAULT_GRANTORS = [
    {"nameUnparsed": "KING CUNNINGHAM LLC TR", "type": "ORGANIZATION"},
    {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "ORGANIZATION"}
]

DEFAULT_GRANTEES = [
    {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "ORGANIZATION"}
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
                "operations": {
                    "draftOnErrors": True,
                    "submitImmediately": False,
                    "verifyPageMargins": True
                }
            }
            
            # Process each document
            total_docs = len(document_files)
            for i, doc_data in enumerate(document_files):
                self.status.emit(f"Processing document {i+1} of {total_docs}: {os.path.basename(doc_data['file_path'])}")
                self.progress.emit(10 + (i * 70 // total_docs))
                
                # Encode document
                encoded_file = self.encode_file(doc_data["file_path"])
                if not encoded_file:
                    continue
                
                # Start with default grantors and grantees
                grantors = DEFAULT_GRANTORS.copy()
                grantees = DEFAULT_GRANTEES.copy()
                
                # Add additional person grantors if provided
                if "person_grantors" in doc_data and doc_data["person_grantors"]:
                    for person in doc_data["person_grantors"]:
                        grantors.append({
                            "firstName": person.get("first_name", "").upper(),
                            "middleName": person.get("middle_name", "").upper(),
                            "lastName": person.get("last_name", "").upper(),
                            "type": "PERSON"
                        })
                
                # Add additional organization grantors if provided
                if "org_grantors" in doc_data and doc_data["org_grantors"]:
                    for org in doc_data["org_grantors"]:
                        grantors.append({
                            "nameUnparsed": org.get("name", "").upper(),
                            "type": "ORGANIZATION"
                        })
                
                # Add additional person grantees if provided
                if "person_grantees" in doc_data and doc_data["person_grantees"]:
                    for person in doc_data["person_grantees"]:
                        grantees.append({
                            "firstName": person.get("first_name", "").upper(),
                            "middleName": person.get("middle_name", "").upper(),
                            "lastName": person.get("last_name", "").upper(),
                            "type": "PERSON"
                        })
                
                # Add additional organization grantees if provided
                if "org_grantees" in doc_data and doc_data["org_grantees"]:
                    for org in doc_data["org_grantees"]:
                        grantees.append({
                            "nameUnparsed": org.get("name", "").upper(),
                            "type": "ORGANIZATION"
                        })
                
                # Create document entry with all grantors/grantees
                document = {
                    "submitterDocumentID": doc_data.get("document_id", f"D-{i+1}"),
                    "name": doc_data.get("name", os.path.basename(doc_data["file_path"])).upper(),
                    "kindOfInstrument": [doc_data.get("type", "Deed - Timeshare")],
                    "indexingData": {
                        "consideration": doc_data.get("consideration", "0.00"),
                        "executionDate": doc_data.get("execution_date", datetime.now().strftime('%m/%d/%Y')),
                        "grantors": grantors,
                        "grantees": grantees,
                        "legalDescriptions": [
                            {
                                "description": doc_data.get("legal_description", "").upper(),
                                "parcelId": doc_data.get("parcel_id", "").upper()
                            }
                        ]
                    },
                    "fileBytes": [encoded_file]
                }
                
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