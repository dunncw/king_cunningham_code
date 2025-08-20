"""Horry HOA-FCL workflow implementation with Condo Lien Satisfaction."""

import os
import pandas as pd
import re
from typing import Dict, Any, List
from datetime import datetime
from .base import BaseWorkflow


class HorryHOAFCLWorkflow(BaseWorkflow):
    """Horry County HOA Foreclosure workflow with Condo Lien Satisfaction documents."""
    
    name = "HORRY_HOA_FCL"
    display_name = "HORRY_HOA_FCL"
    docs_url = "https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/HORRY-HOA-FCL/HORRY-HOA-FCL-workflow-spec.md"
    county = "SCCP49"
    
    required_columns = [
        "KC File No.", "Account", "Last Name #1", "First Name #1",
        "Deed Book", "Deed Page", "Recorded Date", "Mortgage Book", "Mortgage Page",
        "Suite", "Consideration", "Execution Date", "GRANTOR", "GRANTEE", "LEGAL DESCRIPTION"
    ]
    
    field_mappings = {
        "KC File No.": "kc_file_no",
        "Account": "account",
        "Last Name #1": "last_1",
        "First Name #1": "first_1",
        "Last Name #2": "last_2",
        "First Name #2": "first_2",
        "&": "has_second_indicator",
        "Deed Book": "deed_book",
        "Deed Page": "deed_page",
        "Recorded Date": "recorded_date",
        "Mortgage Book": "condo_lien_book",  # Reused for condo lien
        "Mortgage Page": "condo_lien_page",  # Reused for condo lien
        "Suite": "suite",
        "Consideration": "consideration",
        "Execution Date": "execution_date",
        "GRANTOR": "grantor_entity",  # Separate from grantee
        "GRANTEE": "grantee_entity",  # Separate from grantor
        "LEGAL DESCRIPTION": "legal_description"
    }
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed with HOA-FCL specific validation."""
        # Check required fields except for name fields (we'll handle those specially)
        name_fields = {"Last Name #1", "First Name #1"}
        for col in self.required_columns:
            if col not in name_fields:
                if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                    return False
        
        # Special validation for names (same logic as other Horry workflows)
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
        
        # STRICT consideration validation for HOA-FCL (must be > 0)
        consideration = str(row.get("Consideration", "")).strip()
        cleaned_consideration = self._clean_consideration(consideration)
        if cleaned_consideration <= 0:
            return False
        
        return True
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with HOA-FCL specific logic."""
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
        data["cls_id"] = f"D-{data['account']}-CLS"  # CLS for Condo Lien Satisfaction
        
        # Combined legal description with suite
        legal_desc = clean_value(data.get("legal_description", ""))
        suite = clean_value(data.get("suite", ""))
        if suite:
            data["combined_legal"] = f"{legal_desc} {suite}"
        else:
            data["combined_legal"] = legal_desc
        
        # Clean consideration - STRICT for HOA-FCL (must be > 0)
        data["consideration"] = self._clean_consideration(data.get("consideration", "0"))
        
        # Format execution date
        data["execution_date"] = self._format_date_for_api(clean_value(data.get("execution_date", "")))
        
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
    
    def _format_date_for_api(self, date_str: str) -> str:
        """Format date string for API (MM/DD/YYYY format)."""
        if not date_str:
            return datetime.now().strftime('%m/%d/%Y')
        
        try:
            # Input might be MM/DD/YYYY, try to parse and return same format
            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
            return date_obj.strftime('%m/%d/%Y')
        except ValueError:
            try:
                # Try YYYY-MM-DD format
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%m/%d/%Y')
            except ValueError:
                # Return current date as fallback
                return datetime.now().strftime('%m/%d/%Y')
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract and merge PDFs for Horry HOA-FCL."""
        index = row_data.get("_index", 0)
        
        # Extract deed (2 pages)
        deed = self.extract_fixed_pages(pdf_paths["deed_stack"], 2, index)
        
        # Extract and merge affidavit if present
        if pdf_paths.get("affidavit_stack") and os.path.exists(pdf_paths["affidavit_stack"]):
            affidavit = self.extract_fixed_pages(pdf_paths["affidavit_stack"], 2, index)
            deed = self.merge_pdfs(deed, affidavit)
        
        # Extract condo lien satisfaction (1 page)
        condo_lien = self.extract_fixed_pages(pdf_paths["condo_lien_stack"], 1, index)
        
        return {"deed": deed, "condo_lien": condo_lien}
    
    def build_payload(self, package_data: Dict[str, Any], pdfs: Dict[str, bytes]) -> Dict[str, Any]:
        """Build Horry HOA-FCL specific payload with 2 documents."""
        package = super().build_payload(package_data, pdfs)
        
        # Build deed document
        deed_doc = {
            "submitterDocumentID": package_data["deed_id"],
            "name": package_data["doc_name_prefix"] + " TD",
            "kindOfInstrument": ["Deed - Timeshare"],
            "indexingData": {
                "executionDate": package_data["execution_date"],
                "consideration": package_data["consideration"],
                "grantors": self._build_deed_grantors(package_data),
                "grantees": [{
                    "nameUnparsed": package_data["grantee_entity"],
                    "type": "Organization"
                }],
                "legalDescriptions": [{
                    "description": package_data["combined_legal"],
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
        
        # Build condo lien satisfaction document
        cls_doc = {
            "submitterDocumentID": package_data["cls_id"],
            "name": package_data["doc_name_prefix"] + " CLS",
            "kindOfInstrument": ["Condo Lien Satisfaction"],
            "indexingData": {
                "executionDate": package_data["execution_date"],
                "grantors": self._build_individual_grantors(package_data),  # Individual owners ONLY
                "grantees": [{
                    "nameUnparsed": package_data["grantee_entity"],
                    "type": "Organization"
                }],
                "legalDescriptions": [{
                    "description": package_data["combined_legal"],
                    "parcelId": ""
                }],
                "referenceInformation": [{
                    "documentType": "Condo Lien Satisfaction",
                    "book": package_data["condo_lien_book"],
                    "page": int(package_data["condo_lien_page"]) if package_data["condo_lien_page"].isdigit() else 0
                }]
            },
            "fileBytes": [self.to_base64(pdfs["condo_lien"])]
        }
        
        package["documents"] = [deed_doc, cls_doc]
        return package
    
    def _build_deed_grantors(self, data: Dict[str, Any]) -> list:
        """Build grantors for deed (includes KING CUNNINGHAM and GRANTOR entity)."""
        grantors = [
            {"nameUnparsed": "KING CUNNINGHAM LLC TR", "type": "Organization"},
            {"nameUnparsed": data["grantor_entity"], "type": "Organization"}
        ]
        grantors.extend(self._build_individual_grantors(data))
        return grantors
    
    def _build_individual_grantors(self, data: Dict[str, Any]) -> list:
        """Build individual grantors only (for condo lien satisfaction)."""
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