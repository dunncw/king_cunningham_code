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
    validation_result = validate_excel_for_version(excel_path, version_display_name)
    if not validation_result.is_valid:
        raise ValueError(f"Excel validation failed: {', '.join(validation_result.errors)}")
    
    version_key, config = get_version_config(version_display_name)
    required_columns = config["required_columns"]
    
    df = pd.read_excel(excel_path)
    
    people_data = []
    for _, row in df.iterrows():
        person = extract_person_data(row, version_key, required_columns)

        if (not person['individual_name']['first'].strip() or
            not person['individual_name']['last'].strip() or
            not person['contract_number'].strip()):
            continue

        people_data.append(person)
    
    return people_data

def extract_person_data(row, version_key, required_columns):
    """
    Extract person data from a row based on version requirements
    """
    from .pt61_config import get_version_by_key
    
    person = {
        "individual_name": {
            "first": safe_get_cell_value(row, "First 1"),
            "middle": safe_get_cell_value(row, "Middle 1"), 
            "last": safe_get_cell_value(row, "Last 1")
        },
        "contract_number": safe_get_cell_value(row, "Contract Num"),
        "sales_price": format_sales_price(safe_get_cell_value(row, "Sales Price"))
    }
    
    try:
        config = get_version_by_key(version_key)
        
        if version_key == "new_batch":
            person.update(extract_new_batch_data(row, config))
        elif version_key == "deedbacks":
            person.update(extract_deedbacks_data(row, config))
        elif version_key == "foreclosures":
            person.update(extract_foreclosures_data(row, config))
            
    except Exception:
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
    
    date_column = "date on deed"
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
    
    additional_name = {
        "first": safe_get_cell_value(row, "First 2"),
        "middle": safe_get_cell_value(row, "Middle 2"),
        "last": safe_get_cell_value(row, "Last 2")
    }
    
    if any(additional_name.values()):
        data["additional_name"] = additional_name
    else:
        data["additional_name"] = {"first": "", "middle": "", "last": ""}
    
    return data

def extract_deedbacks_data(row, config=None):
    """Extract data specific to deedbacks version"""
    data = {}
    
    date_column = "Date on Deed"
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
    
    db_to_column = "DB To"
    if config:
        try:
            buyer_config = config["constants"]["buyer_section"]
            if "conditional_field" in buyer_config:
                db_to_column = buyer_config["conditional_field"]
        except:
            pass
    
    data["db_to"] = safe_get_cell_value(row, db_to_column)
    
    data["additional_name"] = {"first": "", "middle": "", "last": ""}
    
    return data

def extract_foreclosures_data(row, config=None):
    """Extract data specific to foreclosures version"""
    data = {}
    
    date_column = "date on deed"
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
    
    data["additional_name"] = {"first": "", "middle": "", "last": ""}
    
    return data

def safe_get_cell_value(row, column_name):
    """
    Safely get cell value, handling missing columns and null values
    """
    try:
        if column_name in row.index:
            value = row[column_name]
            if pd.notnull(value):
                if column_name.lower() in ['contract num', 'contract_num', 'contract number']:
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
    Format date value to MM/DD/YYYY string (required format for PT-61 form)
    
    Args:
        date_value: Date value (can be datetime, Timestamp, string, or other)
    
    Returns:
        str: Formatted date string in MM/DD/YYYY format
    """
    if date_value is None or date_value == "":
        return ""
    
    try:
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%m/%d/%Y')
        
        if isinstance(date_value, str):
            date_value = date_value.strip()
            
            if " " in date_value:
                date_value = date_value.split(" ")[0]
            
            parse_formats = [
                '%Y-%m-%d',      # ISO format: 2024-01-15
                '%m/%d/%Y',      # US format: 01/15/2024
                '%m-%d-%Y',      # US with dashes: 01-15-2024
                '%d/%m/%Y',      # European: 15/01/2024
                '%Y/%m/%d',      # Alternative ISO: 2024/01/15
                '%m/%d/%y',      # Short year: 01/15/24
                '%m-%d-%y',      # Short year with dashes: 01-15-24
            ]
            
            for fmt in parse_formats:
                try:
                    parsed_date = datetime.strptime(date_value, fmt)
                    return parsed_date.strftime('%m/%d/%Y')
                except ValueError:
                    continue
        
        return str(date_value)
        
    except Exception as e:
        print(f"[WARNING] Date format error for '{date_value}': {e}")
        return str(date_value) if date_value else ""

def format_sales_price(price_value):
    """
    Format sales price to 2 decimal places
    """
    if not price_value or price_value == "":
        return "0.00"
    
    try:
        price_float = float(price_value)
        return f"{price_float:.2f}"
    except (ValueError, TypeError):
        try:
            import re
            numbers = re.findall(r'[\d.]+', str(price_value))
            if numbers:
                price_float = float(numbers[0])
                return f"{price_float:.2f}"
        except:
            pass
        
        return "0.00"

def validate_and_extract_data(excel_path, version_display_name="PT-61 New Batch"):
    """
    Validate Excel file and extract data if valid
    
    Returns:
        tuple: (success: bool, data: list or error_message: str)
    """
    try:
        validation_result = validate_excel_for_version(excel_path, version_display_name)
        
        if not validation_result.is_valid:
            error_msg = "Excel validation failed:\n"
            error_msg += "\n".join(f"- {error}" for error in validation_result.errors)
            return False, error_msg
        
        data = extract_data_from_excel(excel_path, version_display_name)
        return True, data
        
    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}"

if __name__ == "__main__":
    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    
    print("Testing New Batch version:")
    success, result = validate_and_extract_data(test_excel_path, "PT-61 New Batch")
    
    if success:
        print("Validation passed")
        print(f"Extracted {len(result)} records")
        if result:
            print("\nFirst record:")
            print(json.dumps(result[0], indent=2))
    else:
        print("Validation failed")
        print(result)