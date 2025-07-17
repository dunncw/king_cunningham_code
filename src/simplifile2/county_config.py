# simplifile2/county_config.py - Minimal county configuration
from typing import Dict, List, Any


class CountyConfig:
    """Base class for county-specific configuration"""
    
    # County identification
    COUNTY_ID = ""
    COUNTY_NAME = ""
    
    # Document types
    DEED_DOCUMENT_TYPE = ""
    MORTGAGE_DOCUMENT_TYPE = ""
    
    # Supported workflows
    SUPPORTED_WORKFLOWS = []
    
    # Fixed values (None if not applicable)
    FIXED_PARCEL_ID = None
    FIXED_TAX_EXEMPT = None
    FIXED_DEED_GRANTEE = None
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            "county_id": cls.COUNTY_ID,
            "county_name": cls.COUNTY_NAME,
            "deed_document_type": cls.DEED_DOCUMENT_TYPE,
            "mortgage_document_type": cls.MORTGAGE_DOCUMENT_TYPE,
            "supported_workflows": cls.SUPPORTED_WORKFLOWS,
            "fixed_parcel_id": cls.FIXED_PARCEL_ID,
            "fixed_tax_exempt": cls.FIXED_TAX_EXEMPT,
            "fixed_deed_grantee": cls.FIXED_DEED_GRANTEE
        }


class FultonCountyConfig(CountyConfig):
    """Fulton County, GA configuration"""
    
    COUNTY_ID = "GAC3TH"
    COUNTY_NAME = "Fulton County, GA"
    
    # Document types specific to Fulton County
    DEED_DOCUMENT_TYPE = "DEED"
    MORTGAGE_DOCUMENT_TYPE = "SATISFACTION"
    
    # Supported workflows
    SUPPORTED_WORKFLOWS = ["fcl"]
    
    # Fixed values from requirements
    FIXED_PARCEL_ID = "14-0078-0007-096-9"
    FIXED_TAX_EXEMPT = True
    FIXED_DEED_GRANTEE = "CENTENNIAL PARK DEVELOPMENT LLC"


# Registry of available counties
COUNTY_CONFIGS = {
    "GAC3TH": FultonCountyConfig
}


def get_county_config(county_id: str) -> CountyConfig:
    """Get configuration for a specific county"""
    if county_id not in COUNTY_CONFIGS:
        raise ValueError(f"Unsupported county: {county_id}")
    return COUNTY_CONFIGS[county_id]


def get_available_counties() -> Dict[str, str]:
    """Get list of available counties"""
    return {
        county_id: config.COUNTY_NAME 
        for county_id, config in COUNTY_CONFIGS.items()
    }


def get_county_workflows(county_id: str) -> List[str]:
    """Get supported workflows for a county"""
    config = get_county_config(county_id)
    return config.SUPPORTED_WORKFLOWS


def is_county_supported(county_id: str) -> bool:
    """Check if a county is supported"""
    return county_id in COUNTY_CONFIGS


def get_county_display_name(county_id: str) -> str:
    """Get display name for a county"""
    if county_id in COUNTY_CONFIGS:
        return COUNTY_CONFIGS[county_id].COUNTY_NAME
    return f"Unknown County ({county_id})"