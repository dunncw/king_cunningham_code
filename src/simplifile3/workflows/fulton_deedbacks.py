"""Fulton Deedbacks workflow implementation with directory-based document discovery."""

import os
import re
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from .base import BaseWorkflow


class FultonDeedbacksWorkflow(BaseWorkflow):
    """Fulton County Deedbacks workflow with directory-based document discovery."""
    
    name = "FULTON_DEEDBACKS"
    display_name = "FULTON_DEEDBACKS"
    docs_url = "https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/FULTON-DEEDBACK/FULTON-DEEDBACKS_workflow_spec.md"
    county = "GAC3TH"
    
    required_columns = [
        "Contract Num", "First 1", "Last 1", "Sales Price", "DB To"
    ]
    
    field_mappings = {
        "Contract Num": "contract_number",
        "First 1": "grantor_1_first_name",
        "Middle 1": "grantor_1_middle_name",
        "Last 1": "grantor_1_last_name",
        "First 2": "grantor_2_first_name",
        "Middle 2": "grantor_2_middle_name",
        "Last 2": "grantor_2_last_name",
        "Sales Price": "consideration_amount",
        "DB To": "grantee_name"
    }
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.document_catalog = {}  # Cache of discovered documents
    
    def normalize_contract_number(self, contract_num: str) -> str:
        """Normalize contract number by removing leading zeros."""
        if not contract_num:
            return ""
        return str(int(contract_num)) if contract_num.isdigit() else contract_num.strip()
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed with Fulton Deedbacks validation."""
        # Check all required fields
        for col in self.required_columns:
            if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                return False
        
        # Validate sales price format
        sales_price = str(row.get("Sales Price", "")).strip()
        cleaned_price = self._clean_consideration(sales_price)
        if cleaned_price <= 0:
            return False
        
        return True
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform row with Fulton Deedbacks logic."""
        # Start with base transformation
        data = super().transform_row(row)
        
        # Clean up potential NaN values
        def clean_value(value):
            if pd.isna(value):
                return ""
            return str(value).strip()
        
        # Clean all fields and uppercase names
        data["grantor_1_first_name"] = clean_value(data.get("grantor_1_first_name", "")).upper()
        data["grantor_1_middle_name"] = clean_value(data.get("grantor_1_middle_name", "")).upper()
        data["grantor_1_last_name"] = clean_value(data.get("grantor_1_last_name", "")).upper()
        data["grantor_2_first_name"] = clean_value(data.get("grantor_2_first_name", "")).upper()
        data["grantor_2_middle_name"] = clean_value(data.get("grantor_2_middle_name", "")).upper()
        data["grantor_2_last_name"] = clean_value(data.get("grantor_2_last_name", "")).upper()
        
        # Normalize contract number
        raw_contract_num = clean_value(data.get("contract_number", ""))
        data["contract_number"] = self.normalize_contract_number(raw_contract_num)
        
        # Check for second owner
        data["has_second_owner"] = bool(data["grantor_2_first_name"])
        
        # Package naming: {Last 1} DB {Contract Num}
        data["package_name"] = f"{data['grantor_1_last_name']} DB {data['contract_number']}"
        data["package_id"] = f"P-{data['contract_number']}"
        
        # Document IDs
        data["deed_document_id"] = f"D-{data['contract_number']}-DEED"
        data["deed_document_name"] = f"{data['grantor_1_last_name']} DB {data['contract_number']} DEED"
        data["satisfaction_document_id"] = f"D-{data['contract_number']}-SAT"
        data["satisfaction_document_name"] = f"{data['grantor_1_last_name']} DB {data['contract_number']} SAT"
        
        # Clean consideration
        data["consideration_amount"] = self._clean_consideration(data.get("consideration_amount", "0"))
        
        # Fixed Fulton values
        data["parcel_id"] = "14-0078-0007-096-9"
        data["tax_exempt"] = False
        
        # Grantee from DB To column
        data["deed_grantee_name"] = clean_value(data.get("grantee_name", "")).upper()
        data["deed_grantee_type"] = "Organization"
        data["sat_grantee_name"] = data["deed_grantee_name"]
        data["sat_grantee_type"] = "Organization"
        
        return data
    
    def _clean_consideration(self, consideration_str: str) -> float:
        """Clean consideration amount by removing $ and commas."""
        if not consideration_str:
            return 0.0
        
        # Remove $ and commas, keep only digits and decimal point
        cleaned = re.sub(r'[\$,]', '', str(consideration_str))
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def scan_documents_directory(self, documents_directory: str) -> Dict[str, Dict[str, str]]:
        """
        Scan documents directory and catalog all PDF files by normalized contract number.
        
        Returns:
            Dictionary mapping normalized_contract_num -> {deed_path, pt61_path, sat_path}
        """
        self.document_catalog = {}
        
        if not os.path.exists(documents_directory) or not os.path.isdir(documents_directory):
            raise Exception(f"Documents directory does not exist: {documents_directory}")
        
        # Get all PDF files in directory
        pdf_files = [f for f in os.listdir(documents_directory) if f.lower().endswith('.pdf')]
        
        if self.logger:
            self.logger.info(f"Found {len(pdf_files)} PDF files in directory")
        
        # Parse each PDF filename and catalog by normalized contract number
        for pdf_file in pdf_files:
            file_path = os.path.join(documents_directory, pdf_file)
            parsed = self._parse_filename_by_contract(pdf_file)
            
            if parsed:
                raw_contract_num, doc_type = parsed
                normalized_contract_num = self.normalize_contract_number(raw_contract_num)
                
                if normalized_contract_num not in self.document_catalog:
                    self.document_catalog[normalized_contract_num] = {}
                
                self.document_catalog[normalized_contract_num][doc_type] = file_path
                if self.logger:
                    self.logger.info(f"Cataloged: {normalized_contract_num} -> {doc_type} ({pdf_file})")
            else:
                if self.logger:
                    self.logger.info(f"Could not parse filename: {pdf_file}")
        
        if self.logger:
            self.logger.info(f"Cataloged {len(self.document_catalog)} document sets")
        return self.document_catalog
    
    def _parse_filename_by_contract(self, filename: str) -> Optional[Tuple[str, str]]:
        """
        Parse filename by contract number patterns.
        
        Expected patterns:
        - *{Contract Num} DB.pdf -> (contract_num, 'deed_path')
        - *{Contract Num} DB PT61.pdf -> (contract_num, 'pt61_path')
        - *{Contract Num} DB SAT.pdf -> (contract_num, 'sat_path')
        """
        # Remove .pdf extension
        basename = filename[:-4] if filename.lower().endswith('.pdf') else filename
        
        # Try SAT pattern: ends with "{CONTRACT} DB SAT"
        sat_pattern = r'(.+)\s+DB\s+SAT$'
        match = re.search(sat_pattern, basename, re.IGNORECASE)
        if match:
            contract_part = match.group(1).strip()
            contract_num = self._extract_contract_number(contract_part)
            if contract_num:
                return (contract_num, 'sat_path')
        
        # Try PT61 pattern: ends with "{CONTRACT} DB PT61"
        pt61_pattern = r'(.+)\s+DB\s+PT61$'
        match = re.search(pt61_pattern, basename, re.IGNORECASE)
        if match:
            contract_part = match.group(1).strip()
            contract_num = self._extract_contract_number(contract_part)
            if contract_num:
                return (contract_num, 'pt61_path')
        
        # Try basic deed pattern: ends with "{CONTRACT} DB"
        deed_pattern = r'(.+)\s+DB$'
        match = re.search(deed_pattern, basename, re.IGNORECASE)
        if match:
            contract_part = match.group(1).strip()
            contract_num = self._extract_contract_number(contract_part)
            if contract_num:
                return (contract_num, 'deed_path')
        
        return None
    
    def _extract_contract_number(self, contract_part: str) -> Optional[str]:
        """
        Extract contract number from the end of the contract part.
        Examples:
        - "DEMAYO DB 392400442" -> "392400442"
        - "KEMMERER DB 762401133" -> "762401133"
        """
        # Split by spaces and take the last part
        parts = contract_part.split()
        if parts:
            last_part = parts[-1]
            # Check if it looks like a contract number (digits)
            if last_part.isdigit():
                return last_part
        
        return None
    
    def get_documents_for_package(self, contract_num: str) -> Dict[str, str]:
        """
        Get document paths for a specific contract number.
        
        Returns:
            Dictionary with 'deed_path', 'pt61_path', and optionally 'sat_path'
        """
        normalized_contract = self.normalize_contract_number(contract_num)
        
        if normalized_contract not in self.document_catalog:
            raise Exception(f"No documents found for contract {contract_num} (normalized: {normalized_contract})")
        
        docs = self.document_catalog[normalized_contract]
        
        # Check for required documents
        if 'deed_path' not in docs:
            raise Exception(f"Missing deed document for contract {contract_num}")
        
        if 'pt61_path' not in docs:
            raise Exception(f"Missing PT-61 document for contract {contract_num}")
        
        result = {
            'deed_path': docs['deed_path'],
            'pt61_path': docs['pt61_path']
        }
        
        # Add SAT if present
        if 'sat_path' in docs:
            result['sat_path'] = docs['sat_path']
        
        return result
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract PDFs from directory-based files."""
        # Get documents directory from pdf_paths
        documents_dir = pdf_paths.get("documents_dir", "")
        if not documents_dir:
            raise Exception("Documents directory not provided in pdf_paths")
        
        # Scan directory if not already done
        if not self.document_catalog:
            self.scan_documents_directory(documents_dir)
        
        contract_num = row_data["contract_number"]
        
        # Get document paths for this contract
        document_paths = self.get_documents_for_package(contract_num)
        
        pdfs = {}
        
        # Load deed document
        deed_path = document_paths['deed_path']
        with open(deed_path, 'rb') as f:
            pdfs["deed"] = f.read()
        
        # Load PT-61 document
        pt61_path = document_paths['pt61_path']
        with open(pt61_path, 'rb') as f:
            pdfs["pt61"] = f.read()
        
        # Load SAT document if present
        if 'sat_path' in document_paths:
            sat_path = document_paths['sat_path']
            with open(sat_path, 'rb') as f:
                pdfs["sat"] = f.read()
        
        return pdfs
    
    def build_payload(self, package_data: Dict[str, Any], pdfs: Dict[str, bytes]) -> Dict[str, Any]:
        """Build Fulton Deedbacks specific payload."""
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
        
        documents = [deed_doc]
        
        # Add satisfaction document if present
        if "sat" in pdfs:
            sat_doc = {
                "submitterDocumentID": package_data["satisfaction_document_id"],
                "name": package_data["satisfaction_document_name"],
                "kindOfInstrument": ["SATISFACTION"],
                "indexingData": {
                    "grantors": [{
                        "nameUnparsed": package_data["sat_grantee_name"],
                        "type": package_data["sat_grantee_type"]
                    }],
                    "grantees": self._build_grantors(package_data)
                },
                "fileBytes": [self.to_base64(pdfs["sat"])]
            }
            documents.append(sat_doc)
        
        package["documents"] = documents
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
            
            # Add last name (use Last 2 if present, otherwise use Last 1)
            if data.get("grantor_2_last_name"):
                grantor_2["lastName"] = data["grantor_2_last_name"]
            else:
                grantor_2["lastName"] = data["grantor_1_last_name"]  # Default to same last name
            
            grantors.append(grantor_2)
        
        return grantors