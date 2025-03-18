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
    
    def to_dict(self):
        """Convert party to dictionary for API request"""
        if self.type == "ORGANIZATION":
            return {
                "nameUnparsed": self.name,
                "type": self.type
            }
        else:
            return {
                "firstName": self.first_name,
                "middleName": self.middle_name,
                "lastName": self.last_name,
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

class SimplifilePackage:
    """Represents a complete package for Simplifile submission"""
    def __init__(self):
        self.reference_number = ""
        self.package_name = ""
        self.document_type = "Deed"
        self.consideration = "0.00"
        self.execution_date = ""
        self.legal_description = ""
        self.parcel_id = ""
        self.book = ""
        self.page = ""
        self.grantors = []
        self.grantees = []
        self.helper_documents = []
    
    def add_grantor(self, party):
        """Add a grantor to the package"""
        self.grantors.append(party)
    
    def add_grantee(self, party):
        """Add a grantee to the package"""
        self.grantees.append(party)
    
    def add_helper_document(self, helper_doc):
        """Add a helper document to the package"""
        self.helper_documents.append(helper_doc)
    
    def to_dict(self):
        """Convert package to dictionary for API request"""
        return {
            "reference_number": self.reference_number,
            "package_name": self.package_name,
            "document_type": self.document_type,
            "consideration": self.consideration,
            "execution_date": self.execution_date,
            "legal_description": self.legal_description,
            "parcel_id": self.parcel_id,
            "book": self.book,
            "page": self.page,
            "grantors": [grantor.to_dict() for grantor in self.grantors],
            "grantees": [grantee.to_dict() for grantee in self.grantees],
            "helper_documents": [helper.to_dict() for helper in self.helper_documents]
        }