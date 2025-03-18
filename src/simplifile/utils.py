import os
import base64
import json
from datetime import datetime
from .models import Party, HelperDocument, SimplifilePackage

def validate_package_data(package_data):
    """Validate that required fields are present in package data"""
    required_fields = [
        "reference_number", "package_name", "document_type"
    ]
    
    for field in required_fields:
        if not package_data.get(field):
            return False, f"Missing required field: {field}"
    
    # Check that there's at least one grantor and grantee
    if not package_data.get("grantors"):
        return False, "At least one grantor is required"
    
    if not package_data.get("grantees"):
        return False, "At least one grantee is required"
    
    return True, "Valid"

def get_document_types():
    """Return a list of common document types for Simplifile"""
    return [
        "Deed",
        "Mortgage",
        "Assignment of Mortgage",
        "Satisfaction of Mortgage",
        "Deed of Trust",
        "Release of Lien",
        "Affidavit",
        "Amendment",
        "DEED-TIMESHARE",
        "Lien",
        "Modification",
        "Power of Attorney",
        "UCC Financing Statement"
    ]

def get_helper_document_types():
    """Return a list of helper document types for Simplifile"""
    return [
        "PT-61",
        "Tax Form",
        "Cover Sheet",
        "Other"
    ]

def format_date(date_obj):
    """Format a date object for Simplifile API"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%m/%d/%Y")
    return date_obj

def create_sample_package():
    """Create a sample package with test data"""
    package = SimplifilePackage()
    package.reference_number = "12345"
    package.package_name = "SMITH 12345"
    package.document_type = "Deed"
    package.consideration = "250000.00"
    package.execution_date = "03/15/2025"
    package.legal_description = "ANDERSON OCEAN CLUB HPR U/W"
    package.parcel_id = "14-0078-0007-096-9"
    
    # Add grantor
    grantor1 = Party("ORGANIZATION", name="KING CUNNINGHAM LLC TR")
    package.add_grantor(grantor1)
    
    grantor2 = Party("PERSON", first_name="John", last_name="Smith")
    package.add_grantor(grantor2)
    
    # Add grantee
    grantee = Party("ORGANIZATION", name="OCEAN CLUB VACATIONS LLC")
    package.add_grantee(grantee)
    
    return package

def save_config(config_data, file_path):
    """Save configuration data to a file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        return True
    except Exception:
        return False

def load_config(file_path):
    """Load configuration data from a file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    
    # Return default config if file doesn't exist or can't be loaded
    return {
        "api_token": "",
        "submitter_id": "",
        "recipient_id": "",
        "last_document_path": "",
        "last_package_data": {}
    }