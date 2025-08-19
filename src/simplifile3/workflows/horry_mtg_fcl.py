"""Horry MTG-FCL workflow implementation."""

import os
from typing import Dict, Any
from .base import BaseWorkflow


class HorryMTGFCLWorkflow(BaseWorkflow):
    """Horry County Timeshare Deed workflow."""
    
    name = "HORRY_MTG_FCL"
    display_name = "Horry Timeshare Deed (MTG-FCL)"
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
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with Horry-specific logic."""
        # Start with base transformation
        data = super().transform_row(row)
        
        # Uppercase names
        for field in ["first_1", "last_1", "first_2", "last_2"]:
            if field in data:
                data[field] = data[field].upper()
        
        # Handle second owner
        data["has_second"] = (row.get("&") == "&")
        
        # Handle ORG: prefix
        if data.get("last_1", "").startswith("ORG:"):
            data["is_org"] = True
            data["package_name"] = f"{data['account']} {data['first_1']} TD {data['kc_file_no']}"
        else:
            data["is_org"] = False
            data["package_name"] = f"{data['account']} {data['last_1']} TD {data['kc_file_no']}"
        
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
            grantors.append({
                "nameUnparsed": data["first_1"],
                "type": "Organization"
            })
        else:
            grantors.append({
                "firstName": data["first_1"],
                "lastName": data["last_1"],
                "type": "Individual"
            })
        
        if data.get("has_second") and data.get("first_2"):
            grantors.append({
                "firstName": data["first_2"],
                "lastName": data.get("last_2", ""),
                "type": "Individual"
            })
        
        return grantors