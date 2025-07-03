# File: web_automation/excel_processor.py

import pandas as pd
import json
from datetime import datetime
from .pt61_config import get_version_config, get_required_columns
from .version_validator import validate_excel_for_version

def extract_data_from_excel(excel_path, version_display_name="PT-61 New Batch"):
    """
    Extract data from Excel file based on version configuration
    
    Args:
        excel_path (str): Path to Excel file
        version_display_name (str): Version to extract data for
    
    Returns:
        list: List of person data dictionaries
    """
    # Validate Excel file first
    validation_result = validate_excel_for_version(excel_path, version_display_name)
    if not validation_result.is_valid:
        raise ValueError(f"Excel validation failed: {', '.join(validation_result.errors)}")
    
    # Get version configuration
    version_key, config = get_version_config(version_display_name)
    required_columns = config["required_columns"]
    
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Extract relevant data and create JSON objects
    people_data = []
    for _, row in df.iterrows():
        person = extract_person_data(row, version_key, required_columns)
        people_data.append(person)
    
    return people_data

def extract_person_data(row, version_key, required_columns):
    """
    Extract person data from a row based on version requirements
    
    Args:
        row: Pandas row object
        version_key: Version key (new_batch, deedbacks, foreclosures)
        required_columns: List of required columns for this version
    
    Returns:
        dict: Person data dictionary
    """
    # Import here to avoid circular imports
    from .pt61_config import get_version_by_key
    
    # Base structure that all versions need
    person = {
        "individual_name": {
            "first": safe_get_cell_value(row, "First 1"),
            "middle": safe_get_cell_value(row, "Middle 1"), 
            "last": safe_get_cell_value(row, "Last 1")
        },
        "contract_number": safe_get_cell_value(row, "Contract Num"),
        "sales_price": format_sales_price(safe_get_cell_value(row, "Sales Price"))
    }
    
    # Get version config for dynamic extraction
    try:
        config = get_version_by_key(version_key)
        
        # Version-specific data extraction based on config
        if version_key == "new_batch":
            person.update(extract_new_batch_data(row, config))
        elif version_key == "deedbacks":
            person.update(extract_deedbacks_data(row, config))
        elif version_key == "foreclosures":
            person.update(extract_foreclosures_data(row, config))
            
    except Exception:
        # Fallback to hardcoded extraction if config fails
        if version_key == "new_batch":
            person.update(extract_new_batch_data(row))
        elif version_key == "deedbacks":
            person.update(extract_deedbacks_data(row))
        elif version_key == "foreclosures":
            person.update(extract_foreclosures_data(row))
    
    return person

def extract_new_batch_data(row, config=None):
    """Extract data specific to new_batch version"""
    data = {}
    
    # Date field - get column name from config if available
    date_column = "date on deed"  # Default
    if config:
        try:
            # Look for date column in required columns
            required_cols = config.get("required_columns", [])
            date_columns = [col for col in required_cols if "date" in col.lower() and "deed" in col.lower()]
            if date_columns:
                date_column = date_columns[0]
        except:
            pass
    
    date_value = safe_get_cell_value(row, date_column)
    data["date_on_deed"] = format_date(date_value)
    
    # Additional sellers (optional) - always check for these in new_batch
    additional_name = {
        "first": safe_get_cell_value(row, "First 2"),
        "middle": safe_get_cell_value(row, "Middle 2"),
        "last": safe_get_cell_value(row, "Last 2")
    }
    
    # Only include additional name if at least one field has data
    if any(additional_name.values()):
        data["additional_name"] = additional_name
    else:
        data["additional_name"] = {"first": "", "middle": "", "last": ""}
    
    return data

def extract_deedbacks_data(row, config=None):
    """Extract data specific to deedbacks version"""
    data = {}
    
    # Date field - get column name from config if available
    date_column = "Date on Deed"  # Default with capital D
    if config:
        try:
            required_cols = config.get("required_columns", [])
            date_columns = [col for col in required_cols if "date" in col.lower() and "deed" in col.lower()]
            if date_columns:
                date_column = date_columns[0]
        except:
            pass
    
    date_value = safe_get_cell_value(row, date_column)
    data["date_on_deed"] = format_date(date_value)
    
    # DB To field for buyer determination - get field name from config if available
    db_to_column = "DB To"  # Default
    if config:
        try:
            buyer_config = config["constants"]["buyer_section"]
            if "conditional_field" in buyer_config:
                db_to_column = buyer_config["conditional_field"]
        except:
            pass
    
    data["db_to"] = safe_get_cell_value(row, db_to_column)
    
    # No additional sellers for deedbacks version
    data["additional_name"] = {"first": "", "middle": "", "last": ""}
    
    return data

def extract_foreclosures_data(row, config=None):
    """Extract data specific to foreclosures version"""
    data = {}
    
    # Date field - get column name from config if available
    date_column = "date on deed"  # Default lowercase
    if config:
        try:
            required_cols = config.get("required_columns", [])
            date_columns = [col for col in required_cols if "date" in col.lower() and "deed" in col.lower()]
            if date_columns:
                date_column = date_columns[0]
        except:
            pass
    
    date_value = safe_get_cell_value(row, date_column)
    data["date_on_deed"] = format_date(date_value)
    
    # No additional sellers for foreclosures version
    data["additional_name"] = {"first": "", "middle": "", "last": ""}
    
    return data

def safe_get_cell_value(row, column_name):
    """
    Safely get cell value, handling missing columns and null values
    
    Args:
        row: Pandas row object
        column_name: Column name to extract
    
    Returns:
        str: Cell value as string, empty string if null/missing
    """
    try:
        if column_name in row.index:
            value = row[column_name]
            if pd.notnull(value):
                # Handle contract numbers and other numeric values that should be strings
                if column_name.lower() in ['contract num', 'contract_num', 'contract number']:
                    # Convert to string and remove .0 if it's a whole number
                    if isinstance(value, float) and value.is_integer():
                        return str(int(value))
                    else:
                        return str(value).strip()
                else:
                    return str(value).strip()
        return ""
    except (KeyError, IndexError):
        return ""

def format_date(date_value):
    """
    Format date value to MM/DD/YYYY string
    
    Args:
        date_value: Date value (can be datetime, string, or other)
    
    Returns:
        str: Formatted date string or empty string
    """
    if not date_value or date_value == "":
        return ""
    
    try:
        # If it's already a datetime object
        if isinstance(date_value, datetime):
            return date_value.strftime('%m/%d/%Y')
        
        # If it's a pandas timestamp
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%m/%d/%Y')
        
        # If it's a string that looks like datetime output
        if isinstance(date_value, str):
            # Handle pandas datetime string format like "2024-01-04 00:00:00"
            if " 00:00:00" in date_value:
                date_part = date_value.split(" ")[0]  # Get just the date part
                try:
                    parsed_date = datetime.strptime(date_part, '%Y-%m-%d')
                    return parsed_date.strftime('%m/%d/%Y')
                except ValueError:
                    pass
            
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    parsed_date = datetime.strptime(date_value, fmt)
                    return parsed_date.strftime('%m/%d/%Y')
                except ValueError:
                    continue
        
        # If all else fails, return as string
        return str(date_value)
        
    except Exception:
        return str(date_value) if date_value else ""

def format_sales_price(price_value):
    """
    Format sales price to 2 decimal places
    
    Args:
        price_value: Price value (can be number, string, etc.)
    
    Returns:
        str: Formatted price string
    """
    if not price_value or price_value == "":
        return "0.00"
    
    try:
        # Convert to float and format
        price_float = float(price_value)
        return f"{price_float:.2f}"
    except (ValueError, TypeError):
        # If conversion fails, try to extract numbers from string
        try:
            import re
            numbers = re.findall(r'[\d.]+', str(price_value))
            if numbers:
                price_float = float(numbers[0])
                return f"{price_float:.2f}"
        except:
            pass
        
        return "0.00"

def print_extracted_data(people_data):
    """Print extracted data for debugging"""
    for i, person in enumerate(people_data):
        print(f"Person {i + 1}:")
        print(json.dumps(person, indent=2))
        print()  # Add a blank line between people

def validate_and_extract_data(excel_path, version_display_name="PT-61 New Batch"):
    """
    Validate Excel file and extract data if valid
    
    Args:
        excel_path (str): Path to Excel file
        version_display_name (str): Version to process
    
    Returns:
        tuple: (success: bool, data: list or error_message: str)
    """
    try:
        # First validate
        validation_result = validate_excel_for_version(excel_path, version_display_name)
        
        if not validation_result.is_valid:
            error_msg = "Excel validation failed:\n"
            error_msg += "\n".join(f"• {error}" for error in validation_result.errors)
            return False, error_msg
        
        # If valid, extract data
        data = extract_data_from_excel(excel_path, version_display_name)
        return True, data
        
    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}"

if __name__ == "__main__":
    # This block allows you to test the function independently
    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    
    print("Testing New Batch version:")
    success, result = validate_and_extract_data(test_excel_path, "PT-61 New Batch")
    
    if success:
        print("✅ Validation passed")
        print(f"Extracted {len(result)} records")
        if result:
            print("\nFirst record:")
            print(json.dumps(result[0], indent=2))
    else:
        print("❌ Validation failed")
        print(result)