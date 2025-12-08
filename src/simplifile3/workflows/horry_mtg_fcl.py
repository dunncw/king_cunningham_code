"""Horry MTG-FCL workflow implementation with organization detection."""

import os
import pandas as pd
from typing import Dict, Any, List
from .base import BaseWorkflow


class HorryMTGFCLWorkflow(BaseWorkflow):
    """Horry County Timeshare Deed workflow with proper organization handling."""
    
    name = "HORRY_MTG_FCL"
    display_name = "HORRY_MTG_FCL"
    docs_url = "https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/HORRY-MTG-FCL/HORRY-MTG-FCL-workflow-spec.md"
    county = "SCCP49"
    
    required_columns = [
        "KC File No.", "Account", "Last Name #1", "First Name #1",
        "Deed Book", "Deed Page", "Mortgage Book", "Mortgage Page",
        "Suite", "Consideration", "Execution Date", 
        "GRANTOR/GRANTEE", "LEGAL DESCRIPTION"
    ]
    
    field_mappings = {
        "KC File No.": "kc_file_no",
        "Account": "account",
        "Last Name #1": "last_1",
        "First Name #1": "first_1",
        "&": "has_second_indicator",
        "Last Name #2": "last_2",
        "First Name #2": "first_2",
        "Deed Book": "deed_book",
        "Deed Page": "deed_page",
        "Mortgage Book": "mortgage_book",
        "Mortgage Page": "mortgage_page",
        "Suite": "suite",
        "Consideration": "consideration",
        "Execution Date": "execution_date",
        "GRANTOR/GRANTEE": "grantor_grantee",
        "LEGAL DESCRIPTION": "legal_description"
    }
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed with improved validation."""
        # Check required fields except for name fields (we'll handle those specially)
        name_fields = {"Last Name #1", "First Name #1"}
        for col in self.required_columns:
            if col not in name_fields:
                if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                    return False
        
        # Special validation for names
        last_1 = str(row.get("Last Name #1", "")).strip()
        first_1 = str(row.get("First Name #1", "")).strip()
        
        # Must have at least first name (for both individuals and organizations)
        if not first_1:
            return False
        
        # Valid cases:
        # 1. Both first and last name (individual)
        # 2. Only first name (organization)
        # Invalid case: Only last name without first name
        if last_1 and not first_1:
            return False
        
        return True
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with Horry-specific logic and organization detection."""
        # Start with base transformation
        data = super().transform_row(row)
        
        # Clean up potential NaN values
        def clean_value(value):
            if pd.isna(value):
                return ""
            return str(value).strip()
        
        # Clean all name fields
        data["first_1"] = clean_value(data.get("first_1", ""))
        data["last_1"] = clean_value(data.get("last_1", ""))
        data["first_2"] = clean_value(data.get("first_2", ""))
        data["last_2"] = clean_value(data.get("last_2", ""))
        
        # Organization detection: if last name is empty and first name has value, it's an org
        data["is_org"] = (not data["last_1"] and data["first_1"])
        
        if data["is_org"]:
            # Organization handling
            data["org_name"] = data["first_1"]
            # Package name uses organization name
            data["package_name"] = f"{data['account']} {data['first_1']} TD {data['kc_file_no']}"
        else:
            # Individual handling - uppercase names
            data["first_1"] = data["first_1"].upper()
            data["last_1"] = data["last_1"].upper()
            data["first_2"] = data["first_2"].upper()
            data["last_2"] = data["last_2"].upper()
            # Package name uses last name
            data["package_name"] = f"{data['account']} {data['last_1']} TD {data['kc_file_no']}"
        
        # Handle second owner (check for "&" symbol)
        data["has_second"] = (data.get("has_second_indicator") == "&" and data["first_2"] and data["last_2"])
        
        # IDs
        data["package_id"] = f"P-{data['kc_file_no']}-{data['account']}"
        data["deed_id"] = f"D-{data['account']}-TD"
        data["sat_id"] = f"D-{data['account']}-SAT"
        
        # Combined legal
        data["legal"] = f"{data['legal_description']} {data['suite']}"
        
        # Clean consideration
        data["consideration"] = self.clean_money(data.get("consideration", "0"))
        
        return data
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract and merge PDFs for Horry."""
        index = row_data.get("_index", 0)
        
        # Extract deed (2 pages)
        deed = self.extract_fixed_pages(pdf_paths["deed_stack"], 2, index)
        
        # Extract and merge affidavit if present
        if pdf_paths.get("affidavit_stack") and os.path.exists(pdf_paths["affidavit_stack"]):
            affidavit = self.extract_fixed_pages(pdf_paths["affidavit_stack"], 2, index)
            deed = self.merge_pdfs(deed, affidavit)
        
        # Extract mortgage satisfaction (1 page)
        mortgage = self.extract_fixed_pages(pdf_paths["mortgage_stack"], 1, index)
        
        return {"deed": deed, "mortgage": mortgage}
    
    def build_payload(self, package_data: Dict[str, Any], pdfs: Dict[str, bytes]) -> Dict[str, Any]:
        """Build Horry-specific payload with 2 documents."""
        package = super().build_payload(package_data, pdfs)
        
        # Build deed document
        deed_doc = {
            "submitterDocumentID": package_data["deed_id"],
            "name": package_data["package_name"].replace("TD", "DEED"),
            "kindOfInstrument": ["Deed - Timeshare"],
            "indexingData": {
                "executionDate": package_data["execution_date"],
                "consideration": package_data["consideration"],
                "grantors": self._build_deed_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["grantor_grantee"],
                    "type": "Organization"
                }],
                "legalDescriptions": [{
                    "description": package_data["legal"],
                    "parcelId": ""
                }],
                "referenceInformation": [{
                    "documentType": "Deed - Timeshare",
                    "book": package_data["deed_book"],
                    "page": int(package_data["deed_page"]) if package_data["deed_page"].isdigit() else 0
                }]
            },
            "fileBytes": [self.to_base64(pdfs["deed"])]
        }
        
        # Build satisfaction document
        sat_doc = {
            "submitterDocumentID": package_data["sat_id"],
            "name": package_data["package_name"].replace("TD", "SAT"),
            "kindOfInstrument": ["Mortgage Satisfaction"],
            "indexingData": {
                "executionDate": package_data["execution_date"],
                "grantors": self._build_individual_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["grantor_grantee"],
                    "type": "Organization"
                }],
                "legalDescriptions": [{
                    "description": package_data["legal"],
                    "parcelId": ""
                }],
                "referenceInformation": [{
                    "documentType": "Mortgage Satisfaction",
                    "book": package_data["mortgage_book"],
                    "page": int(package_data["mortgage_page"]) if package_data["mortgage_page"].isdigit() else 0
                }]
            },
            "fileBytes": [self.to_base64(pdfs["mortgage"])]
        }
        
        package["documents"] = [deed_doc, sat_doc]
        return package
    
    def _build_deed_grantors(self, data: Dict[str, Any]) -> list:
        """Build grantors for deed (includes KING CUNNINGHAM)."""
        grantors = [
            {"nameUnparsed": "KING CUNNINGHAM LLC TR", "type": "Organization"},
            {"nameUnparsed": data["grantor_grantee"], "type": "Organization"}
        ]
        grantors.extend(self._build_individual_grantors(data))
        return grantors
    
    def _build_individual_grantors(self, data: Dict[str, Any]) -> list:
        """Build individual grantors only."""
        grantors = []
        
        if data.get("is_org"):
            # Organization in first name field
            grantors.append({
                "nameUnparsed": data["org_name"],
                "type": "Organization"
            })
        else:
            # Individual
            grantors.append({
                "firstName": data["first_1"],
                "lastName": data["last_1"],
                "type": "Individual"
            })
        
        # Add second grantor if present (always individual for "&" cases)
        if data.get("has_second") and data.get("first_2"):
            grantors.append({
                "firstName": data["first_2"],
                "lastName": data.get("last_2", ""),
                "type": "Individual"
            })
        
        return grantors