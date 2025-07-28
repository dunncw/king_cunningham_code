import re
from typing import Dict, List, Any
import pandas as pd

from ...base.workflow import BaseWorkflow


class FultonFCLWorkflow(BaseWorkflow):
    """Fulton County Foreclosure (FCL) workflow"""

    def get_required_excel_columns(self) -> List[str]:
        """Required columns for FCL workflow"""
        return [
            "Contract Num",
            "First 1",
            "Last 1",
            "Sales Price"
        ]

    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel columns to internal field names"""
        return {
            "Contract Num": "contract_number",
            "First 1": "grantor_1_first_name",
            "Middle 1": "grantor_1_middle_name",
            "Last 1": "grantor_1_last_name",
            "&": "has_second_owner",
            "First 2": "grantor_2_first_name",
            "Middle 2": "grantor_2_middle_name",
            "Last 2": "grantor_2_last_name",
            "Sales Price": "consideration_amount"
        }

    def get_document_types(self) -> List[str]:
        """FCL creates both DEED and SATISFACTION documents"""
        return [self.county.DEED_DOCUMENT_TYPE, self.county.MORTGAGE_DOCUMENT_TYPE]

    def transform_row_data(self, excel_row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Excel row data for FCL workflow"""
        # Map Excel columns to internal fields
        mapping = self.get_excel_mapping()
        transformed = {}

        for excel_col, internal_field in mapping.items():
            value = excel_row.get(excel_col, "")
            if pd.isna(value):
                value = ""
            transformed[internal_field] = str(value).strip().upper()

        # Apply FCL-specific business rules
        contract_num = transformed["contract_number"]
        last_1 = transformed["grantor_1_last_name"]

        # Package naming convention
        transformed["package_name"] = f"{contract_num} {last_1} FCL DEED"
        transformed["package_id"] = f"P-{contract_num}"

        # Clean consideration amount
        consideration = transformed["consideration_amount"]
        cleaned_consideration = self._clean_consideration(consideration)
        transformed["consideration_amount"] = cleaned_consideration

        # Process second owner logic
        has_second = transformed["has_second_owner"] == "&"
        transformed["has_second_owner"] = has_second

        # Clean up optional middle names
        if not transformed["grantor_1_middle_name"]:
            transformed["grantor_1_middle_name"] = ""
        if not transformed["grantor_2_middle_name"]:
            transformed["grantor_2_middle_name"] = ""

        # Apply county fixed values
        transformed["parcel_id"] = self.county.FIXED_PARCEL_ID
        transformed["tax_exempt"] = self.county.FIXED_TAX_EXEMPT
        transformed["deed_grantee_name"] = self.county.FIXED_DEED_GRANTEE
        transformed["deed_grantee_type"] = "Organization"
        transformed["sat_grantee_name"] = self.county.FIXED_SAT_GRANTEE
        transformed["sat_grantee_type"] = "Organization"

        # Document naming
        transformed["deed_document_id"] = f"D-{contract_num}-DEED"
        transformed["deed_document_name"] = f"{last_1} {contract_num} DEED"
        transformed["satisfaction_document_id"] = f"D-{contract_num}-SAT"
        transformed["satisfaction_document_name"] = f"{last_1} {contract_num} SAT"

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

    def validate_excel_data(self, df: pd.DataFrame) -> List[str]:
        """Additional FCL-specific validation"""
        errors = super().validate_excel_data(df)

        # Validate consideration amounts
        if "Sales Price" in df.columns:
            for idx, value in df["Sales Price"].items():
                if pd.notna(value):
                    cleaned = self._clean_consideration(str(value))
                    if cleaned <= 0:
                        errors.append(f"Invalid sales price at row {idx + 2}: must be greater than 0")

        # Check for proper name formatting
        name_columns = ["First 1", "Last 1", "First 2", "Last 2"]
        for column in name_columns:
            if column in df.columns:
                for idx, value in df[column].items():
                    if pd.notna(value) and str(value).strip():
                        if str(value) != str(value).upper():
                            errors.append(f"Name in column '{column}' at row {idx + 2} should be in ALL CAPS: '{value}'")

        # Validate second owner logic
        if "&" in df.columns and "First 2" in df.columns:
            for idx, row in df.iterrows():
                has_ampersand = str(row.get("&", "")).strip() == "&"
                first_2 = str(row.get("First 2", "")).strip()

                if has_ampersand and not first_2:
                    errors.append(f"Row {idx + 2}: Has '&' indicator but missing 'First 2' name")
                elif first_2 and not has_ampersand:
                    errors.append(f"Row {idx + 2}: Has 'First 2' name but missing '&' indicator")

        return errors

    def is_row_valid(self, excel_row: Dict[str, Any]) -> tuple[bool, str]:
        """Check if a row has all required data for FCL processing"""
        # Check core required fields
        required_fields = {
            "Contract Num": excel_row.get("Contract Num"),
            "First 1": excel_row.get("First 1"),
            "Last 1": excel_row.get("Last 1"),
            "Sales Price": excel_row.get("Sales Price")
        }

        # Check for empty required fields
        for field_name, value in required_fields.items():
            if pd.isna(value) or str(value).strip() == "":
                return False, f"Missing required field: {field_name}"

        # If & indicates second owner, check First 2
        ampersand_value = excel_row.get("&", "")
        if not pd.isna(ampersand_value) and str(ampersand_value).strip() == "&":
            first_2 = excel_row.get("First 2")
            if pd.isna(first_2) or str(first_2).strip() == "":
                return False, "Has '&' indicator but missing 'First 2' name"

        # Validate sales price format
        sales_price = str(excel_row.get("Sales Price", "")).strip()
        cleaned_price = self._clean_consideration(sales_price)
        if cleaned_price <= 0:
            return False, f"Invalid sales price: {sales_price}"

        return True, ""