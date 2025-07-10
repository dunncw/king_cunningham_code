# File: web_automation/pt61_config.py

PT61_VERSIONS = {
    "new_batch": {
        "display_name": "New Batch",
        "description": "Current version for new Wyndham batch processing",
        "required_columns": [
            "Contract Num",
            "Last 1", 
            "First 1", 
            "Middle 1",
            "Last 2",     # Optional - for additional sellers
            "First 2",    # Optional - for additional sellers
            "Middle 2",   # Optional - for additional sellers
            "Sales Price",
            "date on deed"
        ],
        "constants": {
            "login": {
                "url": "https://apps.gsccca.org/pt61efiling/",
                "username_field": "txtUserID",
                "password_field": "txtPassword"
            },
            "seller_section": {
                "type": "business",
                "address": {
                    "line1": "CENTENNIAL PARK DEVELOPMENT LLC",
                    "line2": "c/o 155 CENTENNIAL OLYMPIC PARK DR. NW",
                    "city": "ATLANTA",
                    "state": "GA",
                    "zip": "30313"
                }
            },
            "buyer_section": {
                "type": "individual",
                "name": "CENTENNIAL PARK DEVELOPMENT LLC",
                "address": "same_as_seller"
            },
            "property_section": {
                "street_number": "155",
                "street_name": "Centennial Olympic Park",
                "street_type": "Drive",
                "street_type_value": "DR",  # Form value
                "post_direction": "NW",
                "county": "Fulton",
                "county_value": "60",  # Form value
                "map_parcel": "14-0078-0007-096-9"
            },
            "tax_computation": {
                "exempt_code": "None",
                "fair_market_value": "0",
                "liens_encumbrances": "0"
            },
            "file_naming": {
                "pattern": "{last_name}_{contract_num}_PT61.pdf",
                "fields": ["Last 1", "Contract Num"]
            }
        }
    },
    
    "deedbacks": {
        "display_name": "Deedbacks", 
        "description": "For Wyndham deedback processing (Brittany's version)",
        "required_columns": [
            "Contract Num",
            "Last 1",
            "First 1", 
            "Middle 1",
            "Sales Price",
            "Date on Deed",  # Note: different capitalization
            "DB To"  # Determines buyer (CENTENNIAL vs WYNDHAM)
        ],
        "constants": {
            "login": {
                "url": "https://apps.gsccca.org/pt61efiling/",
                "username_field": "txtUserID", 
                "password_field": "txtPassword"
            },
            "seller_section": {
                "type": "individual",
                "address": {
                    "line1": "C/O 155 CENTENNIAL OLYMPIC PARK DRIVE NW",
                    "city": "ATLANTA",
                    "state": "GA",
                    "zip": "30313"
                }
            },
            "buyer_section": {
                "type": "business",
                "address": {
                    "line1": "155 CENTENNIAL OLYMPIC PARK DRIVE NW",
                    "city": "ATLANTA",
                    "state": "GA",
                    "zip": "30313"
                }
            },
            "property_section": {
                "street_number": "155", 
                "street_name": "Centennial Olympic Park",
                "street_type": "Drive",
                "street_type_value": "DR",
                "post_direction": "NW",
                "county": "Fulton",
                "county_value": "60",
                "map_parcel": "14-0078-0007-096-9"
            },
            "tax_computation": {
                "exempt_code": "None",
                "fair_market_value": "0",
                "liens_encumbrances": "0"
            },
            "file_naming": {
                "pattern": "{last_name}_{contract_num}_PT61.pdf", 
                "fields": ["Last 1", "Contract Num"]
            }
        }
    },
    
    "foreclosures": {
        "display_name": "Foreclosures",
        "description": "For foreclosure processing (Shannon's version)",
        "required_columns": [
            "Contract Num",
            "First 1",
            "Middle 1", 
            "Last 1",
            "date on deed",
            "Sales Price"
        ],
        "constants": {
            "login": {
                "url": "https://apps.gsccca.org/pt61efiling/",
                "username_field": "txtUserID",
                "password_field": "txtPassword"
            },
            "seller_section": {
                "type": "individual",
                "address": {
                    "line1": "c/o 155 CENTENNIAL OLYMPIC PARK DR. NW", 
                    "city": "ATLANTA",
                    "state": "GA",
                    "zip": "30313"
                }
            },
            "buyer_section": {
                "type": "business",
                "name": "CENTENNIAL PARK DEVELOPMENT LLC",
                "address": "same_as_seller",
                "clear_additional_buyers": True  # Ensure auto-fill is cleared
            },
            "property_section": {
                "county": "Fulton",
                "county_value": "60",
                "map_parcel": "14-0078-0007-096-9"
            },
            "tax_computation": {
                "exempt_code": "First Transferee Foreclosure"
            },
            "file_naming": {
                "pattern": "{contract_num}_{last_name}_PT61.pdf",  # Different order
                "fields": ["Contract Num", "Last 1"]
            }
        }
    }
}

def get_version_config(version_display_name):
    """Get configuration for a version by display name"""
    for key, config in PT61_VERSIONS.items():
        if config["display_name"] == version_display_name:
            return key, config
    raise ValueError(f"Unknown version: {version_display_name}")

def get_version_key(version_display_name):
    """Get the version key from display name"""
    version_key, _ = get_version_config(version_display_name)
    return version_key

def get_required_columns(version_display_name):
    """Get required Excel columns for a version"""
    _, config = get_version_config(version_display_name)
    return config["required_columns"]

def get_constants(version_display_name):
    """Get constants for a version"""
    _, config = get_version_config(version_display_name)
    return config["constants"]

# Single source of truth functions for UI
def get_all_version_display_names():
    """Get all version display names for UI dropdowns"""
    return [config["display_name"] for config in PT61_VERSIONS.values()]

def get_version_descriptions():
    """Get all version descriptions"""
    return {config["display_name"]: config["description"] for config in PT61_VERSIONS.values()}

def get_version_by_key(version_key):
    """Get version config by key"""
    if version_key in PT61_VERSIONS:
        return PT61_VERSIONS[version_key]
    raise ValueError(f"Unknown version key: {version_key}")

def is_valid_version_name(version_display_name):
    """Check if a version display name is valid"""
    try:
        get_version_config(version_display_name)
        return True
    except ValueError:
        return False