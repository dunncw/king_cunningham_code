# workflows/horry_mtg_fcl.py - Horry County MTG-FCL workflow implementation
import re
from typing import Dict, List, Any
import pandas as pd

from .base import BaseWorkflow, BasePDFProcessor, BasePayloadBuilder
from ..core.county_config import CountyConfig


class HorryMTGFCLWorkflow(BaseWorkflow):
    """Horry County Timeshare Deed (MTG-FCL) workflow"""

    def get_required_excel_columns(self) -> List[str]:
        """Required columns for Horry MTG-FCL workflow"""
        return [
            "KC File No.",
            "Account", 
            "Last Name #1",
            "First Name #1",
            "Deed Book",
            "Deed Page",
            "Recorded Date",
            "Mortgage Book", 
            "Mortgage Page",
            "Suite",
            "Consideration",
            "Execution Date",
            "GRANTOR/GRANTEE",
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
            "Mortgage Book": "mortgage_book",
            "Mortgage Page": "mortgage_page",
            "Suite": "suite_number",
            "Consideration": "consideration_amount",
            "Execution Date": "execution_date",
            "GRANTOR/GRANTEE": "grantor_grantee_entity",
            "LEGAL DESCRIPTION": "legal_description"
        }

    def get_document_types(self) -> List[str]:
        """Horry MTG-FCL creates both deed and mortgage satisfaction documents"""
        return [self.county.DEED_DOCUMENT_TYPE, self.county.MORTGAGE_DOCUMENT_TYPE]

    def transform_row_data(self, excel_row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Excel row data for Horry MTG-FCL workflow"""
        # Map Excel columns to internal fields
        mapping = self.get_excel_mapping()
        transformed = {}

        for excel_col, internal_field in mapping.items():
            value = excel_row.get(excel_col, "")
            if pd.isna(value):
                value = ""
            transformed[internal_field] = str(value).strip().upper()

        # Apply Horry-specific business rules
        account_number = transformed["account_number"]
        kc_file_no = transformed["kc_file_no"]
        last_1 = transformed["owner_1_last_name"]
        first_1 = transformed["owner_1_first_name"]

        # Handle organization naming (ORG: prefix logic from old code)
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

        # Clean consideration amount
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

        # Document naming
        transformed["deed_document_id"] = f"D-{account_number}-TD"
        transformed["deed_document_name"] = f"{doc_name_prefix} TD"
        transformed["satisfaction_document_id"] = f"D-{account_number}-SAT" 
        transformed["satisfaction_document_name"] = f"{doc_name_prefix} SAT"

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
        """Additional Horry-specific validation"""
        errors = super().validate_excel_data(df)

        # NOTE: For Horry workflow, consideration can be 0.00, so we skip consideration validation

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


        # Validate GRANTOR/GRANTEE field
        if "GRANTOR/GRANTEE" in df.columns:
            for idx, value in df["GRANTOR/GRANTEE"].items():
                if pd.isna(value) or str(value).strip() == "":
                    errors.append(f"Missing 'GRANTOR/GRANTEE' value at row {idx + 2}")
                elif str(value) != str(value).upper():
                    errors.append(f"'GRANTOR/GRANTEE' at row {idx + 2} should be in ALL CAPS: '{value}'")

        # Validate execution date format - FIXED to handle datetime strings
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
        """Check if a row has all required data for Horry MTG-FCL processing"""
        # Get all required fields from the spec
        required_fields = {
            "KC File No.": excel_row.get("KC File No."),
            "Account": excel_row.get("Account"),
            "Last Name #1": excel_row.get("Last Name #1"),
            "First Name #1": excel_row.get("First Name #1"),
            "Deed Book": excel_row.get("Deed Book"),
            "Deed Page": excel_row.get("Deed Page"),
            "Recorded Date": excel_row.get("Recorded Date"),
            "Mortgage Book": excel_row.get("Mortgage Book"),
            "Mortgage Page": excel_row.get("Mortgage Page"),
            "Suite": excel_row.get("Suite"),
            "Consideration": excel_row.get("Consideration"),
            "Execution Date": excel_row.get("Execution Date"),
            "GRANTOR/GRANTEE": excel_row.get("GRANTOR/GRANTEE"),
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

        # NOTE: For Horry workflow, consideration can be 0.00, so we allow it
        # Just validate that it's a valid number format
        consideration = str(excel_row.get("Consideration", "")).strip()
        cleaned_consideration = self._clean_consideration(consideration)
        # Allow 0.00 for Horry workflow - just check it's a valid number
        if cleaned_consideration < 0:
            return False, f"Invalid consideration: {consideration}"

        return True, ""


class HorryMTGFCLPDFProcessor(BasePDFProcessor):
    """PDF processor for Horry MTG-FCL workflow"""

    def __init__(self, logger=None):
        super().__init__(logger)

    def validate_stacks(self, deed_path: str, affidavit_path: str, mortgage_path: str) -> List[str]:
        """Validate all three Horry MTG-FCL PDF stacks"""
        from ..core.pdf_stack_processor import PDFStackProcessor

        stack_processor = PDFStackProcessor()

        stack_configs = [
            {
                "pdf_path": deed_path,
                "pages_per_document": 2,
                "stack_name": "Deed Stack"
            },
            {
                "pdf_path": affidavit_path,
                "pages_per_document": 2,
                "stack_name": "Affidavit Stack"
            },
            {
                "pdf_path": mortgage_path,
                "pages_per_document": 1,
                "stack_name": "Mortgage Satisfaction Stack"
            }
        ]

        return stack_processor.validate_stacks_alignment(stack_configs)

    def get_documents(self, document_index: int, deed_path: str, affidavit_path: str, mortgage_path: str) -> Dict[str, str]:
        """Get all documents for a specific Horry MTG-FCL package with deed+affidavit merging"""
        from ..core.pdf_stack_processor import PDFStackProcessor
        import io
        from PyPDF2 import PdfReader, PdfWriter
        import base64

        try:
            stack_processor = PDFStackProcessor()
            
            # Extract deed document (2 pages)
            deed_pdf_b64 = stack_processor.get_document_from_stack(
                deed_path, document_index, 2
            )
            
            # Extract affidavit document (2 pages) 
            affidavit_pdf_b64 = stack_processor.get_document_from_stack(
                affidavit_path, document_index, 2
            )
            
            # Extract mortgage satisfaction document (1 page)
            mortgage_pdf_b64 = stack_processor.get_document_from_stack(
                mortgage_path, document_index, 1
            )
            
            # Merge deed and affidavit into single 4-page document
            merged_deed_pdf_b64 = self._merge_deed_and_affidavit(deed_pdf_b64, affidavit_pdf_b64)

            return {
                "deed_pdf": merged_deed_pdf_b64,  # 4 pages (2 deed + 2 affidavit)
                "mortgage_pdf": mortgage_pdf_b64  # 1 page
            }

        except Exception as e:
            raise Exception(f"Error extracting Horry MTG-FCL documents for index {document_index}: {str(e)}")

    def _merge_deed_and_affidavit(self, deed_pdf_b64: str, affidavit_pdf_b64: str) -> str:
        """Merge deed and affidavit PDFs into single 4-page document"""
        try:
            import base64
            import io
            from PyPDF2 import PdfReader, PdfWriter
            
            # Decode base64 PDFs
            deed_bytes = base64.b64decode(deed_pdf_b64)
            affidavit_bytes = base64.b64decode(affidavit_pdf_b64)
            
            # Create PDF readers
            deed_reader = PdfReader(io.BytesIO(deed_bytes))
            affidavit_reader = PdfReader(io.BytesIO(affidavit_bytes))
            
            # Create new PDF writer for merged document
            merged_writer = PdfWriter()
            
            # Add all pages from deed document first
            for page in deed_reader.pages:
                merged_writer.add_page(page)
            
            # Add all pages from affidavit document
            for page in affidavit_reader.pages:
                merged_writer.add_page(page)
            
            # Convert merged PDF back to base64
            merged_buffer = io.BytesIO()
            merged_writer.write(merged_buffer)
            merged_bytes = merged_buffer.getvalue()
            merged_buffer.close()
            
            return base64.b64encode(merged_bytes).decode('utf-8')
            
        except Exception as e:
            raise Exception(f"Error merging deed and affidavit PDFs: {str(e)}")

    def get_stack_summary(self, deed_path: str, affidavit_path: str, mortgage_path: str) -> Dict[str, Any]:
        """Get summary information about all Horry MTG-FCL stacks"""
        from ..core.pdf_stack_processor import PDFStackProcessor

        try:
            stack_processor = PDFStackProcessor()

            deed_info = stack_processor.get_stack_info(deed_path, 2)
            affidavit_info = stack_processor.get_stack_info(affidavit_path, 2)
            mortgage_info = stack_processor.get_stack_info(mortgage_path, 1)

            # Determine how many complete packages we can create
            max_packages = min(
                deed_info["complete_documents"],
                affidavit_info["complete_documents"],
                mortgage_info["complete_documents"]
            )

            return {
                "deed_stack": deed_info,
                "affidavit_stack": affidavit_info,
                "mortgage_stack": mortgage_info,
                "max_packages": max_packages,
                "all_stacks_aligned": (
                    deed_info["complete_documents"] == affidavit_info["complete_documents"] ==
                    mortgage_info["complete_documents"]
                ),
                "merged_documents": True  # Horry always merges deed+affidavit
            }

        except Exception as e:
            raise Exception(f"Error getting Horry MTG-FCL stack summary: {str(e)}")


class HorryMTGFCLPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Horry MTG-FCL workflow"""

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete Horry MTG-FCL package for API submission"""
        # Build the documents array
        documents = []

        # Add DEED document (merged deed+affidavit, 4 pages total)
        deed_document = self._build_deed_document(workflow_data, pdf_documents)
        documents.append(deed_document)

        # Add MORTGAGE SATISFACTION document
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
        """Build DEED document according to Horry County requirements"""
        # Build grantors according to Horry spec
        grantors = []

        # 1. KING CUNNINGHAM LLC TR (Organization) - REQUIRED for deed documents
        grantors.append({
            "nameUnparsed": "KING CUNNINGHAM LLC TR",
            "type": "Organization"
        })

        # 2. Entity from GRANTOR/GRANTEE column (Organization)
        grantors.append({
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        })

        # 3. Individual owners from Excel
        # First owner
        grantor_1 = {
            "firstName": workflow_data["owner_1_first_name"],
            "lastName": workflow_data["owner_1_last_name"],
            "type": "Individual"
        }
        
        # Handle organization prefix (ORG:)
        if workflow_data["owner_1_last_name"].startswith("ORG:"):
            # This is actually an organization
            grantors.append({
                "nameUnparsed": workflow_data["owner_1_first_name"],
                "type": "Organization"
            })
        else:
            grantors.append(grantor_1)

        # Second owner (if exists)
        if workflow_data["has_second_owner"] and workflow_data["owner_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["owner_2_first_name"],
                "lastName": workflow_data["owner_2_last_name"],
                "type": "Individual"
            }
            
            # Handle organization prefix for second owner
            if workflow_data["owner_2_last_name"].startswith("ORG:"):
                grantors.append({
                    "nameUnparsed": workflow_data["owner_2_first_name"],
                    "type": "Organization"
                })
            else:
                grantors.append(grantor_2)

        # Build grantees - Entity from GRANTOR/GRANTEE column (Horry County approach)
        grantees = [{
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": workflow_data["combined_legal_description"],
            "parcelId": ""  # Leave parcelId blank as per old code spec
        }]

        # Build reference information for deed
        reference_information = [{
            "documentType": self.county.DEED_DOCUMENT_TYPE,
            "book": workflow_data["deed_book"],
            "page": int(workflow_data["deed_page"]) if workflow_data["deed_page"].isdigit() else 0
        }]

        # Build complete DEED document
        deed_document = {
            "submitterDocumentID": workflow_data["deed_document_id"],
            "name": workflow_data["deed_document_name"],
            "kindOfInstrument": [self.county.DEED_DOCUMENT_TYPE],
            "indexingData": {
                "executionDate": workflow_data["execution_date"],
                "consideration": float(workflow_data["consideration_amount"]),
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions,
                "referenceInformation": reference_information
            },
            "fileBytes": [pdf_documents["deed_pdf"]]
        }

        return deed_document

    def _build_satisfaction_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build MORTGAGE SATISFACTION document according to Horry County requirements"""
        # Build grantors - Individual owners only (NOT KING CUNNINGHAM LLC TR)
        grantors = []

        # First owner
        grantor_1 = {
            "firstName": workflow_data["owner_1_first_name"],
            "lastName": workflow_data["owner_1_last_name"],
            "type": "Individual"
        }
        
        # Handle organization prefix (ORG:)
        if workflow_data["owner_1_last_name"].startswith("ORG:"):
            # This is actually an organization
            grantors.append({
                "nameUnparsed": workflow_data["owner_1_first_name"],
                "type": "Organization"
            })
        else:
            grantors.append(grantor_1)

        # Second owner (if exists)
        if workflow_data["has_second_owner"] and workflow_data["owner_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["owner_2_first_name"],
                "lastName": workflow_data["owner_2_last_name"],
                "type": "Individual"
            }
            
            # Handle organization prefix for second owner
            if workflow_data["owner_2_last_name"].startswith("ORG:"):
                grantors.append({
                    "nameUnparsed": workflow_data["owner_2_first_name"],
                    "type": "Organization"
                })
            else:
                grantors.append(grantor_2)

        # Build grantees - Entity from GRANTOR/GRANTEE column
        grantees = [{
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": workflow_data["combined_legal_description"],
            "parcelId": ""  # Leave parcelId blank as per old code spec
        }]

        # Build reference information for mortgage satisfaction
        reference_information = [{
            "documentType": self.county.MORTGAGE_DOCUMENT_TYPE,
            "book": workflow_data["mortgage_book"],
            "page": int(workflow_data["mortgage_page"]) if workflow_data["mortgage_page"].isdigit() else 0
        }]

        # Build complete SATISFACTION document
        satisfaction_document = {
            "submitterDocumentID": workflow_data["satisfaction_document_id"],
            "name": workflow_data["satisfaction_document_name"],
            "kindOfInstrument": [self.county.MORTGAGE_DOCUMENT_TYPE],
            "indexingData": {
                "executionDate": workflow_data["execution_date"],
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions,
                "referenceInformation": reference_information
            },
            "fileBytes": [pdf_documents["mortgage_pdf"]]
        }

        return satisfaction_document

    def validate_package(self, package: Dict[str, Any]) -> List[str]:
        """Validate package against Horry County requirements"""
        errors = super().validate_package(package)

        # Additional Horry-specific validation
        if "documents" in package:
            for i, document in enumerate(package["documents"]):
                doc_errors = self._validate_horry_document(document, i)
                errors.extend(doc_errors)

        return errors

    def _validate_horry_document(self, document: Dict[str, Any], doc_index: int) -> List[str]:
        """Validate individual Horry document"""
        errors = []
        doc_prefix = f"Document {doc_index + 1}"

        # Check document type
        kind = document.get("kindOfInstrument", [])
        if not kind:
            errors.append(f"{doc_prefix}: Missing kindOfInstrument")
            return errors

        doc_type = kind[0]
        indexing_data = document.get("indexingData", {})

        if doc_type == self.county.DEED_DOCUMENT_TYPE:
            # Validate DEED document specific requirements
            
            # Check for consideration - allow 0.00 for Horry workflow
            if "consideration" not in indexing_data:
                errors.append(f"{doc_prefix}: DEED missing consideration")
            elif not isinstance(indexing_data["consideration"], (int, float)):
                errors.append(f"{doc_prefix}: DEED consideration must be numeric")
            elif indexing_data["consideration"] < 0:  # Allow 0.00, just not negative
                errors.append(f"{doc_prefix}: DEED consideration cannot be negative")

            # Check for execution date
            if "executionDate" not in indexing_data or not indexing_data["executionDate"]:
                errors.append(f"{doc_prefix}: DEED missing execution date")

            # Check for legal descriptions
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append(f"{doc_prefix}: DEED missing legal descriptions")

            # Check for reference information
            if "referenceInformation" not in indexing_data or not indexing_data["referenceInformation"]:
                errors.append(f"{doc_prefix}: DEED missing reference information")

            # Check for KING CUNNINGHAM LLC TR in grantors
            grantors = indexing_data.get("grantors", [])
            has_king_cunningham = False
            for grantor in grantors:
                if (grantor.get("type") == "Organization" and 
                    "KING CUNNINGHAM LLC TR" in grantor.get("nameUnparsed", "")):
                    has_king_cunningham = True
                    break
            
            if not has_king_cunningham:
                errors.append(f"{doc_prefix}: DEED missing required grantor 'KING CUNNINGHAM LLC TR'")

        elif doc_type == self.county.MORTGAGE_DOCUMENT_TYPE:
            # Validate SATISFACTION document requirements
            
            # Check for execution date
            if "executionDate" not in indexing_data or not indexing_data["executionDate"]:
                errors.append(f"{doc_prefix}: SATISFACTION missing execution date")

            # Check for legal descriptions
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append(f"{doc_prefix}: SATISFACTION missing legal descriptions")

            # Check for reference information
            if "referenceInformation" not in indexing_data or not indexing_data["referenceInformation"]:
                errors.append(f"{doc_prefix}: SATISFACTION missing reference information")

            # Check that KING CUNNINGHAM LLC TR is NOT a grantor for satisfaction
            grantors = indexing_data.get("grantors", [])
            for grantor in grantors:
                if (grantor.get("type") == "Organization" and 
                    "KING CUNNINGHAM LLC TR" in grantor.get("nameUnparsed", "")):
                    errors.append(f"{doc_prefix}: SATISFACTION should not have 'KING CUNNINGHAM LLC TR' as grantor")
                    break

        return errors

    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a Horry MTG-FCL package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "package_type": "Horry Timeshare Deed + Mortgage Satisfaction",
            "documents": []
        }

        for document in package.get("documents", []):
            doc_summary = {
                "document_id": document.get("submitterDocumentID", "Unknown"),
                "name": document.get("name", "Unknown"),
                "type": document.get("kindOfInstrument", ["Unknown"])[0],
                "has_file": len(document.get("fileBytes", [])) > 0,
                "has_helper_documents": len(document.get("helperDocuments", [])) > 0
            }

            # Count parties
            indexing_data = document.get("indexingData", {})
            doc_summary["grantor_count"] = len(indexing_data.get("grantors", []))
            doc_summary["grantee_count"] = len(indexing_data.get("grantees", []))

            # Add specific info for each document type
            if doc_summary["type"] == self.county.DEED_DOCUMENT_TYPE:
                doc_summary["has_consideration"] = "consideration" in indexing_data
                doc_summary["merged_document"] = True  # Always merged deed+affidavit
            elif doc_summary["type"] == self.county.MORTGAGE_DOCUMENT_TYPE:
                doc_summary["satisfaction_type"] = "Mortgage Satisfaction"

            summary["documents"].append(doc_summary)

        return summary