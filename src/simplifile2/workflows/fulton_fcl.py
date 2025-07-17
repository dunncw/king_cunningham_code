# workflows/fulton_fcl.py - Fulton County FCL workflow implementation
import base64
import io
import re
from typing import Dict, List, Any
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter

from .base import BaseWorkflow, BasePDFProcessor, BasePayloadBuilder
from ..core.county_config import CountyConfig


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


class FultonFCLPDFProcessor(BasePDFProcessor):
    """PDF processor for Fulton FCL workflow"""
    
    def __init__(self, logger=None):
        super().__init__(logger)
        self.pdf_cache = {}
    
    def validate_stacks(self, deed_path: str, pt61_path: str, mortgage_path: str) -> List[str]:
        """Validate all three FCL PDF stacks"""
        from ..core.pdf_stack_processor import PDFStackProcessor
        
        stack_processor = PDFStackProcessor()
        
        stack_configs = [
            {
                "pdf_path": deed_path,
                "pages_per_document": 3,
                "stack_name": "Deed Stack"
            },
            {
                "pdf_path": pt61_path,
                "pages_per_document": 1,
                "stack_name": "PT-61 Stack"
            },
            {
                "pdf_path": mortgage_path,
                "pages_per_document": 1,
                "stack_name": "Mortgage Satisfaction Stack"
            }
        ]
        
        return stack_processor.validate_stacks_alignment(stack_configs)
    
    def get_documents(self, document_index: int, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, str]:
        """Get all documents for a specific FCL package"""
        from ..core.pdf_stack_processor import PDFStackProcessor
        
        try:
            stack_processor = PDFStackProcessor()
            documents = {}
            
            # Extract deed document (3 pages)
            documents["deed_pdf"] = stack_processor.get_document_from_stack(
                deed_path, document_index, 3
            )
            
            # Extract PT-61 document (1 page)
            documents["pt61_pdf"] = stack_processor.get_document_from_stack(
                pt61_path, document_index, 1
            )
            
            # Extract mortgage satisfaction document (1 page)
            documents["mortgage_pdf"] = stack_processor.get_document_from_stack(
                mortgage_path, document_index, 1
            )
            
            return documents
            
        except Exception as e:
            raise Exception(f"Error extracting FCL documents for index {document_index}: {str(e)}")
    
    def get_stack_summary(self, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, Any]:
        """Get summary information about all FCL stacks"""
        from ..core.pdf_stack_processor import PDFStackProcessor
        
        try:
            stack_processor = PDFStackProcessor()
            
            deed_info = stack_processor.get_stack_info(deed_path, 3)
            pt61_info = stack_processor.get_stack_info(pt61_path, 1)
            mortgage_info = stack_processor.get_stack_info(mortgage_path, 1)
            
            # Determine how many complete packages we can create
            max_packages = min(
                deed_info["complete_documents"],
                pt61_info["complete_documents"],
                mortgage_info["complete_documents"]
            )
            
            return {
                "deed_stack": deed_info,
                "pt61_stack": pt61_info,
                "mortgage_stack": mortgage_info,
                "max_packages": max_packages,
                "all_stacks_aligned": (
                    deed_info["complete_documents"] == pt61_info["complete_documents"] == 
                    mortgage_info["complete_documents"]
                )
            }
            
        except Exception as e:
            raise Exception(f"Error getting FCL stack summary: {str(e)}")


class FultonFCLPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Fulton FCL workflow"""
    
    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete FCL package for API submission"""
        # Build the documents array
        documents = []
        
        # Add DEED document with PT-61 helper
        deed_document = self._build_deed_document(workflow_data, pdf_documents)
        documents.append(deed_document)
        
        # Add SATISFACTION document
        satisfaction_document = self._build_satisfaction_document(workflow_data, pdf_documents)
        documents.append(satisfaction_document)
        
        # Build complete package
        package = {
            "documents": documents,
            "recipient": self.county.COUNTY_ID,
            "submitterPackageID": workflow_data["package_id"],
            "name": workflow_data["package_name"],
            "operations": {
                "draftOnErrors": True,
                "submitImmediately": False,
                "verifyPageMargins": True
            }
        }
        
        return package
    
    def _build_deed_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build DEED document with PT-61 helper document"""
        # Build grantors
        grantors = []
        
        # Add first grantor
        grantor_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }
        
        if workflow_data["grantor_1_middle_name"]:
            grantor_1["middleName"] = workflow_data["grantor_1_middle_name"]
        
        grantors.append(grantor_1)
        
        # Add second grantor if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }
            
            if workflow_data["grantor_2_middle_name"]:
                grantor_2["middleName"] = workflow_data["grantor_2_middle_name"]
            
            if workflow_data["grantor_2_last_name"]:
                grantor_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                grantor_2["lastName"] = ""
            
            grantors.append(grantor_2)
        
        # Build grantees
        grantees = [{
            "nameUnparsed": workflow_data["deed_grantee_name"],
            "type": workflow_data["deed_grantee_type"]
        }]
        
        # Build legal descriptions
        legal_descriptions = [{
            "description": "",
            "parcelId": workflow_data["parcel_id"]
        }]
        
        # Build helper documents
        helper_documents = [{
            "fileBytes": [pdf_documents["pt61_pdf"]],
            "helperKindOfInstrument": "PT-61",
            "isElectronicallyOriginated": False
        }]
        
        # Build complete DEED document
        deed_document = {
            "submitterDocumentID": workflow_data["deed_document_id"],
            "name": workflow_data["deed_document_name"],
            "kindOfInstrument": [self.county.DEED_DOCUMENT_TYPE],
            "indexingData": {
                "consideration": float(workflow_data["consideration_amount"]),
                "exempt": workflow_data["tax_exempt"],
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions
            },
            "fileBytes": [pdf_documents["deed_pdf"]],
            "helperDocuments": helper_documents
        }
        
        return deed_document
    
    def _build_satisfaction_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build SATISFACTION document"""
        # Build parties (same individuals for both grantors and grantees)
        parties = []
        
        # Add first party
        party_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }
        
        if workflow_data["grantor_1_middle_name"]:
            party_1["middleName"] = workflow_data["grantor_1_middle_name"]
        
        parties.append(party_1)
        
        # Add second party if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            party_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }
            
            if workflow_data["grantor_2_middle_name"]:
                party_2["middleName"] = workflow_data["grantor_2_middle_name"]
            
            if workflow_data["grantor_2_last_name"]:
                party_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                party_2["lastName"] = ""
            
            parties.append(party_2)
        
        # For satisfaction documents, grantors and grantees are the same
        grantors = parties.copy()
        grantees = parties.copy()
        
        # Build complete SATISFACTION document
        satisfaction_document = {
            "submitterDocumentID": workflow_data["satisfaction_document_id"],
            "name": workflow_data["satisfaction_document_name"],
            "kindOfInstrument": [self.county.MORTGAGE_DOCUMENT_TYPE],
            "indexingData": {
                "grantors": grantors,
                "grantees": grantees
            },
            "fileBytes": [pdf_documents["mortgage_pdf"]]
        }
        
        return satisfaction_document