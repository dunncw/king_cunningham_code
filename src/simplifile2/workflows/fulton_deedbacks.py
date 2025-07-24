# workflows/fulton_deedbacks.py - Fulton County Deedbacks workflow implementation
import os
import re
import base64
from typing import Dict, List, Any, Tuple
import pandas as pd

from .base import BaseWorkflow
from ..core.county_config import CountyConfig
from ..utils.logging import Logger, StepLogger


class FultonDeedbacksWorkflow(BaseWorkflow):
    """Fulton County Deedbacks workflow"""

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
        contract_num = transformed["contract_number"]
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
        self.document_catalog = {}  # Cache of discovered documents

    def scan_documents_directory(self, documents_directory: str) -> Dict[str, Dict[str, str]]:
        """
        Scan documents directory and catalog all PDF files
        
        Returns:
            Dictionary mapping (last_name, contract_num) -> {deed_path, pt61_path, sat_path}
        """
        self.document_catalog = {}
        
        if not os.path.exists(documents_directory) or not os.path.isdir(documents_directory):
            raise Exception(f"Documents directory does not exist: {documents_directory}")
        
        # Get all PDF files in directory
        pdf_files = [f for f in os.listdir(documents_directory) if f.lower().endswith('.pdf')]
        
        self.logger.info(f"Found {len(pdf_files)} PDF files in directory")
        
        # Parse each PDF filename and catalog
        for pdf_file in pdf_files:
            file_path = os.path.join(documents_directory, pdf_file)
            parsed = self._parse_filename(pdf_file)
            
            if parsed:
                last_name, contract_num, doc_type = parsed
                key = (last_name, contract_num)
                
                if key not in self.document_catalog:
                    self.document_catalog[key] = {}
                
                self.document_catalog[key][doc_type] = file_path
                self.logger.info(f"Cataloged: {last_name} {contract_num} -> {doc_type}")
            else:
                self.logger.warning(f"Could not parse filename: {pdf_file}")
        
        self.logger.info(f"Cataloged {len(self.document_catalog)} document sets")
        return self.document_catalog

    def _parse_filename(self, filename: str) -> Tuple[str, str, str] | None:
        """
        Parse filename according to Deedbacks naming convention
        
        Expected patterns:
        - {Last 1} DB {Contract Num} DB.pdf -> (last_name, contract_num, 'deed')
        - {Last 1} DB {Contract Num} DB PT61.pdf -> (last_name, contract_num, 'pt61')
        - {Last 1} DB {Contract Num} DB SAT.pdf -> (last_name, contract_num, 'sat')
        
        Returns:
            Tuple of (last_name, contract_num, doc_type) or None if not parseable
        """
        # Remove .pdf extension
        basename = filename[:-4] if filename.lower().endswith('.pdf') else filename
        
        # Pattern: {LASTNAME} DB {CONTRACT} DB {TYPE}
        # Where TYPE is optional (empty), PT61, or SAT
        
        # Try SAT pattern first
        sat_pattern = r'^(.+)\s+DB\s+(.+)\s+DB\s+SAT$'
        match = re.match(sat_pattern, basename, re.IGNORECASE)
        if match:
            last_name, contract_num = match.groups()
            return (last_name.strip().upper(), contract_num.strip(), 'sat')
        
        # Try PT61 pattern
        pt61_pattern = r'^(.+)\s+DB\s+(.+)\s+DB\s+PT61$'
        match = re.match(pt61_pattern, basename, re.IGNORECASE)
        if match:
            last_name, contract_num = match.groups()
            return (last_name.strip().upper(), contract_num.strip(), 'pt61')
        
        # Try basic deed pattern
        deed_pattern = r'^(.+)\s+DB\s+(.+)\s+DB$'
        match = re.match(deed_pattern, basename, re.IGNORECASE)
        if match:
            last_name, contract_num = match.groups()
            return (last_name.strip().upper(), contract_num.strip(), 'deed')
        
        return None

    def get_documents_for_package(self, last_name: str, contract_num: str) -> Dict[str, str]:
        """
        Get document paths for a specific package
        
        Returns:
            Dictionary with 'deed_path', 'pt61_path', and optionally 'sat_path'
        """
        key = (last_name.upper(), contract_num)
        
        if key not in self.document_catalog:
            raise Exception(f"No documents found for {last_name} {contract_num}")
        
        docs = self.document_catalog[key]
        
        # Check for required documents
        if 'deed' not in docs:
            raise Exception(f"Missing deed document for {last_name} {contract_num}")
        
        if 'pt61' not in docs:
            raise Exception(f"Missing PT-61 document for {last_name} {contract_num}")
        
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
        Validate that all Excel rows have corresponding documents
        
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
        
        excel_keys = set()
        
        # Check each Excel row for corresponding documents
        for index, row in excel_df.iterrows():
            row_number = index + 2  # +2 for 1-based indexing and header row
            
            try:
                last_name = str(row.get("Last 1", "")).strip().upper()
                contract_num = str(row.get("Contract Num", "")).strip()
                
                if not last_name or not contract_num:
                    continue  # Skip invalid rows
                
                key = (last_name, contract_num)
                excel_keys.add(key)
                
                if key in self.document_catalog:
                    docs = self.document_catalog[key]
                    
                    # Check for required documents
                    if 'deed' not in docs:
                        errors.append(f"Row {row_number}: Missing deed document for {last_name} {contract_num}")
                        summary["rows_missing_documents"] += 1
                    elif 'pt61' not in docs:
                        errors.append(f"Row {row_number}: Missing PT-61 document for {last_name} {contract_num}")
                        summary["rows_missing_documents"] += 1
                    else:
                        summary["rows_with_documents"] += 1
                        
                        match_info = {
                            "row_number": row_number,
                            "last_name": last_name,
                            "contract_num": contract_num,
                            "has_deed": True,
                            "has_pt61": True,
                            "has_sat": 'sat' in docs
                        }
                        summary["document_matches"].append(match_info)
                        
                        if 'sat' not in docs:
                            summary["rows_missing_sat"] += 1
                            # Don't log missing SAT as it's optional and will be shown in package output
                else:
                    errors.append(f"Row {row_number}: No documents found for {last_name} {contract_num}")
                    summary["rows_missing_documents"] += 1
                    
            except Exception as e:
                errors.append(f"Row {row_number}: Error processing - {str(e)}")
                summary["rows_missing_documents"] += 1
        
        # Check for orphaned documents
        catalog_keys = set(self.document_catalog.keys())
        orphaned_keys = catalog_keys - excel_keys
        summary["orphaned_documents"] = len(orphaned_keys)
        
        if orphaned_keys:
            self.logger.warning(f"Found {len(orphaned_keys)} orphaned document sets:")
            for last_name, contract_num in orphaned_keys:
                self.logger.warning(f"  - {last_name} {contract_num}")
        
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
        from ..core.county_config import get_county_config
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
                        docs = self.doc_processor.get_documents_for_package(last_name, contract_num)
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
                        self.logger.warning(f"Error getting document details for {last_name} {contract_num}: {str(e)}")
            
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
                last_name = str(row.get("Last 1", "")).strip().upper()
                contract_num = str(row.get("Contract Num", "")).strip()
                
                # Get documents for this package
                documents = self.doc_processor.get_documents_for_package(last_name, contract_num)
                
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