# core/county_config.py - Updated with workflow-specific document types and HOA-FCL support
from typing import Dict, List, Any


class CountyConfig:
    """Base class for county-specific configuration"""
    
    # County identification
    COUNTY_ID = ""
    COUNTY_NAME = ""
    
    # Legacy document types (for backward compatibility)
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
    SUPPORTED_WORKFLOWS = ["fcl", "deedbacks"]
    
    # Fixed values from requirements
    FIXED_PARCEL_ID = "14-0078-0007-096-9"
    FIXED_TAX_EXEMPT = True
    FIXED_DEED_GRANTEE = "CENTENNIAL PARK DEVELOPMENT LLC"
    FIXED_SAT_GRANTEE = "CENTENNIAL PARK DEVELOPMENT LLC"


class HorryCountyConfig(CountyConfig):
    """Horry County, SC configuration"""
    
    COUNTY_ID = "SCCP49"
    COUNTY_NAME = "Horry County, SC"
    
    # Legacy document types (for backward compatibility with old code)
    DEED_DOCUMENT_TYPE = "Deed - Timeshare"
    MORTGAGE_DOCUMENT_TYPE = "Mortgage Satisfaction"
    
    # Supported workflows
    SUPPORTED_WORKFLOWS = ["mtg_fcl", "hoa_fcl"]
    
    # No fixed values for Horry - all come from Excel data
    FIXED_PARCEL_ID = None
    FIXED_TAX_EXEMPT = None
    FIXED_DEED_GRANTEE = None


# Workflow configurations per county with document types
WORKFLOW_CONFIGS = {
    "GAC3TH": {  # Fulton County
        "fcl": {
            "name": "Foreclosure (FCL)",
            "description": "Foreclosure documents with PDF stacks",
            "input_type": "pdf_stacks",
            "supports_processing": True,
            "document_types": {
                "DEED_DOCUMENT_TYPE": "DEED",
                "MORTGAGE_DOCUMENT_TYPE": "SATISFACTION"
            },
            "required_files": [
                {
                    "key": "excel",
                    "label": "Excel File",
                    "placeholder": "Select Excel file with package data",
                    "filter": "Excel Files (*.xlsx *.xls)",
                    "type": "file"
                },
                {
                    "key": "deed_stack",
                    "label": "Deed Stack PDF",
                    "placeholder": "Select deed stack PDF (3 pages per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                },
                {
                    "key": "pt61_stack",
                    "label": "PT-61 Stack PDF",
                    "placeholder": "Select PT-61 stack PDF (1 page per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                },
                {
                    "key": "mortgage_stack",
                    "label": "Mortgage Satisfaction Stack PDF",
                    "placeholder": "Select mortgage satisfaction stack PDF (1 page per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                }
            ]
        },
        "deedbacks": {
            "name": "Deedbacks",
            "description": "Deedback documents with directory input",
            "input_type": "directory",
            "supports_processing": True,
            "document_types": {
                "DEED_DOCUMENT_TYPE": "DEED",
                "MORTGAGE_DOCUMENT_TYPE": "SATISFACTION"
            },
            "required_files": [
                {
                    "key": "excel",
                    "label": "Excel File",
                    "placeholder": "Select Excel file with package data",
                    "filter": "Excel Files (*.xlsx *.xls)",
                    "type": "file"
                },
                {
                    "key": "documents_directory",
                    "label": "Documents Directory",
                    "placeholder": "Select directory containing all PDF documents",
                    "filter": "",
                    "type": "directory"
                }
            ]
        }
    },
    "SCCP49": {  # Horry County
        "mtg_fcl": {
            "name": "Timeshare Deed (MTG-FCL)",
            "description": "Horry County timeshare deed and mortgage satisfaction documents",
            "input_type": "pdf_stacks",
            "supports_processing": True,
            "document_types": {
                "DEED_DOCUMENT_TYPE": "Deed - Timeshare",
                "MORTGAGE_DOCUMENT_TYPE": "Mortgage Satisfaction"
            },
            "required_files": [
                {
                    "key": "excel",
                    "label": "Excel File",
                    "placeholder": "Select Excel file with package data",
                    "filter": "Excel Files (*.xlsx *.xls)",
                    "type": "file"
                },
                {
                    "key": "deed_stack",
                    "label": "Deed Stack PDF",
                    "placeholder": "Select deed stack PDF (2 pages per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                },
                {
                    "key": "affidavit_stack",
                    "label": "Affidavit Stack PDF",
                    "placeholder": "Select affidavit stack PDF (2 pages per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                },
                {
                    "key": "mortgage_stack",
                    "label": "Mortgage Satisfaction Stack PDF",
                    "placeholder": "Select mortgage satisfaction stack PDF (1 page per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                }
            ]
        },
        "hoa_fcl": {
            "name": "HOA Foreclosure (HOA-FCL)",
            "description": "HOA foreclosure with condo lien satisfaction documents",
            "input_type": "pdf_stacks",
            "supports_processing": True,
            "document_types": {
                "DEED_DOCUMENT_TYPE": "Deed - Timeshare",
                "SATISFACTION_DOCUMENT_TYPE": "Condo Lien Satisfaction"
            },
            "required_files": [
                {
                    "key": "excel",
                    "label": "Excel File",
                    "placeholder": "Select Excel file with package data",
                    "filter": "Excel Files (*.xlsx *.xls)",
                    "type": "file"
                },
                {
                    "key": "deed_stack",
                    "label": "Deed Stack PDF",
                    "placeholder": "Select deed stack PDF (2 pages per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                },
                {
                    "key": "affidavit_stack",
                    "label": "Affidavit Stack PDF",
                    "placeholder": "Select affidavit stack PDF (2 pages per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                },
                {
                    "key": "condo_lien_stack",
                    "label": "Condo Lien Satisfaction Stack PDF",
                    "placeholder": "Select condo lien satisfaction stack PDF (1 page per document)",
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                }
            ]
        }
    }
}


# Registry of available counties
COUNTY_CONFIGS = {
    "GAC3TH": FultonCountyConfig,
    "SCCP49": HorryCountyConfig
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


def get_county_workflows(county_id: str) -> Dict[str, Dict[str, Any]]:
    """Get supported workflows for a county with their configurations"""
    if county_id not in WORKFLOW_CONFIGS:
        return {}
    return WORKFLOW_CONFIGS[county_id]


def get_workflow_config(county_id: str, workflow_id: str) -> Dict[str, Any]:
    """Get specific workflow configuration"""
    workflows = get_county_workflows(county_id)
    if workflow_id not in workflows:
        raise ValueError(f"Workflow '{workflow_id}' not supported for county '{county_id}'")
    return workflows[workflow_id]


def get_workflow_document_types(county_id: str, workflow_id: str) -> Dict[str, str]:
    """Get document types for a specific workflow"""
    workflow_config = get_workflow_config(county_id, workflow_id)
    return workflow_config.get("document_types", {})


def is_county_supported(county_id: str) -> bool:
    """Check if a county is supported"""
    return county_id in COUNTY_CONFIGS


def get_county_display_name(county_id: str) -> str:
    """Get display name for a county"""
    if county_id in COUNTY_CONFIGS:
        return COUNTY_CONFIGS[county_id].COUNTY_NAME
    return f"Unknown County ({county_id})"


def get_workflow_display_name(county_id: str, workflow_id: str) -> str:
    """Get display name for a workflow"""
    try:
        config = get_workflow_config(county_id, workflow_id)
        return config["name"]
    except ValueError:
        return f"Unknown Workflow ({workflow_id})"