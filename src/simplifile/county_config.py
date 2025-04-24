# county_config.py - Centralized county-specific configurations for Simplifile
from typing import Dict, Any, List

class CountyConfig:
    """Base class for county-specific configuration"""
    
    # County identification
    COUNTY_ID = ""
    COUNTY_NAME = ""
    
    # Document type configurations
    DEED_DOCUMENT_TYPE = "Deed - Timeshare"
    MORTGAGE_DOCUMENT_TYPE = "Mortgage Satisfaction"
    
    # Required fields for deed documents
    DEED_REQUIRES_EXECUTION_DATE = True
    DEED_REQUIRES_LEGAL_DESCRIPTION = True
    DEED_REQUIRES_REFERENCE_INFO = True
    
    # Required fields for mortgage documents
    MORTGAGE_REQUIRES_EXECUTION_DATE = True
    MORTGAGE_REQUIRES_LEGAL_DESCRIPTION = True
    MORTGAGE_REQUIRES_REFERENCE_INFO = True
    
    # Grantee configurations
    DEED_GRANTEES_USE_GRANTOR_GRANTEE = True
    DEED_GRANTEES_USE_OWNERS = False
    
    # Special configurations
    KING_CUNNINGHAM_REQUIRED_FOR_DEED = True
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as a dictionary"""
        return {
            "county_id": cls.COUNTY_ID,
            "county_name": cls.COUNTY_NAME,
            "deed_document_type": cls.DEED_DOCUMENT_TYPE,
            "mortgage_document_type": cls.MORTGAGE_DOCUMENT_TYPE,
            "deed_requires_execution_date": cls.DEED_REQUIRES_EXECUTION_DATE,
            "deed_requires_legal_description": cls.DEED_REQUIRES_LEGAL_DESCRIPTION,
            "deed_requires_reference_info": cls.DEED_REQUIRES_REFERENCE_INFO,
            "mortgage_requires_execution_date": cls.MORTGAGE_REQUIRES_EXECUTION_DATE,
            "mortgage_requires_legal_description": cls.MORTGAGE_REQUIRES_LEGAL_DESCRIPTION,
            "mortgage_requires_reference_info": cls.MORTGAGE_REQUIRES_REFERENCE_INFO,
            "deed_grantees_use_grantor_grantee": cls.DEED_GRANTEES_USE_GRANTOR_GRANTEE,
            "deed_grantees_use_owners": cls.DEED_GRANTEES_USE_OWNERS,
            "king_cunningham_required_for_deed": cls.KING_CUNNINGHAM_REQUIRED_FOR_DEED
        }


class HorryCountyConfig(CountyConfig):
    """Horry County, SC configuration"""
    
    COUNTY_ID = "SCCP49"
    COUNTY_NAME = "Horry County, SC"
    
    DEED_DOCUMENT_TYPE = "Deed - Timeshare"
    MORTGAGE_DOCUMENT_TYPE = "Mortgage Satisfaction"
    
    DEED_REQUIRES_EXECUTION_DATE = True
    DEED_REQUIRES_LEGAL_DESCRIPTION = True
    DEED_REQUIRES_REFERENCE_INFO = True
    
    MORTGAGE_REQUIRES_EXECUTION_DATE = True
    MORTGAGE_REQUIRES_LEGAL_DESCRIPTION = True
    MORTGAGE_REQUIRES_REFERENCE_INFO = True
    
    DEED_GRANTEES_USE_GRANTOR_GRANTEE = True
    DEED_GRANTEES_USE_OWNERS = False
    
    KING_CUNNINGHAM_REQUIRED_FOR_DEED = True


class BeaufortCountyConfig(CountyConfig):
    """Beaufort County, GA configuration"""
    
    COUNTY_ID = "SCCY4G"
    COUNTY_NAME = "Beaufort County, GA"
    
    DEED_DOCUMENT_TYPE = "DEED - HILTON HEAD TIMESHARE"
    MORTGAGE_DOCUMENT_TYPE = "MORT - SATISFACTION"
    
    DEED_REQUIRES_EXECUTION_DATE = False
    DEED_REQUIRES_LEGAL_DESCRIPTION = False
    DEED_REQUIRES_REFERENCE_INFO = False
    
    MORTGAGE_REQUIRES_EXECUTION_DATE = False
    MORTGAGE_REQUIRES_LEGAL_DESCRIPTION = False
    MORTGAGE_REQUIRES_REFERENCE_INFO = False
    
    DEED_GRANTEES_USE_GRANTOR_GRANTEE = False
    DEED_GRANTEES_USE_OWNERS = True
    
    KING_CUNNINGHAM_REQUIRED_FOR_DEED = True


# Add more county configurations as needed
class WilliamsburgCountyConfig(CountyConfig):
    """Williamsburg County, SC configuration"""
    
    COUNTY_ID = "SCCE6P"
    COUNTY_NAME = "Williamsburg County, SC"
    
    # Using same config as Horry County for now
    DEED_DOCUMENT_TYPE = "Deed - Timeshare"
    MORTGAGE_DOCUMENT_TYPE = "Mortgage Satisfaction"


class FultonCountyConfig(CountyConfig):
    """Fulton County, GA configuration"""
    
    COUNTY_ID = "GAC3TH"
    COUNTY_NAME = "Fulton County, GA"
    
    # Using same config as Beaufort County for now
    DEED_DOCUMENT_TYPE = "DEED - HILTON HEAD TIMESHARE"
    MORTGAGE_DOCUMENT_TYPE = "MORT - SATISFACTION"


class ForsythCountyConfig(CountyConfig):
    """Forsyth County, NC configuration"""
    
    COUNTY_ID = "NCCHLB"
    COUNTY_NAME = "Forsyth County, NC"
    
    # Using default config for now
    DEED_DOCUMENT_TYPE = "Deed - Timeshare"
    MORTGAGE_DOCUMENT_TYPE = "Mortgage Satisfaction"


# Registry of all county configurations
COUNTY_CONFIGS = {
    "SCCP49": HorryCountyConfig,
    "SCCY4G": BeaufortCountyConfig,
    "SCCE6P": WilliamsburgCountyConfig,
    "GAC3TH": FultonCountyConfig,
    "NCCHLB": ForsythCountyConfig
}


def get_county_config(county_id: str) -> CountyConfig:
    """Get configuration for a specific county"""
    return COUNTY_CONFIGS.get(county_id, HorryCountyConfig)