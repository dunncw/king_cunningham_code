# simplifile2/workflow_definition.py - Workflow definitions
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import pandas as pd
import re
from .county_config import CountyConfig, get_county_config


class WorkflowDefinition(ABC):
    """Abstract base for workflow-specific processing logic"""
    
    def __init__(self, county_config: CountyConfig):
        self.county = county_config
    
    @abstractmethod
    def get_required_excel_columns(self) -> List[str]:
        """Return list of required Excel column names"""
        pass
    
    @abstractmethod
    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel column headers to internal field names"""
        pass
    
    @abstractmethod
    def get_document_types(self) -> List[str]:
        """Return document types this workflow creates"""
        pass
    
    @abstractmethod
    def transform_row_data(self, excel_row: Dict[str, Any]) -> Dict[str, Any]:
        """Apply workflow-specific business logic to a single row"""
        pass
    
    def validate_excel_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate Excel file structure"""
        errors = []
        required_columns = self.get_required_excel_columns()
        
        for column in required_columns:
            if column not in df.columns:
                errors.append(f"Missing required Excel column: '{column}'")
        
        return errors
    
    def validate_excel_data(self, df: pd.DataFrame) -> List[str]:
        """Validate Excel data content"""
        errors = []
        required_columns = self.get_required_excel_columns()
        
        for column in required_columns:
            if column in df.columns:
                # Check for empty required fields
                empty_rows = df[df[column].isna() | (df[column] == "")].index.tolist()
                if empty_rows:
                    row_numbers = [str(row + 2) for row in empty_rows]  # +2 for 1-based and header
                    errors.append(f"Empty values in required column '{column}' at rows: {', '.join(row_numbers)}")
        
        return errors


class FultonFCLWorkflow(WorkflowDefinition):
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
        
        # Package naming convention: {Contract Num} {Last 1} FCL DEED
        transformed["package_name"] = f"{contract_num} {last_1} FCL DEED"
        transformed["package_id"] = f"P-{contract_num}"
        
        # Clean consideration amount (remove $ and commas) and convert to float
        consideration = transformed["consideration_amount"]
        cleaned_consideration = self._clean_consideration(consideration)
        transformed["consideration_amount"] = cleaned_consideration
        
        # Process second owner logic
        has_second = transformed["has_second_owner"] == "&"
        transformed["has_second_owner"] = has_second
        
        # Clean up optional middle names (only include if not empty)
        if not transformed["grantor_1_middle_name"]:
            transformed["grantor_1_middle_name"] = ""
        if not transformed["grantor_2_middle_name"]:
            transformed["grantor_2_middle_name"] = ""
        
        # Apply county fixed values
        transformed["parcel_id"] = self.county.FIXED_PARCEL_ID
        transformed["tax_exempt"] = self.county.FIXED_TAX_EXEMPT
        transformed["deed_grantee_name"] = self.county.FIXED_DEED_GRANTEE
        transformed["deed_grantee_type"] = "Organization"
        
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
            # Convert to float
            return float(cleaned)
        except ValueError:
            # If not a valid number, return 0.0
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
        
        # Check for proper name formatting (should be ALL CAPS)
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
        """Check if a row has all required data and should be processed"""
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


# Workflow registry
WORKFLOW_REGISTRY = {
    ("GAC3TH", "fcl"): FultonFCLWorkflow
}


def get_workflow(county_id: str, workflow_type: str) -> WorkflowDefinition:
    """Get workflow instance for county and workflow type"""
    key = (county_id, workflow_type)
    if key not in WORKFLOW_REGISTRY:
        raise ValueError(f"Workflow '{workflow_type}' not supported for county '{county_id}'")
    
    county_config = get_county_config(county_id)
    workflow_class = WORKFLOW_REGISTRY[key]
    return workflow_class(county_config)


def get_available_workflows(county_id: str) -> Dict[str, str]:
    """Get available workflows for a county"""
    workflows = {}
    for (cid, workflow_type), workflow_class in WORKFLOW_REGISTRY.items():
        if cid == county_id:
            # Create friendly names for workflows
            if workflow_type == "fcl":
                workflows[workflow_type] = "Foreclosure (FCL)"
            else:
                workflows[workflow_type] = workflow_type.upper()
    
    return workflows