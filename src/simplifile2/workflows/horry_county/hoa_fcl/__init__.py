# workflows/horry_county/hoa_fcl/workflow.py - Horry County HOA-FCL workflow implementation
import re
from typing import Dict, List, Any
import pandas as pd

from ...base.workflow import BaseWorkflow


class HorryHOAFCLWorkflow(BaseWorkflow):
    """Horry County HOA Foreclosure (HOA-FCL) workflow"""

    def __init__(self, county_config, workflow_config: Dict[str, Any], logger=None):
        super().__init__(county_config, logger)
        self.workflow_config = workflow_config
        self.document_types = workflow_config.get("document_types", {})

    def get_required_excel_columns(self) -> List[str]:
        """Required columns for Horry HOA-FCL workflow"""
        return [
            "KC File No.",
            "Account", 
            "Last Name #1",
            "First Name #1",
            "Deed Book",
            "Deed Page",
            "Recorded Date",
            "Mortgage Book",  # Reused for condo lien book
            "Mortgage Page",  # Reused for condo lien page
            "Suite",
            "Consideration",
            "Execution Date",
            "GRANTOR",  # Separate from grantee
            "GRANTEE",  # Separate from grantor
            "LEGAL DESCRIPTION"
        ]

    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel columns to internal field names"""
        return {
            "KC File No.": "kc_file_no",
            "Account": "account_number",
            "Last Name #1": "owner_1_last_name",
            "First Name #1": "owner_1_first_name",
            "&": "has_second_owner",
            "Last Name #2": "owner_2_last_name", 
            "First Name #2": "owner_2_first_name",
            "Deed Book": "deed_book",
            "Deed Page": "deed_page",
            "Recorded Date": "recorded_date",
            "Mortgage Book": "condo_lien_book",  # Reused column for condo lien
            "Mortgage Page": "condo_lien_page",  # Reused column for condo lien
            "Suite": "suite_number",
            "Consideration": "consideration_amount",
            "Execution Date": "execution_date",
            "GRANTOR": "grantor_entity",  # Separate grantor
            "GRANTEE": "grantee_entity",  # Separate grantee
            "LEGAL DESCRIPTION": "legal_description"
        }

    def get_document_types(self) -> List[str]:
        """HOA-FCL creates both deed and condo lien satisfaction documents"""
        return [
            self.document_types.get("DEED_DOCUMENT_TYPE", "Deed - Timeshare"),
            self.document_types.get("SATISFACTION_DOCUMENT_TYPE", "Condo Lien Satisfaction")
        ]

    def get_deed_document_type(self) -> str:
        """Get deed document type for this workflow"""
        return self.document_types.get("DEED_DOCUMENT_TYPE", "Deed - Timeshare")

    def get_satisfaction_document_type(self) -> str:
        """Get satisfaction document type for this workflow"""
        return self.document_types.get("SATISFACTION_DOCUMENT_TYPE", "Condo Lien Satisfaction")

    def transform_row_data(self, excel_row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Excel row data for Horry HOA-FCL workflow"""
        # Map Excel columns to internal fields
        mapping = self.get_excel_mapping()
        transformed = {}

        for excel_col, internal_field in mapping.items():
            value = excel_row.get(excel_col, "")
            if pd.isna(value):
                value = ""
            transformed[internal_field] = str(value).strip().upper()

        # Apply HOA-FCL-specific business rules
        account_number = transformed["account_number"]
        kc_file_no = transformed["kc_file_no"]
        last_1 = transformed["owner_1_last_name"]
        first_1 = transformed["owner_1_first_name"]

        # Handle organization naming (ORG: prefix logic)
        if last_1.startswith("ORG:"):
            # Organization case: use first name as the display name
            package_name_prefix = f"{account_number} {first_1} TD {kc_file_no}"
            doc_name_prefix = f"{account_number} {first_1}"
        else:
            # Individual case: use last name
            package_name_prefix = f"{account_number} {last_1} TD {kc_file_no}"
            doc_name_prefix = f"{account_number} {last_1}"

        # Package naming convention
        transformed["package_name"] = package_name_prefix
        transformed["package_id"] = f"{kc_file_no}-{account_number}"

        # Clean consideration amount - STRICT validation for HOA-FCL
        consideration = transformed["consideration_amount"]
        cleaned_consideration = self._clean_consideration(consideration)
        transformed["consideration_amount"] = cleaned_consideration

        # Process second owner logic (& column indicates second owner)
        has_second = transformed["has_second_owner"] == "&"
        transformed["has_second_owner"] = has_second

        # Clean up optional fields
        if not transformed["owner_2_last_name"]:
            transformed["owner_2_last_name"] = ""
        if not transformed["owner_2_first_name"]:
            transformed["owner_2_first_name"] = ""

        # Format date fields (convert to API format)
        transformed["execution_date"] = self._format_date_for_api(transformed["execution_date"])

        # Legal description and parcel ID handling
        legal_desc = transformed["legal_description"] 
        suite = transformed["suite_number"]
        
        # Combine legal description with suite as per spec
        if suite:
            transformed["combined_legal_description"] = f"{legal_desc} {suite}"
        else:
            transformed["combined_legal_description"] = legal_desc
        
        # Suite becomes parcel_id for API
        transformed["parcel_id"] = suite

        # Document naming - Using "CLS" for Condo Lien Satisfaction
        transformed["deed_document_id"] = f"D-{account_number}-TD"
        transformed["deed_document_name"] = f"{doc_name_prefix} TD"
        transformed["satisfaction_document_id"] = f"D-{account_number}-CLS"  # CLS for Condo Lien Satisfaction
        transformed["satisfaction_document_name"] = f"{doc_name_prefix} CLS"

        return transformed

    def _clean_consideration(self, consideration_str: str) -> float:
        """Clean consideration amount by removing $ and commas, return as float"""
        if not consideration_str:
            return 0.0

        # Remove $ and commas, keep only digits and decimal point
        cleaned = re.sub(r'[\$,]', '', str(consideration_str))

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _format_date_for_api(self, date_str: str) -> str:
        """Format date string for API (YYYY-MM-DD format)"""
        if not date_str:
            from datetime import datetime
            return datetime.now().strftime('%Y-%m-%d')
            
        try:
            # Try to parse MM/DD/YYYY format
            from datetime import datetime
            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            # If that fails, try different format or return as-is
            try:
                # Try to parse YYYY-MM-DD format
                from datetime import datetime
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str  # Already in correct format
            except ValueError:
                # Return current date as fallback
                from datetime import datetime
                return datetime.now().strftime('%Y-%m-%d')

    def validate_excel_data(self, df: pd.DataFrame) -> List[str]:
        """Additional HOA-FCL-specific validation"""
        errors = super().validate_excel_data(df)

        # STRICT consideration validation for HOA-FCL workflow
        if "Consideration" in df.columns:
            for idx, value in df["Consideration"].items():
                if pd.notna(value):
                    cleaned = self._clean_consideration(str(value))
                    if cleaned <= 0:
                        errors.append(f"Invalid consideration at row {idx + 2}: must be greater than 0 for HOA-FCL workflow (found: {value})")

        # Check for proper name formatting (ALL CAPS)
        name_columns = ["First Name #1", "Last Name #1", "First Name #2", "Last Name #2"]
        for column in name_columns:
            if column in df.columns:
                for idx, value in df[column].items():
                    if pd.notna(value) and str(value).strip():
                        if str(value) != str(value).upper():
                            errors.append(f"Name in column '{column}' at row {idx + 2} should be in ALL CAPS: '{value}'")

        # Validate second owner logic - ROBUST VERSION
        if "&" in df.columns and "First Name #2" in df.columns and "Last Name #2" in df.columns:
            for idx, row in df.iterrows():
                row_num = idx + 2  # +2 for 1-based indexing and header row
                
                # Get raw values
                ampersand_val = row.get("&")
                first_2_val = row.get("First Name #2") 
                last_2_val = row.get("Last Name #2")
                
                # Check ampersand - must be exactly "&" string
                has_ampersand = False
                if not pd.isna(ampersand_val):
                    amp_str = str(ampersand_val).strip()
                    has_ampersand = (amp_str == "&")
                
                # Check second owner data - both fields must have content
                has_second_owner_data = False
                if not pd.isna(first_2_val) and not pd.isna(last_2_val):
                    first_2_str = str(first_2_val).strip()
                    last_2_str = str(last_2_val).strip()
                    # Both must be non-empty strings
                    has_second_owner_data = bool(first_2_str and last_2_str)

                # Only report errors if there's a mismatch
                if has_ampersand and not has_second_owner_data:
                    errors.append(f"Row {row_num}: Has '&' indicator but missing second owner information")
                elif has_second_owner_data and not has_ampersand:
                    errors.append(f"Row {row_num}: Has second owner information but missing '&' indicator")

        # Validate separate GRANTOR and GRANTEE fields - KEY DIFFERENCE from MTG-FCL
        if "GRANTOR" in df.columns:
            for idx, value in df["GRANTOR"].items():
                if pd.isna(value) or str(value).strip() == "":
                    errors.append(f"Missing 'GRANTOR' value at row {idx + 2}")
                elif str(value) != str(value).upper():
                    errors.append(f"'GRANTOR' at row {idx + 2} should be in ALL CAPS: '{value}'")

        if "GRANTEE" in df.columns:
            for idx, value in df["GRANTEE"].items():
                if pd.isna(value) or str(value).strip() == "":
                    errors.append(f"Missing 'GRANTEE' value at row {idx + 2}")
                elif str(value) != str(value).upper():
                    errors.append(f"'GRANTEE' at row {idx + 2} should be in ALL CAPS: '{value}'")

        # Validate execution date format
        if "Execution Date" in df.columns:
            for idx, value in df["Execution Date"].items():
                if pd.notna(value) and str(value).strip():
                    date_str = str(value).strip()
                    # Handle datetime strings by chopping off time
                    if ' ' in date_str:
                        date_str = date_str.split(' ')[0]
                    
                    try:
                        from datetime import datetime
                        # Try to parse MM/DD/YYYY format first
                        datetime.strptime(date_str, '%m/%d/%Y')
                    except ValueError:
                        try:
                            # Try YYYY-MM-DD format
                            datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            errors.append(f"Invalid execution date format at row {idx + 2}: {value} (expected MM/DD/YYYY or YYYY-MM-DD)")

        return errors

    def is_row_valid(self, excel_row: Dict[str, Any]) -> tuple[bool, str]:
        """Check if a row has all required data for Horry HOA-FCL processing"""
        # Get all required fields from the spec - INCLUDING separate GRANTOR/GRANTEE
        required_fields = {
            "KC File No.": excel_row.get("KC File No."),
            "Account": excel_row.get("Account"),
            "Last Name #1": excel_row.get("Last Name #1"),
            "First Name #1": excel_row.get("First Name #1"),
            "Deed Book": excel_row.get("Deed Book"),
            "Deed Page": excel_row.get("Deed Page"),
            "Recorded Date": excel_row.get("Recorded Date"),
            "Mortgage Book": excel_row.get("Mortgage Book"),  # Condo lien book
            "Mortgage Page": excel_row.get("Mortgage Page"),  # Condo lien page
            "Suite": excel_row.get("Suite"),
            "Consideration": excel_row.get("Consideration"),
            "Execution Date": excel_row.get("Execution Date"),
            "GRANTOR": excel_row.get("GRANTOR"),  # Required and separate
            "GRANTEE": excel_row.get("GRANTEE"),  # Required and separate
            "LEGAL DESCRIPTION": excel_row.get("LEGAL DESCRIPTION")
        }

        # Check for empty required fields
        for field_name, value in required_fields.items():
            if pd.isna(value) or str(value).strip() == "":
                return False, f"Missing required field: {field_name}"

        # If & indicates second owner, check First Name #2 and Last Name #2
        ampersand_value = excel_row.get("&", "")
        if not pd.isna(ampersand_value) and str(ampersand_value).strip() == "&":
            first_2 = excel_row.get("First Name #2")
            last_2 = excel_row.get("Last Name #2")
            if pd.isna(first_2) or str(first_2).strip() == "":
                return False, "Has '&' indicator but missing 'First Name #2'"
            if pd.isna(last_2) or str(last_2).strip() == "":
                return False, "Has '&' indicator but missing 'Last Name #2'"

        # STRICT consideration validation for HOA-FCL workflow
        consideration = str(excel_row.get("Consideration", "")).strip()
        cleaned_consideration = self._clean_consideration(consideration)
        if cleaned_consideration <= 0:
            return False, f"Invalid consideration: {consideration} (must be greater than 0 for HOA-FCL workflow)"

        return True, ""