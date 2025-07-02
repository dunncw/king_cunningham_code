# File: web_automation/version_validator.py

import pandas as pd
from .pt61_config import get_required_columns, get_version_config

class ValidationResult:
    def __init__(self, is_valid=True, errors=None, warnings=None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning):
        self.warnings.append(warning)

def validate_excel_for_version(excel_path, version_display_name):
    """
    Validate that an Excel file has the required columns for a specific PT61 version
    
    Args:
        excel_path (str): Path to Excel file
        version_display_name (str): Display name of the version (e.g., "PT-61 New Batch")
    
    Returns:
        ValidationResult: Object containing validation status and any errors/warnings
    """
    result = ValidationResult()
    
    try:
        # Read Excel file to get column headers
        df = pd.read_excel(excel_path, nrows=0)  # Just read headers
        excel_columns = [col.strip() for col in df.columns.tolist()]  # Remove whitespace
        excel_columns_lower = [col.lower() for col in excel_columns]  # For case-insensitive matching
        
        # Get required columns for this version
        required_columns = get_required_columns(version_display_name)
        version_key, config = get_version_config(version_display_name)
        
        # Check for missing required columns
        missing_columns = []
        found_columns = []
        
        for required_col in required_columns:
            # Try exact match first
            if required_col in excel_columns:
                found_columns.append(required_col)
            # Try case-insensitive match
            elif required_col.lower() in excel_columns_lower:
                # Find the actual column name
                actual_col = excel_columns[excel_columns_lower.index(required_col.lower())]
                found_columns.append(actual_col)
                result.add_warning(f"Column '{required_col}' found as '{actual_col}' (case mismatch)")
            else:
                # Check if it's an optional column (for additional sellers in new_batch)
                if version_key == "new_batch" and required_col in ["Last 2", "First 2", "Middle 2"]:
                    result.add_warning(f"Optional column '{required_col}' not found - additional sellers won't be processed")
                else:
                    missing_columns.append(required_col)
        
        # Add errors for missing required columns
        for missing_col in missing_columns:
            result.add_error(f"Required column '{missing_col}' not found in Excel file")
        
        # Check if Excel file is empty
        df_data = pd.read_excel(excel_path)
        if df_data.empty:
            result.add_error("Excel file contains no data rows")
        elif len(df_data) == 0:
            result.add_error("Excel file contains only headers, no data")
        else:
            result.add_warning(f"Found {len(df_data)} data rows to process")
        
        # Add info about extra columns (not an error, just informational)
        extra_columns = [col for col in excel_columns if col not in required_columns]
        if extra_columns:
            result.add_warning(f"Extra columns found (will be ignored): {', '.join(extra_columns[:5])}" + 
                             ("..." if len(extra_columns) > 5 else ""))
        
    except FileNotFoundError:
        result.add_error(f"Excel file not found: {excel_path}")
    except Exception as e:
        result.add_error(f"Error reading Excel file: {str(e)}")
    
    return result

def get_validation_summary(excel_path, version_display_name):
    """
    Get a human-readable validation summary
    
    Returns:
        str: Formatted validation summary
    """
    result = validate_excel_for_version(excel_path, version_display_name)
    
    summary = f"Validation for {version_display_name}:\n"
    summary += "=" * 50 + "\n"
    
    if result.is_valid:
        summary += "✅ VALIDATION PASSED\n\n"
    else:
        summary += "❌ VALIDATION FAILED\n\n"
    
    if result.errors:
        summary += "ERRORS:\n"
        for error in result.errors:
            summary += f"  • {error}\n"
        summary += "\n"
    
    if result.warnings:
        summary += "WARNINGS:\n"
        for warning in result.warnings:
            summary += f"  • {warning}\n"
        summary += "\n"
    
    # Add required columns info
    required_columns = get_required_columns(version_display_name)
    summary += f"REQUIRED COLUMNS for {version_display_name}:\n"
    for col in required_columns:
        summary += f"  • {col}\n"
    
    return summary

# Convenience function for quick validation
def is_excel_valid_for_version(excel_path, version_display_name):
    """
    Quick check if Excel file is valid for a version
    
    Returns:
        bool: True if valid, False otherwise
    """
    result = validate_excel_for_version(excel_path, version_display_name)
    return result.is_valid