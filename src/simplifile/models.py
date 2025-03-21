class Party:
    """Represents a party (grantor or grantee) in a Simplifile document"""
    def __init__(self, party_type="PERSON", **kwargs):
        self.type = party_type  # PERSON or ORGANIZATION
        
        if party_type == "ORGANIZATION":
            self.name = kwargs.get("name", "")
        else:
            self.first_name = kwargs.get("first_name", "")
            self.middle_name = kwargs.get("middle_name", "")
            self.last_name = kwargs.get("last_name", "")
            self.suffix = kwargs.get("suffix", "")
    
    def to_dict(self):
        """Convert party to dictionary for API request"""
        if self.type == "ORGANIZATION":
            return {
                "nameUnparsed": self.name.upper(),
                "type": self.type
            }
        else:
            return {
                "firstName": self.first_name.upper(),
                "middleName": self.middle_name.upper() if self.middle_name else "",
                "lastName": self.last_name.upper(),
                "nameSuffix": self.suffix.upper() if hasattr(self, 'suffix') and self.suffix else "",
                "type": self.type
            }


class HelperDocument:
    """Represents a helper document in a Simplifile package"""
    def __init__(self, path, doc_type="PT-61", is_electronic=False):
        self.path = path
        self.type = doc_type
        self.is_electronic = is_electronic
    
    def to_dict(self):
        """Convert helper document to dictionary for API request"""
        return {
            "path": self.path,
            "type": self.type,
            "is_electronic": self.is_electronic
        }


class LegalDescription:
    """Represents a legal description for a Simplifile document"""
    def __init__(self, description="", parcel_id="", unit_number=None):
        self.description = description
        self.parcel_id = parcel_id
        self.unit_number = unit_number
    
    def to_dict(self):
        """Convert legal description to dictionary for API request"""
        result = {
            "description": self.description.upper(),
            "parcelId": self.parcel_id.upper()
        }
        if self.unit_number is not None:
            result["unitNumber"] = self.unit_number
        return result


class ReferenceInformation:
    """Represents reference information for a Simplifile document"""
    def __init__(self, document_type="", book="", page=0):
        self.document_type = document_type
        self.book = book
        self.page = page
    
    def to_dict(self):
        """Convert reference information to dictionary for API request"""
        return {
            "documentType": self.document_type,
            "book": self.book,
            "page": self.page
        }


class SimplifilePackage:
    """Represents a complete package for Simplifile submission"""
    def __init__(self):
        self.reference_number = ""
        self.package_id = ""
        self.package_name = ""
        self.document_type = "Deed - Timeshare"
        self.consideration = "0.00"
        self.execution_date = ""
        self.legal_description = ""
        self.parcel_id = ""
        self.book = ""
        self.page = ""
        self.grantors = []
        self.grantees = []
        self.helper_documents = []
        self.legal_descriptions = []
        self.reference_information = []
        self.operations = {
            "draftOnErrors": True,
            "submitImmediately": False,
            "verifyPageMargins": True
        }
    
    def add_grantor(self, party):
        """Add a grantor to the package"""
        self.grantors.append(party)
    
    def add_grantee(self, party):
        """Add a grantee to the package"""
        self.grantees.append(party)
    
    def add_helper_document(self, helper_doc):
        """Add a helper document to the package"""
        self.helper_documents.append(helper_doc)
    
    def add_legal_description(self, legal_desc):
        """Add a legal description to the package"""
        self.legal_descriptions.append(legal_desc)
    
    def add_reference_info(self, ref_info):
        """Add reference information to the package"""
        self.reference_information.append(ref_info)
    
    def set_operations(self, draft_on_errors=True, submit_immediately=False, verify_page_margins=True):
        """Set operations flags for the package"""
        self.operations = {
            "draftOnErrors": draft_on_errors,
            "submitImmediately": submit_immediately,
            "verifyPageMargins": verify_page_margins
        }
    
    def to_dict(self):
        """Convert package to dictionary for API request"""
        package_data = {
            "package_id": self.package_id or f"P-{self.reference_number}",
            "package_name": self.package_name,
            "document_type": self.document_type,
            "consideration": self.consideration,
            "execution_date": self.execution_date,
            "grantors": [grantor.to_dict() for grantor in self.grantors],
            "grantees": [grantee.to_dict() for grantee in self.grantees],
            "helper_documents": [helper.to_dict() for helper in self.helper_documents],
            "draft_on_errors": self.operations["draftOnErrors"],
            "submit_immediately": self.operations["submitImmediately"],
            "verify_page_margins": self.operations["verifyPageMargins"]
        }
        
        # Handle legal descriptions
        if self.legal_descriptions:
            package_data["legal_descriptions"] = [desc.to_dict() for desc in self.legal_descriptions]
        elif self.legal_description:
            # For backward compatibility
            leg_desc = LegalDescription(self.legal_description, self.parcel_id)
            package_data["legal_descriptions"] = [leg_desc.to_dict()]
        
        # Handle reference information
        if self.reference_information:
            package_data["reference_information"] = [ref.to_dict() for ref in self.reference_information]
        elif self.book or self.page:
            # For backward compatibility
            ref_info = ReferenceInformation(self.document_type, self.book, self.page)
            package_data["reference_information"] = [ref_info.to_dict()]
        
        return package_data