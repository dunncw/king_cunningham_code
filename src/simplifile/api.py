import requests
import base64
import json
import os
from PyQt6.QtCore import QObject, pyqtSignal, QThread

class SimplifileAPIWorker(QObject):
    """Worker class for interacting with the Simplifile API"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, 
                 api_token, 
                 submitter_id, 
                 recipient_id,
                 document_path, 
                 package_data):
        super().__init__()
        self.api_token = api_token
        self.submitter_id = submitter_id
        self.recipient_id = recipient_id
        self.document_path = document_path
        self.package_data = package_data
        self.base_url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{submitter_id}"
    
    def encode_document(self, file_path):
        """Convert document to base64 encoding"""
        self.status.emit(f"Encoding document: {os.path.basename(file_path)}")
        try:
            with open(file_path, "rb") as doc_file:
                return base64.b64encode(doc_file.read()).decode('utf-8')
        except Exception as e:
            self.error.emit(f"Error encoding document: {str(e)}")
            return None
    
    def create_request_payload(self):
        """Create the JSON payload for the API request"""
        self.status.emit("Creating API request payload")
        
        # Extract data from package_data
        reference_number = self.package_data.get("reference_number", "")
        package_name = self.package_data.get("package_name", "")
        document_type = self.package_data.get("document_type", "Deed")
        consideration = self.package_data.get("consideration", "0.00")
        execution_date = self.package_data.get("execution_date", "")
        
        # Grantors processing
        grantors = []
        for grantor in self.package_data.get("grantors", []):
            if grantor.get("type") == "ORGANIZATION":
                grantors.append({
                    "nameUnparsed": grantor.get("name", ""),
                    "type": "ORGANIZATION"
                })
            else:
                grantors.append({
                    "firstName": grantor.get("first_name", ""),
                    "middleName": grantor.get("middle_name", ""),
                    "lastName": grantor.get("last_name", ""),
                    "type": "PERSON"
                })
        
        # Grantees processing
        grantees = []
        for grantee in self.package_data.get("grantees", []):
            if grantee.get("type") == "ORGANIZATION":
                grantees.append({
                    "nameUnparsed": grantee.get("name", ""),
                    "type": "ORGANIZATION"
                })
            else:
                grantees.append({
                    "firstName": grantee.get("first_name", ""),
                    "middleName": grantee.get("middle_name", ""),
                    "lastName": grantee.get("last_name", ""),
                    "type": "PERSON"
                })
        
        # Encode the main document
        document_bytes = self.encode_document(self.document_path)
        if not document_bytes:
            return None
        
        # Process helper documents if any
        helper_docs = []
        for helper in self.package_data.get("helper_documents", []):
            if os.path.exists(helper["path"]):
                helper_bytes = self.encode_document(helper["path"])
                if helper_bytes:
                    helper_docs.append({
                        "fileBytes": [helper_bytes],
                        "helperKindOfInstrument": helper.get("type", "PT-61"),
                        "isElectronicallyOriginated": False
                    })
        
        # Create the final payload
        payload = {
            "documents": [
                {
                    "submitterDocumentID": f"D-{reference_number}",
                    "name": package_name,
                    "kindOfInstrument": [document_type],
                    "indexingData": {
                        "consideration": consideration,
                        "executionDate": execution_date,
                        "grantors": grantors,
                        "grantees": grantees,
                        "legalDescriptions": [
                            {
                                "description": self.package_data.get("legal_description", ""),
                                "parcelId": self.package_data.get("parcel_id", "")
                            }
                        ]
                    },
                    "fileBytes": [document_bytes],
                }
            ],
            "recipient": self.recipient_id,
            "submitterPackageID": f"P-{reference_number}",
            "name": package_name,
            "operations": {
                "draftOnErrors": True,
                "submitImmediately": False,
                "verifyPageMargins": True
            }
        }
        
        # Add helper documents if available
        if helper_docs:
            payload["documents"][0]["helperDocuments"] = helper_docs
            
        # Add reference info if available
        book = self.package_data.get("book", "")
        page = self.package_data.get("page", "")
        if book and page:
            payload["documents"][0]["indexingData"]["referenceInfo"] = {
                "bookPage": f"{book}/{page}"
            }
            
        return payload
    
    def submit_to_api(self):
        """Submit package to Simplifile API"""
        self.status.emit("Starting Simplifile API submission")
        self.progress.emit(10)
        
        # Create request payload
        payload = self.create_request_payload()
        if not payload:
            self.error.emit("Failed to create request payload")
            return False
        
        self.progress.emit(50)
        self.status.emit("Sending data to Simplifile API")
        
        # Prepare headers
        headers = {
            "api_token": self.api_token,
            "Content-Type": "application/json"
        }
        
        try:
            # Make the API request
            response = requests.post(
                f"{self.base_url}/packages/create",
                headers=headers,
                json=payload,
                timeout=120  # 2 minute timeout for large documents
            )
            
            self.progress.emit(90)
            self.status.emit(f"Received response (status code: {response.status_code})")
            
            # Process response
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("resultCode") == "SUCCESS":
                    self.status.emit(f"Successfully created package: {payload['name']}")
                    self.progress.emit(100)
                    return True
                else:
                    error_msg = response_data.get("message", "Unknown error")
                    self.error.emit(f"API Error: {error_msg}")
                    return False
            else:
                self.error.emit(f"API request failed with status code: {response.status_code}")
                try:
                    error_details = response.json()
                    self.status.emit(f"Error details: {json.dumps(error_details, indent=2)}")
                except:
                    self.status.emit(f"Response text: {response.text}")
                return False
                
        except Exception as e:
            self.error.emit(f"Error submitting to Simplifile API: {str(e)}")
            return False
        finally:
            self.finished.emit()
    
def run_simplifile_api_thread(api_token, submitter_id, recipient_id, document_path, package_data):
    """Create and return a thread and worker for the Simplifile API operations"""
    thread = QThread()
    worker = SimplifileAPIWorker(api_token, submitter_id, recipient_id, document_path, package_data)
    worker.moveToThread(thread)
    
    # Connect signals and slots
    thread.started.connect(worker.submit_to_api)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker