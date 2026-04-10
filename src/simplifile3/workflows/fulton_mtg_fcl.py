"""Fulton FCL workflow implementation with PT-61 helper documents."""

import re
import pandas as pd
from typing import Dict, Any, List
from .base import BaseWorkflow


class FultonMTGFCLWorkflow(BaseWorkflow):
    """Fulton County Foreclosure workflow with PT-61 helper documents."""
    
    name = "FULTON_MTG_FCL"
    display_name = "FULTON_MTG_FCL"
    docs_url = "https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/FULTON-MTG-FCL/FULTON-MTG-FCL_workflow_spec.md"
    county = "GAC3TH"
    
    required_columns = [
        "Contract Num", "First 1", "Last 1", "Sales Price"
    ]
    
    field_mappings = {
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
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed with Fulton FCL validation."""
        # Check core required fields
        for col in self.required_columns:
            if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                return False
        
        # If & indicates second owner, check First 2
        ampersand_value = row.get("&", "")
        if not pd.isna(ampersand_value) and str(ampersand_value).strip() == "&":
            first_2 = row.get("First 2")
            if pd.isna(first_2) or str(first_2).strip() == "":
                return False
        
        # Validate sales price format
        sales_price = str(row.get("Sales Price", "")).strip()
        cleaned_price = self._clean_consideration(sales_price)
        if cleaned_price <= 0:
            return False
        
        return True
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with Fulton FCL specific logic."""
        # Start with base transformation
        data = super().transform_row(row)
        
        # Clean up potential NaN values
        def clean_value(value):
            if pd.isna(value):
                return ""
            return str(value).strip().upper()
        
        # Clean and uppercase all fields
        for key in data.keys():
            if key in self.field_mappings.values():
                data[key] = clean_value(data.get(key, ""))
        
        # Special handling for consideration - don't uppercase
        consideration = row.get("Sales Price", "")
        data["consideration_amount"] = self._clean_consideration(consideration)
        
        # Process second owner logic
        has_second = data.get("has_second_owner") == "&"
        data["has_second_owner"] = has_second
        
        # Package naming: {Contract Num} {Last 1} FCL DEED
        contract_num = data["contract_number"]
        last_1 = data["grantor_1_last_name"]
        data["package_name"] = f"{contract_num} {last_1} FCL DEED"
        data["package_id"] = f"P-{contract_num}"
        
        # Document IDs and names
        data["deed_document_id"] = f"D-{contract_num}-DEED"
        data["deed_document_name"] = f"{last_1} {contract_num} DEED"
        data["satisfaction_document_id"] = f"D-{contract_num}-SAT"
        data["satisfaction_document_name"] = f"{last_1} {contract_num} SAT"
        
        # Fixed Fulton values
        data["parcel_id"] = "14-0078-0007-096-9"
        data["tax_exempt"] = True
        data["deed_grantee_name"] = "CENTENNIAL PARK DEVELOPMENT LLC"
        data["deed_grantee_type"] = "Organization"
        data["sat_grantee_name"] = "CENTENNIAL PARK DEVELOPMENT LLC"
        data["sat_grantee_type"] = "Organization"
        
        return data
    
    def _clean_consideration(self, consideration_str: str) -> float:
        """Clean consideration amount by removing $ and commas, return as float."""
        if not consideration_str:
            return 0.0
        
        # Remove $ and commas, keep only digits and decimal point
        cleaned = re.sub(r'[\$,]', '', str(consideration_str))
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract PDFs for Fulton FCL (deed 3 pages, PT-61 1 page, mortgage 1 page)."""
        index = row_data.get("_index", 0)
        
        # Extract deed document (3 pages)
        deed = self.extract_fixed_pages(pdf_paths["deed_stack"], 3, index)
        
        # Extract PT-61 document (1 page) 
        pt61 = self.extract_fixed_pages(pdf_paths["pt61_stack"], 1, index)
        
        # Extract mortgage satisfaction document (1 page)
        mortgage = self.extract_fixed_pages(pdf_paths["mortgage_stack"], 1, index)
        
        return {"deed": deed, "pt61": pt61, "mortgage": mortgage}
    
    def build_payload(self, package_data: Dict[str, Any], pdfs: Dict[str, bytes]) -> Dict[str, Any]:
        """Build Fulton FCL specific payload with helper documents."""
        package = super().build_payload(package_data, pdfs)
        
        # Build deed document with PT-61 helper
        deed_doc = {
            "submitterDocumentID": package_data["deed_document_id"],
            "name": package_data["deed_document_name"],
            "kindOfInstrument": ["DEED"],
            "indexingData": {
                "consideration": package_data["consideration_amount"],
                "exempt": package_data["tax_exempt"],
                "grantors": self._build_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["deed_grantee_name"],
                    "type": package_data["deed_grantee_type"]
                }],
                "legalDescriptions": [{
                    "description": "",
                    "parcelId": package_data["parcel_id"]
                }]
            },
            "fileBytes": [self.to_base64(pdfs["deed"])],
            "helperDocuments": [{
                "fileBytes": [self.to_base64(pdfs["pt61"])],
                "helperKindOfInstrument": "PT-61",
                "isElectronicallyOriginated": False
            }]
        }
        
        # Build satisfaction document
        sat_doc = {
            "submitterDocumentID": package_data["satisfaction_document_id"],
            "name": package_data["satisfaction_document_name"],
            "kindOfInstrument": ["SATISFACTION"],
            "indexingData": {
                "grantors": self._build_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["sat_grantee_name"],
                    "type": package_data["sat_grantee_type"]
                }]
            },
            "fileBytes": [self.to_base64(pdfs["mortgage"])]
        }
        
        package["documents"] = [deed_doc, sat_doc]
        package["recipient"] = "GAC3TH"  # Fulton County
        
        return package
    
    def _build_grantors(self, data: Dict[str, Any]) -> list:
        """Build grantors (individuals)."""
        grantors = []
        
        # First grantor
        grantor_1 = {
            "firstName": data["grantor_1_first_name"],
            "lastName": data["grantor_1_last_name"],
            "type": "Individual"
        }
        
        # Add middle name if present
        if data.get("grantor_1_middle_name"):
            grantor_1["middleName"] = data["grantor_1_middle_name"]
        
        grantors.append(grantor_1)
        
        # Second grantor if present
        if data.get("has_second_owner") and data.get("grantor_2_first_name"):
            grantor_2 = {
                "firstName": data["grantor_2_first_name"],
                "type": "Individual"
            }
            
            # Add middle name if present
            if data.get("grantor_2_middle_name"):
                grantor_2["middleName"] = data["grantor_2_middle_name"]
            
            # Add last name if present (may be empty for full name in first field)
            if data.get("grantor_2_last_name"):
                grantor_2["lastName"] = data["grantor_2_last_name"]
            else:
                grantor_2["lastName"] = ""  # Handle case where full name is in First 2
            
            grantors.append(grantor_2)
        
        return grantors