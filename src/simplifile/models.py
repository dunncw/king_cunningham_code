# models.py - Updated with centralized data models for Simplifile
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

class Party:
    """Represents a party (grantor or grantee) in a Simplifile document"""
    
    def __init__(self, name: str = "", is_organization: bool = False, 
                 first_name: str = "", middle_name: str = "", 
                 last_name: str = "", suffix: str = ""):
        self.is_organization = is_organization
        
        # Organization data
        self.name = name
        
        # Individual data
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.suffix = suffix
        
        # Special case: check if last_name starts with "ORG:"
        if last_name.startswith("ORG:"):
            self.is_organization = True
            self.name = first_name  # In this case, first_name contains the org name
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert party to dictionary for API request"""
        if self.is_organization:
            return {
                "nameUnparsed": self.name.upper(),
                "type": "Organization"
            }
        else:
            return {
                "firstName": self.first_name.upper(),
                "middleName": self.middle_name.upper() if self.middle_name else "",
                "lastName": self.last_name.upper(),
                "nameSuffix": self.suffix.upper() if self.suffix else "",
                "type": "Individual"
            }
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert party to a dictionary for UI display"""
        if self.is_organization:
            return {
                "type": "Organization",
                "name": self.name.upper(),
                "display_name": self.name.upper()
            }
        else:
            full_name = " ".join(filter(None, [
                self.first_name.upper(),
                self.middle_name.upper() if self.middle_name else "",
                self.last_name.upper(),
                self.suffix.upper() if self.suffix else ""
            ]))
            return {
                "type": "Individual",
                "first_name": self.first_name.upper(),
                "middle_name": self.middle_name.upper() if self.middle_name else "",
                "last_name": self.last_name.upper(),
                "suffix": self.suffix.upper() if self.suffix else "",
                "display_name": full_name
            }
    
    @staticmethod
    def from_excel_data(first_name: str = "", last_name: str = ""):
        """Create a party from Excel data, handling special cases like 'ORG:' prefix"""
        # Check if this is an organization (last_name starts with "ORG:")
        if last_name.startswith("ORG:"):
            return Party(name=first_name, is_organization=True)
        else:
            return Party(first_name=first_name, last_name=last_name, is_organization=False)

class LegalDescription:
    """Represents a legal description for a Simplifile document"""
    
    def __init__(self, description: str = "", parcel_id: str = "", unit_number: Optional[str] = None):
        self.description = description
        self.parcel_id = parcel_id
        self.unit_number = unit_number
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert legal description to dictionary for API request"""
        # For API, we combine description and parcel_id, with empty parcelId field
        combined_description = self.description.upper()
        if self.parcel_id and self.parcel_id not in combined_description:
            combined_description = f"{combined_description} {self.parcel_id.upper()}"
            
        result = {
            "description": combined_description,
            "parcelId": ""  # Leave parcelId blank as requested
        }
        
        if self.unit_number is not None:
            result["unitNumber"] = self.unit_number
        
        return result
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert legal description to dictionary for UI display"""
        return {
            "description": self.description.upper(),
            "parcel_id": self.parcel_id.upper(),
            "unit_number": self.unit_number if self.unit_number is not None else "",
            "combined_description": f"{self.description.upper()} {self.parcel_id.upper()}".strip()
        }

class ReferenceInformation:
    """Represents reference information for a Simplifile document"""
    
    def __init__(self, document_type: str = "", book: str = "", page: Union[str, int] = ""):
        self.document_type = document_type
        self.book = book
        self.page = str(page)
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert reference information to dictionary for API request"""
        # Convert page to integer if possible for API
        try:
            page_value = int(self.page)
        except (ValueError, TypeError):
            page_value = 0
            
        return {
            "documentType": self.document_type,
            "book": self.book,
            "page": page_value
        }
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert reference information to dictionary for UI display"""
        return {
            "document_type": self.document_type,
            "book": self.book,
            "page": self.page,
            "display_text": f"Book {self.book}, Page {self.page}" if self.book and self.page else "Not provided"
        }

class SimplifileDocument:
    """Represents a document in a Simplifile package"""
    
    def __init__(self):
        # Document identification
        self.document_id = ""
        self.name = ""
        self.type = ""  # "Deed - Timeshare" or "Mortgage Satisfaction"
        
        # File information
        self.file_path = ""
        self.page_range = ""
        self.page_count = 0
        
        # Document metadata
        self.execution_date = ""
        self.consideration = ""
        
        # Parties
        self.grantors = []  # List of Party objects
        self.grantees = []  # List of Party objects
        
        # Legal descriptions and references
        self.legal_descriptions = []  # List of LegalDescription objects
        self.reference_information = []  # List of ReferenceInformation objects
        
        # For preview/validation
        self.validation_issues = []
        self.is_valid = True
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for API request"""
        # Encode file if it exists
        file_bytes = []
        if self.file_path:
            try:
                with open(self.file_path, "rb") as file:
                    import base64
                    encoded_data = base64.b64encode(file.read()).decode('utf-8')
                    file_bytes.append(encoded_data)
            except Exception as e:
                file_bytes = ["<Error encoding file>"]
        
        # Create API structure
        document = {
            "submitterDocumentID": self.document_id,
            "name": self.name.upper(),
            "kindOfInstrument": [self.type],
            "indexingData": {
                "grantors": [grantor.to_api_dict() for grantor in self.grantors],
                "grantees": [grantee.to_api_dict() for grantee in self.grantees],
                "legalDescriptions": [desc.to_api_dict() for desc in self.legal_descriptions],
                "executionDate": self.format_date_for_api(self.execution_date)
            },
            "fileBytes": file_bytes
        }
        
        # Add consideration if present
        if self.consideration:
            try:
                document["indexingData"]["consideration"] = float(self.consideration)
            except (ValueError, TypeError):
                document["indexingData"]["consideration"] = 0.0
        
        # Add reference information if present
        if self.reference_information:
            document["indexingData"]["referenceInformation"] = [
                ref.to_api_dict() for ref in self.reference_information
            ]
        
        return document
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for UI display"""
        return {
            "document_id": self.document_id,
            "name": self.name.upper(),
            "type": self.type,
            "page_range": self.page_range,
            "page_count": self.page_count,
            "execution_date": self.execution_date,
            "consideration": self.consideration,
            "grantors": [grantor.to_display_dict() for grantor in self.grantors],
            "grantees": [grantee.to_display_dict() for grantee in self.grantees],
            "legal_descriptions": [desc.to_display_dict() for desc in self.legal_descriptions],
            "reference_information": [ref.to_display_dict() for ref in self.reference_information],
            "is_valid": self.is_valid,
            "validation_issues": self.validation_issues
        }
    
    def format_date_for_api(self, date_str: str) -> str:
        """Format a date string for Simplifile API (YYYY-MM-DD)"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
            
        try:
            # Try to parse MM/DD/YYYY format
            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            # If that fails, try different format or return as-is
            try:
                # Try to parse YYYY-MM-DD format
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str  # Already in correct format
            except ValueError:
                # Return current date as fallback
                return datetime.now().strftime('%Y-%m-%d')

class SimplifilePackage:
    """Represents a complete package for Simplifile submission"""
    
    def __init__(self):
        # Package identification
        self.package_id = ""
        self.package_name = ""
        self.excel_row = 0
        
        # Business data
        self.account_number = ""
        self.kc_file_no = ""
        self.grantor_grantee = ""  # From GRANTOR/GRANTEE column
        
        # Documents in the package
        self.documents = []  # List of SimplifileDocument objects
        
        # Operation settings
        self.draft_on_errors = True
        self.submit_immediately = False
        self.verify_page_margins = True
        
        # For preview/validation
        self.validation_issues = []
        self.is_valid = True
    
    def to_api_dict(self) -> Dict[str, Any]:
        """Convert package to dictionary for API request"""
        return {
            "documents": [doc.to_api_dict() for doc in self.documents],
            "recipient": "",  # This should be provided separately
            "submitterPackageID": self.package_id,
            "name": self.package_name.upper(),
            "operations": {
                "draftOnErrors": self.draft_on_errors,
                "submitImmediately": self.submit_immediately,
                "verifyPageMargins": self.verify_page_margins
            }
        }
    
    def to_display_dict(self) -> Dict[str, Any]:
        """Convert package to dictionary for UI display"""
        return {
            "package_id": self.package_id,
            "package_name": self.package_name,
            "excel_row": self.excel_row,
            "account_number": self.account_number,
            "kc_file_no": self.kc_file_no,
            "grantor_grantee": self.grantor_grantee,
            "documents": [doc.to_display_dict() for doc in self.documents],
            "draft_on_errors": self.draft_on_errors,
            "submit_immediately": self.submit_immediately,
            "verify_page_margins": self.verify_page_margins,
            "is_valid": self.is_valid,
            "validation_issues": self.validation_issues
        }
    
    def add_document(self, document: SimplifileDocument) -> None:
        """Add a document to the package"""
        self.documents.append(document)
    
    @staticmethod
    def from_excel_row(row_data: Dict[str, Any], row_index: int) -> 'SimplifilePackage':
        """Create a package from Excel row data"""
        package = SimplifilePackage()
        
        # Extract essential data
        package.account_number = str(row_data.get('Account', ''))
        package.kc_file_no = str(row_data.get('KC File No.', ''))
        package.excel_row = row_index + 2  # +2 for 1-based indexing and header row
        
        # Format names (handling ORG: prefix)
        last_name1 = SimplifilePackage.format_name(row_data.get('Last Name #1', ''))
        first_name1 = SimplifilePackage.format_name(row_data.get('First Name #1', ''))
        
        # Set package name based on name type
        if last_name1.startswith("ORG:"):
            package.package_name = f"{package.account_number} {first_name1} TD {package.kc_file_no}"
        else:
            package.package_name = f"{package.account_number} {last_name1} TD {package.kc_file_no}"
        
        # Set package ID as KC File No + Account Number
        package.package_id = f"{package.kc_file_no}-{package.account_number}"
        
        # Set grantor_grantee
        package.grantor_grantee = SimplifilePackage.format_name(row_data.get('GRANTOR/GRANTEE', ''))
        
        return package
    
    @staticmethod
    def format_name(name: str) -> str:
        """Format names according to requirements"""
        if not isinstance(name, str):
            return ""
        # Convert to uppercase
        name = name.upper()
        # Remove hyphens as specified in the guide
        name = name.replace('-', ' ')
        return name