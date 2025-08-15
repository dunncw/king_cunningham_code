# simplifile3/core/county_config.py - County reference data (workflows removed)
from typing import Dict, Any


class CountyConfig:
    """Base class for county-specific reference data"""
    
    # County identification
    COUNTY_ID = ""
    COUNTY_NAME = ""
    
    # Document types supported by this county
    DOCUMENT_TYPES = {}
    
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
            "document_types": cls.DOCUMENT_TYPES,
            "fixed_parcel_id": cls.FIXED_PARCEL_ID,
            "fixed_tax_exempt": cls.FIXED_TAX_EXEMPT,
            "fixed_deed_grantee": cls.FIXED_DEED_GRANTEE
        }


class HorryCountyConfig(CountyConfig):
    """Horry County, SC configuration"""
    
    COUNTY_ID = "SCCP49"
    COUNTY_NAME = "Horry County, SC"
    
    # Document types specific to Horry County
    DOCUMENT_TYPES = {
        "DEED_TIMESHARE": "Deed - Timeshare",
        "MORTGAGE_SATISFACTION": "Mortgage Satisfaction",
        "CONDO_LIEN_SATISFACTION": "Condo Lien Satisfaction"
    }
    
    # No fixed values for Horry - all come from workflow data
    FIXED_PARCEL_ID = None
    FIXED_TAX_EXEMPT = None
    FIXED_DEED_GRANTEE = None


class BeaufortCountyConfig(CountyConfig):
    """Beaufort County, SC configuration"""
    
    COUNTY_ID = "SCCY4G"
    COUNTY_NAME = "Beaufort County, SC"
    
    # Document types specific to Beaufort County
    DOCUMENT_TYPES = {
        "DEED_HILTON_HEAD_TIMESHARE": "DEED - HILTON HEAD TIMESHARE",
        "MORTGAGE_SATISFACTION": "MORT - SATISFACTION"
    }
    
    # No fixed values for Beaufort - all come from workflow data
    FIXED_PARCEL_ID = None
    FIXED_TAX_EXEMPT = None
    FIXED_DEED_GRANTEE = None


class FultonCountyConfig(CountyConfig):
    """Fulton County, GA configuration"""
    
    COUNTY_ID = "GAC3TH"
    COUNTY_NAME = "Fulton County, GA"
    
    # Document types specific to Fulton County
    DOCUMENT_TYPES = {
        "DEED": "DEED",
        "SATISFACTION": "SATISFACTION"
    }
    
    # Fixed values from requirements
    FIXED_PARCEL_ID = "14-0078-0007-096-9"
    FIXED_TAX_EXEMPT = True
    FIXED_DEED_GRANTEE = "CENTENNIAL PARK DEVELOPMENT LLC"


# Registry of available counties
COUNTY_CONFIGS = {
    "SCCP49": HorryCountyConfig,
    "SCCY4G": BeaufortCountyConfig, 
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


def is_county_supported(county_id: str) -> bool:
    """Check if a county is supported"""
    return county_id in COUNTY_CONFIGS


def get_county_display_name(county_id: str) -> str:
    """Get display name for a county"""
    if county_id in COUNTY_CONFIGS:
        return COUNTY_CONFIGS[county_id].COUNTY_NAME
    return f"Unknown County ({county_id})"