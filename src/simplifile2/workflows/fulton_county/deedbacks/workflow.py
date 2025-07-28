# workflows/fulton_deedbacks.py - UPDATED with PDF processor and payload builder integration
import os
import re
import base64
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

from ...base.workflow import BaseWorkflow
from ....core.county_config import CountyConfig
from ....utils.logging import Logger, StepLogger

# Import the new components
from .pdf_processor import FultonDeedbacksPDFProcessor
from .payload_builder import FultonDeedbacksPayloadBuilder


class FultonDeedbacksWorkflow(BaseWorkflow):
    """Fulton County Deedbacks workflow - SAME AS BEFORE"""

    def get_required_excel_columns(self) -> List[str]:
        """Required columns for Deedbacks workflow"""
        return [
            "Contract Num",
            "First 1",
            "Last 1",
            "Sales Price",
            "DB To"
        ]

    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel columns to internal field names"""
        return {
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

    def get_document_types(self) -> List[str]:
        """Deedbacks creates DEED and optionally SATISFACTION documents"""
        return [self.county.DEED_DOCUMENT_TYPE, self.county.MORTGAGE_DOCUMENT_TYPE]

    def normalize_contract_number(self, contract_num: str) -> str:
        """Normalize contract number by removing leading zeros"""
        if not contract_num:
            return ""
        # Remove leading zeros but keep the number as string
        return str(int(contract_num)) if contract_num.isdigit() else contract_num.strip()

    def transform_row_data(self, excel_row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Excel row data for Deedbacks workflow"""
        # Map Excel columns to internal fields
        mapping = self.get_excel_mapping()
        transformed = {}

        for excel_col, internal_field in mapping.items():
            value = excel_row.get(excel_col, "")
            if pd.isna(value):
                value = ""
            transformed[internal_field] = str(value).strip().upper()

        # Apply Deedbacks-specific business rules
        raw_contract_num = transformed["contract_number"]
        contract_num = self.normalize_contract_number(raw_contract_num)
        transformed["contract_number"] = contract_num
        
        last_1 = transformed["grantor_1_last_name"]

        # Package naming convention
        transformed["package_name"] = f"{last_1} DB {contract_num}"
        transformed["package_id"] = f"P-{contract_num}"

        # Clean consideration amount
        consideration = transformed["consideration_amount"]
        cleaned_consideration = self._clean_consideration(consideration)
        transformed["consideration_amount"] = cleaned_consideration

        # Process second owner logic (no & column, just check if First 2 exists)
        has_second = bool(transformed["grantor_2_first_name"])
        transformed["has_second_owner"] = has_second

        # Clean up optional middle names
        if not transformed["grantor_1_middle_name"]:
            transformed["grantor_1_middle_name"] = ""
        if not transformed["grantor_2_middle_name"]:
            transformed["grantor_2_middle_name"] = ""

        # Apply county fixed values
        transformed["parcel_id"] = self.county.FIXED_PARCEL_ID
        transformed["tax_exempt"] = self.county.FIXED_TAX_EXEMPT
        
        # For deedbacks, grantee comes from Excel DB To column
        transformed["deed_grantee_name"] = transformed["grantee_name"]
        transformed["deed_grantee_type"] = "Organization"
        transformed["sat_grantee_name"] = transformed["grantee_name"]
        transformed["sat_grantee_type"] = "Organization"

        # Document naming
        transformed["deed_document_id"] = f"D-{contract_num}-DEED"
        transformed["deed_document_name"] = f"{last_1} DB {contract_num} DEED"
        transformed["satisfaction_document_id"] = f"D-{contract_num}-SAT"
        transformed["satisfaction_document_name"] = f"{last_1} DB {contract_num} SAT"

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
        """Additional Deedbacks-specific validation"""
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

        # Validate DB To field
        if "DB To" in df.columns:
            for idx, value in df["DB To"].items():
                if pd.isna(value) or str(value).strip() == "":
                    errors.append(f"Missing 'DB To' value at row {idx + 2}")

        return errors

    def is_row_valid(self, excel_row: Dict[str, Any]) -> tuple[bool, str]:
        """Check if a row has all required data for Deedbacks processing"""
        # Check core required fields
        required_fields = {
            "Contract Num": excel_row.get("Contract Num"),
            "First 1": excel_row.get("First 1"),
            "Last 1": excel_row.get("Last 1"),
            "Sales Price": excel_row.get("Sales Price"),
            "DB To": excel_row.get("DB To")
        }

        # Check for empty required fields
        for field_name, value in required_fields.items():
            if pd.isna(value) or str(value).strip() == "":
                return False, f"Missing required field: {field_name}"

        # Validate sales price format
        sales_price = str(excel_row.get("Sales Price", "")).strip()
        cleaned_price = self._clean_consideration(sales_price)
        if cleaned_price <= 0:
            return False, f"Invalid sales price: {sales_price}"

        return True, ""


class FultonDeedbacksDocumentProcessor:
    """Document processor for Fulton Deedbacks workflow - handles directory-based file discovery"""

    def __init__(self, logger=None):
        self.logger = logger or Logger()
        self.document_catalog = {}  # Cache of discovered documents indexed by normalized contract number

    def normalize_contract_number(self, contract_num: str) -> str:
        """Normalize contract number by removing leading zeros"""
        if not contract_num:
            return ""
        # Remove leading zeros but keep the number as string
        return str(int(contract_num)) if contract_num.isdigit() else contract_num.strip()

    def scan_documents_directory(self, documents_directory: str) -> Dict[str, Dict[str, str]]:
        """
        Scan documents directory and catalog all PDF files by normalized contract number
        
        Returns:
            Dictionary mapping normalized_contract_num -> {deed_path, pt61_path, sat_path}
        """
        self.document_catalog = {}
        
        if not os.path.exists(documents_directory) or not os.path.isdir(documents_directory):
            raise Exception(f"Documents directory does not exist: {documents_directory}")
        
        # Get all PDF files in directory
        pdf_files = [f for f in os.listdir(documents_directory) if f.lower().endswith('.pdf')]
        
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
                self.logger.info(f"Cataloged: {normalized_contract_num} -> {doc_type} ({pdf_file})")
            else:
                self.logger.warning(f"Could not parse filename: {pdf_file}")
        
        self.logger.info(f"Cataloged {len(self.document_catalog)} document sets")
        return self.document_catalog

    def _parse_filename_by_contract(self, filename: str) -> Optional[Tuple[str, str]]:
        """
        Parse filename by contract number from the end of the filename
        
        Expected patterns (scanning from end):
        - *{Contract Num} DB.pdf -> (contract_num, 'deed')
        - *{Contract Num} DB PT61.pdf -> (contract_num, 'pt61')
        - *{Contract Num} DB SAT.pdf -> (contract_num, 'sat')
        - *{Contract Num}_PT61.pdf -> (contract_num, 'pt61')
        
        Returns:
            Tuple of (contract_num, doc_type) or None if not parseable
        """
        # Remove .pdf extension
        basename = filename[:-4] if filename.lower().endswith('.pdf') else filename
        
        # Try SAT pattern first: ends with "{CONTRACT} DB SAT"
        sat_pattern = r'(.+)\s+DB\s+SAT$'
        match = re.search(sat_pattern, basename, re.IGNORECASE)
        if match:
            contract_part = match.group(1).strip()
            contract_num = self._extract_contract_number(contract_part)
            if contract_num:
                return (contract_num, 'sat')
        
        # Try PT61 pattern: ends with "{CONTRACT} DB PT61"
        pt61_pattern = r'(.+)\s+DB\s+PT61$'
        match = re.search(pt61_pattern, basename, re.IGNORECASE)
        if match:
            contract_part = match.group(1).strip()
            contract_num = self._extract_contract_number(contract_part)
            if contract_num:
                return (contract_num, 'pt61')
        
        # Try underscore PT61 pattern: ends with "{CONTRACT}_PT61"
        pt61_underscore_pattern = r'(.+)_(\d+)_PT61$'
        match = re.search(pt61_underscore_pattern, basename, re.IGNORECASE)
        if match:
            contract_num = match.group(2)  # Extract the numeric part directly
            if contract_num:
                return (contract_num, 'pt61')
        
        # Try basic deed pattern: ends with "{CONTRACT} DB"
        deed_pattern = r'(.+)\s+DB$'
        match = re.search(deed_pattern, basename, re.IGNORECASE)
        if match:
            contract_part = match.group(1).strip()
            contract_num = self._extract_contract_number(contract_part)
            if contract_num:
                return (contract_num, 'deed')
        
        return None

    def _extract_contract_number(self, contract_part: str) -> Optional[str]:
        """
        Extract contract number from the end of the contract part
        Examples:
        - "DEMAYO DB 392400442" -> "392400442"
        - "060325 DB KING 202201353" -> "202201353"
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
        Get document paths for a specific contract number (normalized)
        
        Returns:
            Dictionary with 'deed_path', 'pt61_path', and optionally 'sat_path'
        """
        normalized_contract = self.normalize_contract_number(contract_num)
        
        if normalized_contract not in self.document_catalog:
            raise Exception(f"No documents found for contract {contract_num} (normalized: {normalized_contract})")
        
        docs = self.document_catalog[normalized_contract]
        
        # Check for required documents
        if 'deed' not in docs:
            raise Exception(f"Missing deed document for contract {contract_num}")
        
        if 'pt61' not in docs:
            raise Exception(f"Missing PT-61 document for contract {contract_num}")
        
        result = {
            'deed_path': docs['deed'],
            'pt61_path': docs['pt61']
        }
        
        # Add SAT if present
        if 'sat' in docs:
            result['sat_path'] = docs['sat']
        
        return result

    def validate_documents_for_excel(self, excel_df: pd.DataFrame) -> Tuple[List[str], Dict[str, Any]]:
        """
        Validate that all Excel rows have corresponding documents (matching by normalized contract number)
        
        Returns:
            (errors, summary_info)
        """
        errors = []
        summary = {
            "total_excel_rows": len(excel_df),
            "rows_with_documents": 0,
            "rows_missing_documents": 0,
            "rows_missing_sat": 0,
            "orphaned_documents": 0,
            "document_matches": []
        }
        
        excel_contracts = set()
        
        # Check each Excel row for corresponding documents
        for index, row in excel_df.iterrows():
            row_number = index + 2  # +2 for 1-based indexing and header row
            
            try:
                raw_contract_num = str(row.get("Contract Num", "")).strip()
                contract_num = self.normalize_contract_number(raw_contract_num)
                last_name = str(row.get("Last 1", "")).strip().upper()
                
                if not contract_num:
                    continue  # Skip invalid rows
                
                excel_contracts.add(contract_num)
                
                if contract_num in self.document_catalog:
                    docs = self.document_catalog[contract_num]
                    
                    # Check for required documents
                    if 'deed' not in docs:
                        errors.append(f"Row {row_number}: Missing deed document for contract {contract_num}")
                        summary["rows_missing_documents"] += 1
                    elif 'pt61' not in docs:
                        errors.append(f"Row {row_number}: Missing PT-61 document for contract {contract_num}")
                        summary["rows_missing_documents"] += 1
                    else:
                        summary["rows_with_documents"] += 1
                        
                        match_info = {
                            "row_number": row_number,
                            "last_name": last_name,
                            "contract_num": contract_num,
                            "raw_contract_num": raw_contract_num,
                            "has_deed": True,
                            "has_pt61": True,
                            "has_sat": 'sat' in docs
                        }
                        summary["document_matches"].append(match_info)
                        
                        if 'sat' not in docs:
                            summary["rows_missing_sat"] += 1
                            # Don't log missing SAT as it's optional and will be shown in package output
                else:
                    errors.append(f"Row {row_number}: No documents found for contract {contract_num} (from Excel: {raw_contract_num})")
                    summary["rows_missing_documents"] += 1
                    
            except Exception as e:
                errors.append(f"Row {row_number}: Error processing - {str(e)}")
                summary["rows_missing_documents"] += 1
        
        # Check for orphaned documents
        catalog_contracts = set(self.document_catalog.keys())
        orphaned_contracts = catalog_contracts - excel_contracts
        summary["orphaned_documents"] = len(orphaned_contracts)
        
        if orphaned_contracts:
            self.logger.warning(f"Found {len(orphaned_contracts)} orphaned document sets:")
            for contract_num in orphaned_contracts:
                self.logger.warning(f"  - Contract {contract_num}")
        
        return errors, summary

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of cataloged documents"""
        total_sets = len(self.document_catalog)
        sets_with_sat = sum(1 for docs in self.document_catalog.values() if 'sat' in docs)
        
        return {
            "total_document_sets": total_sets,
            "sets_with_sat": sets_with_sat,
            "sets_without_sat": total_sets - sets_with_sat,
            "catalog": self.document_catalog
        }

    def cleanup(self):
        """Clean up resources"""
        self.document_catalog.clear()


class FultonDeedbacksValidator:
    """Comprehensive validator for Fulton Deedbacks workflow"""
    
    def __init__(self, county_id: str, workflow_type: str, logger: Logger):
        self.county_id = county_id
        self.workflow_type = workflow_type
        self.logger = logger
        self.step_logger = StepLogger(logger)
        
        # Initialize components
        from ....core.county_config import get_county_config
        self.county_config = get_county_config(county_id)
        self.workflow = FultonDeedbacksWorkflow(self.county_config, self.logger)
        self.doc_processor = FultonDeedbacksDocumentProcessor(self.logger)
    
    def validate_all(self, excel_path: str, documents_directory: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Comprehensive validation of all inputs for Deedbacks workflow"""
        errors = []
        validation_summary = {
            "files_checked": 0,
            "excel_rows": 0,
            "valid_packages": 0,
            "documents_found": 0,
            "issues_found": []
        }
        
        self.logger.info("Starting Deedbacks validation and file discovery...")
        self.step_logger.reset()
        
        # Step 1: File existence validation
        self.step_logger.start_step("Validating file existence")
        file_errors = self._validate_file_existence(excel_path, documents_directory)
        if file_errors:
            errors.extend(file_errors)
            return False, errors, validation_summary
        
        validation_summary["files_checked"] = 2
        self.step_logger.step_success("Files exist and are accessible")
        
        # Step 2: Excel validation
        self.step_logger.start_step("Validating Excel structure and data")
        excel_valid, excel_errors, excel_summary = self._validate_excel_comprehensive(excel_path)
        if not excel_valid:
            errors.extend(excel_errors)
            return False, errors, validation_summary
        
        validation_summary.update(excel_summary)
        self.step_logger.step_success(f"{excel_summary.get('valid_packages', 0)} valid packages out of {excel_summary.get('excel_rows', 0)} rows")
        
        # Step 3: Document discovery
        self.step_logger.start_step("Scanning documents directory")
        try:
            self.doc_processor.scan_documents_directory(documents_directory)
            doc_summary = self.doc_processor.get_summary()
            validation_summary["documents_found"] = doc_summary["total_document_sets"]
            
            self.step_logger.step_success(f"Cataloged {doc_summary['total_document_sets']} document sets")
            
        except Exception as e:
            errors.append(f"Error scanning documents directory: {str(e)}")
            return False, errors, validation_summary
        
        # Step 4: Document matching validation
        self.step_logger.start_step("Matching Excel data to documents")
        try:
            excel_df = pd.read_excel(excel_path, dtype=str)
            doc_errors, match_summary = self.doc_processor.validate_documents_for_excel(excel_df)
            
            # Log successful matches in the requested format
            if match_summary["document_matches"]:
                self.logger.info("")
                for match in match_summary["document_matches"]:
                    last_name = match["last_name"]
                    contract_num = match["contract_num"]
                    
                    # Get the actual document filenames
                    try:
                        docs = self.doc_processor.get_documents_for_package(contract_num)
                        deed_filename = os.path.basename(docs['deed_path'])
                        pt61_filename = os.path.basename(docs['pt61_path'])
                        
                        package_name = f"{last_name} DB {contract_num} DEED"
                        self.logger.info(f"Package Name: {package_name}")
                        
                        if match["has_sat"]:
                            sat_filename = os.path.basename(docs['sat_path'])
                            self.logger.info(f"    Deed: {deed_filename}, {pt61_filename}")
                            self.logger.info(f"    SAT: {sat_filename}")
                        else:
                            self.logger.info(f"    Deed: {deed_filename}, {pt61_filename}")
                        
                        self.logger.info("")  # Empty line between packages
                        
                    except Exception as e:
                        self.logger.warning(f"Error getting document details for contract {contract_num}: {str(e)}")
            
            if doc_errors:
                errors.extend(doc_errors)
                return False, errors, validation_summary
            
            validation_summary.update(match_summary)
            self.step_logger.step_success(f"All {match_summary['rows_with_documents']} valid Excel rows have matching documents")
            
            if match_summary["orphaned_documents"] > 0:
                self.step_logger.step_warning(f"{match_summary['orphaned_documents']} orphaned document sets found")
            
        except Exception as e:
            errors.append(f"Error matching documents to Excel: {str(e)}")
            return False, errors, validation_summary
        
        # Step 5: Sample file loading test
        self.step_logger.start_step("Testing document file access")
        sample_errors = self._test_sample_document_access(excel_df)
        if sample_errors:
            errors.extend(sample_errors)
            return False, errors, validation_summary
        
        self.step_logger.step_success("Document files are accessible")
        
        self.logger.info("Deedbacks validation and file discovery completed successfully!")
        return True, [], validation_summary
    
    def _validate_file_existence(self, excel_path: str, documents_directory: str) -> List[str]:
        """Validate that required files/directories exist"""
        errors = []
        
        # Excel file validation
        if not excel_path or not excel_path.strip():
            errors.append("Excel file path is empty")
        elif not os.path.exists(excel_path):
            errors.append(f"Excel file does not exist: {excel_path}")
        elif not os.path.isfile(excel_path):
            errors.append(f"Excel path is not a file: {excel_path}")
        else:
            # Check file size
            try:
                file_size = os.path.getsize(excel_path)
                if file_size == 0:
                    errors.append(f"Excel file is empty: {excel_path}")
                elif file_size > 10 * 1024 * 1024:  # 10MB limit
                    errors.append(f"Excel file is too large (>10MB): {excel_path}")
            except Exception as e:
                errors.append(f"Cannot read Excel file: {str(e)}")
        
        # Documents directory validation
        if not documents_directory or not documents_directory.strip():
            errors.append("Documents directory path is empty")
        elif not os.path.exists(documents_directory):
            errors.append(f"Documents directory does not exist: {documents_directory}")
        elif not os.path.isdir(documents_directory):
            errors.append(f"Documents path is not a directory: {documents_directory}")
        else:
            # Check if directory has any PDF files
            try:
                pdf_files = [f for f in os.listdir(documents_directory) if f.lower().endswith('.pdf')]
                if not pdf_files:
                    errors.append(f"Documents directory contains no PDF files: {documents_directory}")
            except Exception as e:
                errors.append(f"Cannot read documents directory: {str(e)}")
        
        return errors
    
    def _validate_excel_comprehensive(self, excel_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Comprehensive Excel validation"""
        try:
            # Load Excel file
            excel_df = pd.read_excel(excel_path, dtype=str)
            total_rows = len(excel_df)
            
            # Structure validation
            structure_errors = self.workflow.validate_excel_structure(excel_df)
            if structure_errors:
                return False, structure_errors, {"excel_rows": total_rows}
            
            # Data validation
            data_errors = self.workflow.validate_excel_data(excel_df)
            
            # Count valid packages
            valid_packages = 0
            invalid_packages = 0
            validation_issues = []
            
            for index, row in excel_df.iterrows():
                row_number = index + 2  # +2 for 1-based indexing and header row
                row_dict = row.to_dict()
                
                is_valid, validation_error = self.workflow.is_row_valid(row_dict)
                
                if is_valid:
                    valid_packages += 1
                else:
                    invalid_packages += 1
                    validation_issues.append(f"Row {row_number}: {validation_error}")
            
            excel_summary = {
                "excel_rows": total_rows,
                "valid_packages": valid_packages,
                "invalid_packages": invalid_packages,
                "data_warnings": len(data_errors),
                "issues_found": validation_issues
            }
            
            # Log warnings but don't fail validation
            if data_errors:
                self.logger.warning("Data validation warnings:")
                for error in data_errors:
                    self.logger.info(f"   - {error}")
            
            if invalid_packages > 0:
                self.logger.warning(f"{invalid_packages} invalid rows will be skipped during processing")
                for issue in validation_issues:
                    self.logger.info(f"   - {issue}")
            
            # Consider validation successful if we have at least one valid package
            if valid_packages == 0:
                return False, ["No valid packages found in Excel file"], excel_summary
            
            return True, [], excel_summary
            
        except Exception as e:
            return False, [f"Error validating Excel file: {str(e)}"], {}
    
    def _test_sample_document_access(self, excel_df: pd.DataFrame) -> List[str]:
        """Test that we can actually read document files"""
        errors = []
        
        # Find first valid row with documents
        for index, row in excel_df.iterrows():
            row_dict = row.to_dict()
            is_valid, _ = self.workflow.is_row_valid(row_dict)
            
            if not is_valid:
                continue
            
            try:
                raw_contract_num = str(row.get("Contract Num", "")).strip()
                contract_num = self.workflow.normalize_contract_number(raw_contract_num)
                
                # Get documents for this contract
                documents = self.doc_processor.get_documents_for_package(contract_num)
                
                # Test reading each document
                for doc_type, file_path in documents.items():
                    if not os.path.exists(file_path):
                        errors.append(f"Document file missing: {file_path}")
                        continue
                    
                    try:
                        # Test file access and basic PDF validation
                        file_size = os.path.getsize(file_path)
                        if file_size == 0:
                            errors.append(f"Document file is empty: {file_path}")
                        elif file_size > 50 * 1024 * 1024:  # 50MB limit per file
                            errors.append(f"Document file too large (>50MB): {file_path}")
                        
                        # Try to read first few bytes to ensure it's a valid PDF
                        with open(file_path, 'rb') as f:
                            header = f.read(4)
                            if header != b'%PDF':
                                errors.append(f"File does not appear to be a valid PDF: {file_path}")
                                
                    except Exception as e:
                        errors.append(f"Cannot access document file {file_path}: {str(e)}")
                
                # Only test first valid row
                break
                
            except Exception as e:
                errors.append(f"Error testing document access: {str(e)}")
                break
        
        return errors
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.doc_processor, 'cleanup'):
            self.doc_processor.cleanup()

class FultonDeedbacksProcessor:
    """Main processor for Fulton Deedbacks workflow - handles complete batch processing"""
    
    def __init__(self, api_token: str, county_id: str, logger: Logger):
        self.api_token = api_token
        self.county_id = county_id
        self.logger = logger
        self.step_logger = StepLogger(logger)
        
        # Initialize components
        from ....core.county_config import get_county_config
        self.county_config = get_county_config(county_id)
        self.workflow = FultonDeedbacksWorkflow(self.county_config, self.logger)
        self.doc_processor = FultonDeedbacksDocumentProcessor(self.logger)
        self.pdf_processor = FultonDeedbacksPDFProcessor(self.logger)
        self.payload_builder = FultonDeedbacksPayloadBuilder(self.county_config, self.logger)
        
        # Hardcoded submitter ID
        self.submitter_id = "SCTP3G"
        
        # Processing statistics
        self.stats = {
            "total_rows": 0,
            "skipped_rows": 0,
            "processed_packages": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "errors": []
        }
    
    def process_batch(self, excel_path: str, documents_directory: str) -> Dict[str, Any]:
        """
        Process complete Deedbacks batch from Excel and documents directory
        
        Args:
            excel_path: Path to Excel file with package data
            documents_directory: Path to directory containing PDF documents
        
        Returns:
            Dictionary with processing results and statistics
        """
        try:
            from datetime import datetime
            import requests
            import json
            
            start_time = datetime.now()
            self.logger.header(f"{self.county_config.COUNTY_NAME} Deedbacks batch processing started")
            self.step_logger.reset()
            
            # Step 1: Load and validate Excel
            self.step_logger.start_step("Loading and validating Excel file")
            excel_df = self._load_and_validate_excel(excel_path)
            if excel_df is None:
                return self._create_error_result("Excel validation failed", self.stats["errors"])
            
            # Step 2: Scan documents directory
            self.step_logger.start_step("Scanning documents directory")
            try:
                self.doc_processor.scan_documents_directory(documents_directory)
                self.step_logger.step_success("Document catalog created")
            except Exception as e:
                error_msg = f"Error scanning documents directory: {str(e)}"
                self.logger.error(error_msg)
                return self._create_error_result(error_msg, [error_msg])
            
            # Step 3: Process Excel data and create packages
            self.step_logger.start_step("Processing Excel data and matching documents")
            valid_packages_data = self._process_excel_data(excel_df)
            
            if not valid_packages_data:
                return self._create_error_result("No valid packages to process", self.stats["errors"])
            
            self.logger.info(f"Created {len(valid_packages_data)} valid packages from {self.stats['total_rows']} Excel rows")
            if self.stats["skipped_rows"] > 0:
                self.logger.info(f"Skipped {self.stats['skipped_rows']} invalid rows")
            
            # Step 4: Generate API payloads and upload
            self.step_logger.start_step("Generating API payloads and uploading")
            upload_results = self._upload_packages(valid_packages_data)
            
            # Step 5: Generate final results
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.logger.separator()
            self.logger.info("DEEDBACKS BATCH PROCESSING COMPLETED")
            self.logger.separator("=")
            self.logger.info(f"Total processing time: {processing_time:.1f} seconds")
            self.logger.info(f"Packages processed: {self.stats['processed_packages']}")
            self.logger.info(f"Successful uploads: {self.stats['successful_uploads']}")
            self.logger.info(f"Failed uploads: {self.stats['failed_uploads']}")
            
            return {
                "success": True,
                "stats": self.stats,
                "processing_time": processing_time,
                "upload_results": upload_results
            }
            
        except Exception as e:
            self.logger.error(f"CRITICAL ERROR: {str(e)}")
            return self._create_error_result(f"Processing failed: {str(e)}", [str(e)])
        
        finally:
            # Cleanup
            if hasattr(self.doc_processor, 'cleanup'):
                self.doc_processor.cleanup()
            if hasattr(self.pdf_processor, 'cleanup'):
                self.pdf_processor.cleanup()
    
    def _load_and_validate_excel(self, excel_path: str) -> pd.DataFrame:
        """Load and validate Excel file"""
        try:
            # Load Excel file with all columns as strings except specific numeric columns
            excel_df = pd.read_excel(excel_path, dtype=str)
            self.stats["total_rows"] = len(excel_df)
            self.logger.info(f"Loaded Excel file with {self.stats['total_rows']} rows")
            
            # Validate Excel structure
            structure_errors = self.workflow.validate_excel_structure(excel_df)
            if structure_errors:
                self.logger.error("Excel structure validation failed:")
                for error in structure_errors:
                    self.logger.error(f"  - {error}")
                self.stats["errors"].extend(structure_errors)
                return None
            
            # Validate Excel data
            data_errors = self.workflow.validate_excel_data(excel_df)
            if data_errors:
                self.logger.warning("Excel data validation warnings:")
                for error in data_errors:
                    self.logger.warning(f"  - {error}")
                # Data errors are warnings, don't stop processing
            
            self.logger.info("Excel validation completed successfully")
            return excel_df
            
        except Exception as e:
            error_msg = f"Error loading Excel file: {str(e)}"
            self.logger.error(error_msg)
            self.stats["errors"].append(error_msg)
            return None
    
    def _process_excel_data(self, excel_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process Excel data into valid package data with document matching"""
        valid_packages = []
        
        for index, row in excel_df.iterrows():
            row_number = index + 2  # +2 for 1-based indexing and header row
            
            try:
                # Convert row to dictionary
                row_dict = row.to_dict()
                
                # Validate row data
                is_valid, validation_error = self.workflow.is_row_valid(row_dict)
                
                if not is_valid:
                    self.logger.info(f"SKIPPING Row {row_number}: {validation_error}")
                    self.stats["skipped_rows"] += 1
                    continue
                
                # Transform row data
                package_data = self.workflow.transform_row_data(row_dict)
                package_data["excel_row"] = row_number
                
                # Check if documents exist for this contract
                contract_num = package_data["contract_number"]
                try:
                    document_paths = self.doc_processor.get_documents_for_package(contract_num)
                    package_data["document_paths"] = document_paths
                    
                    # Log what we found
                    if "sat_path" in document_paths:
                        self.logger.info(f"Row {row_number}: {package_data['package_name']} (with SAT)")
                    else:
                        self.logger.info(f"Row {row_number}: {package_data['package_name']} (deed only)")
                    
                    valid_packages.append(package_data)
                    
                except Exception as e:
                    self.logger.info(f"SKIPPING Row {row_number}: {str(e)}")
                    self.stats["skipped_rows"] += 1
                    self.stats["errors"].append(f"Row {row_number}: {str(e)}")
                
            except Exception as e:
                error_msg = f"Error processing row {row_number}: {str(e)}"
                self.logger.info(f"SKIPPING Row {row_number}: {error_msg}")
                self.stats["skipped_rows"] += 1
                self.stats["errors"].append(error_msg)
        
        return valid_packages
    
    def _upload_packages(self, packages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Upload packages to Simplifile API"""
        upload_results = []
        
        for package_data in packages_data:
            try:
                package_name = package_data["package_name"]
                contract_num = package_data["contract_number"]
                document_paths = package_data["document_paths"]
                
                self.logger.info(f"Processing package: {package_name}")
                
                # Load PDF documents for this package
                pdf_documents = self.pdf_processor.get_documents_by_contract_number(
                    contract_num, document_paths
                )
                
                # Build API payload
                api_payload = self.payload_builder.build_package(package_data, pdf_documents)
                
                # Validate payload
                validation_errors = self.payload_builder.validate_package(api_payload)
                if validation_errors:
                    error_msg = f"Package validation failed: {'; '.join(validation_errors)}"
                    self.logger.error(f"  VALIDATION ERROR: {error_msg}")
                    
                    upload_results.append({
                        "package_name": package_name,
                        "status": "validation_failed",
                        "error": error_msg
                    })
                    self.stats["failed_uploads"] += 1
                    continue
                
                # Upload to API
                upload_result = self._upload_single_package(api_payload, package_name)
                upload_results.append(upload_result)
                
                self.stats["processed_packages"] += 1
                
                if upload_result["status"] == "success":
                    self.stats["successful_uploads"] += 1
                    self.logger.info(f"  Successfully uploaded: {package_name}")
                else:
                    self.stats["failed_uploads"] += 1
                    self.logger.error(f"  Upload failed: {package_name} - {upload_result['error']}")
                
            except Exception as e:
                error_msg = f"Error processing package {package_data.get('package_name', 'Unknown')}: {str(e)}"
                self.logger.error(f"  ERROR: {error_msg}")
                
                upload_results.append({
                    "package_name": package_data.get("package_name", "Unknown"),
                    "status": "processing_error",
                    "error": error_msg
                })
                self.stats["failed_uploads"] += 1
                self.stats["errors"].append(error_msg)
        
        return upload_results
    
    def _upload_single_package(self, api_payload: Dict[str, Any], package_name: str) -> Dict[str, Any]:
        """Upload a single package to Simplifile API"""
        try:
            import requests
            import json
            
            # Build API URL
            api_url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{self.submitter_id}/packages/create"
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "api_token": self.api_token
            }
            
            # Make API request
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(api_payload),
                timeout=300  # 5 minute timeout
            )
            
            # Log raw response first
            self.logger.info(f"API Raw Response [{response.status_code}] for {package_name}: {response.text}")
            
            # Process response
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("resultCode") == "SUCCESS":
                    return {
                        "package_name": package_name,
                        "status": "success",
                        "api_response": response_data
                    }
                else:
                    return {
                        "package_name": package_name,
                        "status": "api_error",
                        "error": f"API returned error: {response_data.get('message', 'Unknown error')}",
                        "api_response": response_data
                    }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                return {
                    "package_name": package_name,
                    "status": "http_error",
                    "error": error_msg,
                    "status_code": response.status_code
                }
                
        except requests.RequestException as e:
            return {
                "package_name": package_name,
                "status": "request_error",
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "package_name": package_name,
                "status": "unknown_error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _create_error_result(self, message: str, errors: List[str]) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "success": False,
            "error": message,
            "errors": errors,
            "stats": self.stats
        }
    
    def test_api_connection(self) -> Tuple[bool, str]:
        """Test API connection and credentials"""
        try:
            import requests
            
            # Test with a simple recipients endpoint
            api_url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{self.submitter_id}/recipients"
            
            headers = {
                "Content-Type": "application/json",
                "api_token": self.api_token
            }
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            # Log raw response first
            self.logger.info(f"API Raw Response [{response.status_code}]: {response.text}")
            
            if response.status_code == 200:
                return True, "API connection successful!"
            elif response.status_code == 401:
                error_msg = "Authentication failed: Invalid API token"
                return False, error_msg
            else:
                error_msg = f"API connection failed with status {response.status_code}"
                return False, error_msg
                
        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            return False, error_msg