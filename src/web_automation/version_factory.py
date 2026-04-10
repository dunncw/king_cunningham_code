# File: web_automation/version_factory.py

from .pt61_config import get_version_key
from .new_batch_automation import NewBatchAutomation
from .deedbacks_automation import DeedbacksAutomation
from .foreclosures_automation import ForeclosuresAutomation

def create_automation_worker(excel_path, browser, username, password, save_location, version_display_name, document_stacking=False):
    """
    Factory function to create the appropriate automation worker based on version
    
    Args:
        excel_path (str): Path to Excel file
        browser (str): Browser choice
        username (str): Login username
        password (str): Login password
        save_location (str): Where to save PDFs
        version_display_name (str): Display name of version
        document_stacking (bool): Whether to combine PDFs into one document
    
    Returns:
        BasePT61Automation: Appropriate automation worker instance
    """
    # Get version key from display name
    version_key = get_version_key(version_display_name)
    
    # Create appropriate automation worker (all now support document_stacking parameter)
    if version_key == "new_batch":
        return NewBatchAutomation(excel_path, browser, username, password, save_location, version_display_name, document_stacking)
    elif version_key == "deedbacks":
        return DeedbacksAutomation(excel_path, browser, username, password, save_location, version_display_name, document_stacking)
    elif version_key == "foreclosures":
        return ForeclosuresAutomation(excel_path, browser, username, password, save_location, version_display_name, document_stacking)
    else:
        raise ValueError(f"Unknown version key: {version_key}")

def get_available_versions():
    """Get list of all available automation versions"""
    return ["PT-61 New Batch", "PT-61 Deedbacks", "PT61 Foreclosures"]