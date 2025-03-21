import os
import base64
import json
from datetime import datetime
from .models import Party, HelperDocument, SimplifilePackage, LegalDescription, ReferenceInformation

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
        "Deed - Timeshare",
        "Mortgage",
        "Assignment of Mortgage",
        "Satisfaction of Mortgage",
        "Mortgage Satisfaction",
        "Deed of Trust",
        "Release of Lien",
        "Affidavit",
        "Amendment",
        "Lien",
        "Modification",
        "Power of Attorney",
        "UCC Financing Statement"
    ]

def get_instrument_types():
    """Return a list of instrument types from Simplifile API spec"""
    return [
        "Affidavit",
        "Affidavit - Lien Book",
        "Agreement Deed Book",
        "Agreement Mortgage Book",
        "Amed of Partnership",
        "Amendment Deed Book",
        "Articles of Association",
        "Articles of Incorporation",
        "Assignment Deed",
        "Assignment Mortgage",
        "Assignment of Lease",
        "Assignment of Lease Rents and Profits - Deed Book",
        "Bankruptcy",
        "Bill of Sale",
        "Blanket Partial Release - Deed Book",
        "Blanket Partial Release - Mortgage Book",
        "Certificate of Death",
        "Child Support Lien",
        "Child Support Lien Satisfaction",
        "Condemnation",
        "Condo Lien",
        "Condo Lien - Amendment",
        "Condo Lien - Partial Release",
        "Condo Lien Satisfaction",
        "Condo Plat",
        "Contract of Sale",
        "Contractors Notice of Project",
        "Court Order Deed",
        "Deed",
        "Deed - Timeshare",
        "Dissolution of Partnership",
        "Easement",
        "Federal Tax Partial Release",
        "Federal Tax Satisfaction",
        "Federal Tax Withdrawal",
        "HCG Deed",
        "HCG Easement",
        "HCG Plat - Non-Legal Size",
        "Lease",
        "Lease Agreement",
        "Lien Satisfaction Rescission",
        "Lis Pendens Deed",
        "Lis Pendens Deed Release",
        "Lis Pendens Deed Satisfaction",
        "Lis Pendens Mortgage",
        "Lis Pendens Mortgage Release",
        "Lis Pendens Mortgage Satisfaction",
        "Manufactured Home Lien Affidavit",
        "Manufactured Home Satisfaction Affidavit",
        "Manufactured Home Severance Affidavit",
        "Manufactured Home Title Retirement",
        "Master Deed",
        "Mechanics Lien",
        "Mechanics Lien - Partial Release",
        "Mechanics Lien - Sep. Aff. Of Server",
        "Mechanics Lien Amendment",
        "Mechanics Lien Satisfaction",
        "Mechanics Lien Surety Bond",
        "Memorandum of Trust",
        "Mental Health Amendment",
        "Mental Health Lien",
        "Mental Health Lien Satisfaction",
        "Merger",
        "Meter Conservation Notice",
        "Meter Conservation Satisfaction",
        "Military Discharge",
        "Misc - Deeds With Pages",
        "Misc - Lien",
        "Misc - Lien Satisfaction",
        "Misc - Mortgage With Pages",
        "Misc Mortgage Book",
        "Mortgage",
        "Mortgage Book - No Charge",
        "Mortgage Modification",
        "Mortgage Partial Release",
        "Mortgage Satisfaction",
        "Mortgage Satisfaction Rescission",
        "Notice of Bankruptcy Discharge",
        "Notice of Foreclosure",
        "Notice of Pledge of Real Estate",
        "Notice of Termination",
        "Option",
        "Ordinance",
        "Partnership Agreement",
        "Plat - Legal Size",
        "Plat - Other Than Legal Size",
        "Plat Book - No Charge",
        "Power of Attorney",
        "Power of Attorney Revocation",
        "Probate Fiduciary Letter (Charge)",
        "Probate Fiduciary Letter Revocation",
        "Release - Deed Book",
        "Restrictions",
        "Revocation of Release",
        "Satisfaction - Deed Book",
        "State Tax Partial Release",
        "State Tax Withdrawal",
        "Sublease",
        "Subordination Agreement - Deed Book",
        "Subordination Agreement - Mortgage Book",
        "Subordination Agreement - Plat Book",
        "Tax Lien Amendment",
        "Tax Lien Expungement",
        "Tax Liens - Federal Charge",
        "Tax Liens - State",
        "Tax Satisfaction",
        "Trust Agreement",
        "Trust Agreement Revocation",
        "UCC1",
        "UCC3",
        "UCC3 Assignment",
        "UCC3 Termination",
        "Waiver"
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
    package.package_id = "P-12345"
    package.package_name = "SMITH 12345"
    package.document_type = "Deed - Timeshare"
    package.consideration = "0.00"
    package.execution_date = "03/15/2025"
    
    # Add legal description
    legal_desc = LegalDescription(
        description="ANDERSON OCEAN CLUB HPR U/W", 
        parcel_id="14-0078-0007-096-9"
    )
    package.add_legal_description(legal_desc)
    
    # Add reference information
    ref_info = ReferenceInformation(
        document_type="Deed - Timeshare",
        book="1234",
        page="56"
    )
    package.add_reference_info(ref_info)
    
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