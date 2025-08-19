"""Beaufort MTG-FCL workflow implementation with simplified requirements."""

import os
import pandas as pd
from typing import Dict, Any, List
from .base import BaseWorkflow


class BeaufortMTGFCLWorkflow(BaseWorkflow):
    """Beaufort County Hilton Head Timeshare workflow with simplified requirements."""
    
    name = "BEAUFORT_MTG_FCL"
    display_name = "BEAUFORT_MTG_FCL"
    docs_url = "https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/BEAUFORT-MTG-FCL/BEAUFORT-MTG-FCL-workflow-spec.md"
    county = "SCCY4G"
    
    required_columns = [
        "KC File No.", "Account", "Last Name #1", "First Name #1",
        "GRANTOR/GRANTEE", "Consideration"
    ]
    
    field_mappings = {
        "KC File No.": "kc_file_no",
        "Account": "account",
        "Last Name #1": "last_1",
        "First Name #1": "first_1",
        "Last Name #2": "last_2",
        "First Name #2": "first_2",
        "&": "has_second_indicator",
        "GRANTOR/GRANTEE": "grantor_grantee",
        "Consideration": "consideration"
    }
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed with Beaufort-specific validation."""
        # Check required fields except for name fields (we'll handle those specially)
        name_fields = {"Last Name #1", "First Name #1"}
        for col in self.required_columns:
            if col not in name_fields:
                if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                    return False
        
        # Special validation for names (same logic as Horry for organizations)
        last_1 = str(row.get("Last Name #1", "")).strip()
        first_1 = str(row.get("First Name #1", "")).strip()
        
        # Must have at least first name (for both individuals and organizations)
        if not first_1:
            return False
        
        # Valid cases:
        # 1. Both first and last name (individual)
        # 2. Only first name with ORG: prefix in last name (organization)
        # 3. Only first name with empty last name (organization)
        if last_1 and not first_1:
            return False
        
        # If & indicates second owner, check second owner fields
        ampersand_value = row.get("&", "")
        if not pd.isna(ampersand_value) and str(ampersand_value).strip() == "&":
            first_2 = row.get("First Name #2")
            last_2 = row.get("Last Name #2")
            if pd.isna(first_2) or str(first_2).strip() == "":
                return False
            if pd.isna(last_2) or str(last_2).strip() == "":
                return False
        
        return True
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with Beaufort-specific logic."""
        # Start with base transformation
        data = super().transform_row(row)
        
        # Clean up potential NaN values
        def clean_value(value):
            if pd.isna(value):
                return ""
            return str(value).strip()
        
        # Clean all fields
        data["first_1"] = clean_value(data.get("first_1", ""))
        data["last_1"] = clean_value(data.get("last_1", ""))
        data["first_2"] = clean_value(data.get("first_2", ""))
        data["last_2"] = clean_value(data.get("last_2", ""))
        data["has_second_indicator"] = clean_value(data.get("has_second_indicator", ""))
        
        # Organization detection: if last name starts with "ORG:" or is empty with first name present, it's an org
        data["is_org"] = (data["last_1"].startswith("ORG:") or (not data["last_1"] and data["first_1"]))
        
        if data["is_org"]:
            # Organization handling
            if data["last_1"].startswith("ORG:"):
                data["org_name"] = data["first_1"]
            else:
                data["org_name"] = data["first_1"]
            # Package name uses organization name
            data["package_name"] = f"{data['account']} {data['first_1']} TD {data['kc_file_no']}"
            data["doc_name_prefix"] = f"{data['account']} {data['first_1']}"
        else:
            # Individual handling - uppercase names
            data["first_1"] = data["first_1"].upper()
            data["last_1"] = data["last_1"].upper()
            data["first_2"] = data["first_2"].upper()
            data["last_2"] = data["last_2"].upper()
            # Package name uses last name
            data["package_name"] = f"{data['account']} {data['last_1']} TD {data['kc_file_no']}"
            data["doc_name_prefix"] = f"{data['account']} {data['last_1']}"
        
        # Handle second owner (check for "&" symbol)
        data["has_second"] = (data["has_second_indicator"] == "&" and data["first_2"] and data["last_2"])
        
        # IDs
        data["package_id"] = f"P-{data['kc_file_no']}-{data['account']}"
        data["deed_id"] = f"D-{data['account']}-TD"
        data["sat_id"] = f"D-{data['account']}-SAT"
        
        # Clean consideration (keep as string for Beaufort, allow 0.00)
        data["consideration"] = self.clean_money(data.get("consideration", "0"))
        
        return data
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract and merge PDFs for Beaufort (same as Horry structure)."""
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
        """Build Beaufort-specific payload with 2 documents (simplified requirements)."""
        package = super().build_payload(package_data, pdfs)
        
        # Build deed document (simplified for Beaufort - includes consideration but no other complex fields)
        deed_doc = {
            "submitterDocumentID": package_data["deed_id"],
            "name": package_data["doc_name_prefix"] + " TD",
            "kindOfInstrument": ["DEED - HILTON HEAD TIMESHARE"],
            "indexingData": {
                "consideration": float(package_data["consideration"]) if package_data["consideration"] != "0" else 0.0,
                "grantors": self._build_deed_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["grantor_grantee"],
                    "type": "Organization"
                }]
                # Note: Beaufort does NOT require executionDate, legalDescriptions, or referenceInformation
            },
            "fileBytes": [self.to_base64(pdfs["deed"])]
        }
        
        # Build satisfaction document (simplified for Beaufort)
        sat_doc = {
            "submitterDocumentID": package_data["sat_id"],
            "name": package_data["doc_name_prefix"] + " SAT",
            "kindOfInstrument": ["MORT - SATISFACTION"],
            "indexingData": {
                "grantors": self._build_individual_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["grantor_grantee"],
                    "type": "Organization"
                }]
                # Note: Beaufort does NOT require executionDate, legalDescriptions, or referenceInformation
            },
            "fileBytes": [self.to_base64(pdfs["mortgage"])]
        }
        
        package["documents"] = [deed_doc, sat_doc]
        package["recipient"] = "SCCY4G"  # Beaufort County
        
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
            # Organization in first name field (or with ORG: prefix)
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