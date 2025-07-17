# simplifile2/validator.py - Pre-processing validation to prevent broken API requests
import os
import pandas as pd
from typing import Dict, List, Any, Tuple
from .county_config import get_county_config
from .workflow_definition import get_workflow
from .pdf_stack_processor import FultonFCLPDFProcessor


class SimplifileValidator:
    """Comprehensive validator to ensure all data is valid before API submission"""
    
    def __init__(self, county_id: str, workflow_type: str, log_callback=None):
        self.county_id = county_id
        self.workflow_type = workflow_type
        self.log = log_callback or print
        
        # Initialize components
        self.county_config = get_county_config(county_id)
        self.workflow = get_workflow(county_id, workflow_type)
        self.pdf_processor = FultonFCLPDFProcessor()
    
    def validate_all(self, excel_path: str, deed_path: str, pt61_path: str, mortgage_path: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Comprehensive validation of all inputs before processing
        
        Returns:
            Tuple of (is_valid, error_messages, validation_summary)
        """
        errors = []
        validation_summary = {
            "files_checked": 0,
            "excel_rows": 0,
            "valid_packages": 0,
            "pdf_documents": 0,
            "issues_found": []
        }
        
        self.log("Starting comprehensive validation...")
        
        # Step 1: File existence validation
        self.log("Step 1: Validating file existence...")
        file_errors = self._validate_file_existence(excel_path, deed_path, pt61_path, mortgage_path)
        if file_errors:
            errors.extend(file_errors)
            return False, errors, validation_summary
        
        validation_summary["files_checked"] = 4
        
        # Step 2: PDF stack validation
        self.log("Step 2: Validating PDF stacks...")
        pdf_errors, pdf_summary = self._validate_pdf_stacks(deed_path, pt61_path, mortgage_path)
        if pdf_errors:
            errors.extend(pdf_errors)
            return False, errors, validation_summary
        
        validation_summary.update(pdf_summary)
        
        # Step 3: Excel validation
        self.log("Step 3: Validating Excel structure and data...")
        excel_valid, excel_errors, excel_summary = self._validate_excel_comprehensive(excel_path)
        if not excel_valid:
            errors.extend(excel_errors)
            return False, errors, validation_summary
        
        validation_summary.update(excel_summary)
        
        # Step 4: Data alignment validation
        self.log("Step 4: Validating data alignment...")
        alignment_errors = self._validate_data_alignment(validation_summary)
        if alignment_errors:
            errors.extend(alignment_errors)
            return False, errors, validation_summary
        
        # Step 5: Sample package validation
        self.log("Step 5: Validating sample package generation...")
        package_errors = self._validate_sample_package_generation(excel_path, deed_path, pt61_path, mortgage_path)
        if package_errors:
            errors.extend(package_errors)
            return False, errors, validation_summary
        
        self.log("All validations passed successfully!")
        return True, [], validation_summary
    
    def _validate_file_existence(self, excel_path: str, deed_path: str, pt61_path: str, mortgage_path: str) -> List[str]:
        """Validate that all required files exist and are readable"""
        errors = []
        
        file_checks = [
            (excel_path, "Excel file"),
            (deed_path, "Deed Stack PDF"),
            (pt61_path, "PT-61 Stack PDF"), 
            (mortgage_path, "Mortgage Satisfaction Stack PDF")
        ]
        
        for file_path, file_type in file_checks:
            if not file_path or not file_path.strip():
                errors.append(f"{file_type} path is empty")
                continue
                
            if not os.path.exists(file_path):
                errors.append(f"{file_type} does not exist: {file_path}")
                continue
                
            if not os.path.isfile(file_path):
                errors.append(f"{file_type} is not a file: {file_path}")
                continue
                
            # Check file size (basic sanity check)
            try:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    errors.append(f"{file_type} is empty: {file_path}")
                elif file_size > 100 * 1024 * 1024:  # 100MB limit
                    errors.append(f"{file_type} is too large (>100MB): {file_path}")
            except Exception as e:
                errors.append(f"Cannot read {file_type}: {str(e)}")
        
        return errors
    
    def _validate_pdf_stacks(self, deed_path: str, pt61_path: str, mortgage_path: str) -> Tuple[List[str], Dict[str, Any]]:
        """Validate PDF stack structure and alignment"""
        try:
            # Validate stack alignment
            pdf_errors = self.pdf_processor.validate_fcl_stacks(deed_path, pt61_path, mortgage_path)
            
            if pdf_errors:
                return pdf_errors, {}
            
            # Get stack summary for validation info
            summary = self.pdf_processor.get_fcl_stack_summary(deed_path, pt61_path, mortgage_path)
            
            pdf_validation_summary = {
                "pdf_documents": summary["max_packages"],
                "deed_pages": summary["deed_stack"]["total_pages"],
                "pt61_pages": summary["pt61_stack"]["total_pages"],
                "mortgage_pages": summary["mortgage_stack"]["total_pages"],
                "stacks_aligned": summary["all_stacks_aligned"]
            }
            
            self.log(f"PDF Validation: {summary['max_packages']} complete document sets found")
            
            return [], pdf_validation_summary
            
        except Exception as e:
            return [f"Error validating PDF stacks: {str(e)}"], {}
    
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
                self.log("Data validation warnings:")
                for error in data_errors:
                    self.log(f"   - {error}")
            
            if invalid_packages > 0:
                self.log(f"{invalid_packages} invalid rows will be skipped during processing")
                for issue in validation_issues:
                    self.log(f"   - {issue}")
            
            self.log(f"Excel Validation: {valid_packages} valid packages out of {total_rows} rows")
            
            # Consider validation successful if we have at least one valid package
            if valid_packages == 0:
                return False, ["No valid packages found in Excel file"], excel_summary
            
            return True, [], excel_summary
            
        except Exception as e:
            return False, [f"Error validating Excel file: {str(e)}"], {}
    
    def _validate_data_alignment(self, validation_summary: Dict[str, Any]) -> List[str]:
        """Validate that Excel and PDF data are properly aligned"""
        errors = []
        
        valid_packages = validation_summary.get("valid_packages", 0)
        pdf_documents = validation_summary.get("pdf_documents", 0)
        
        if valid_packages > pdf_documents:
            errors.append(
                f"Data alignment error: Excel has {valid_packages} valid packages "
                f"but PDF stacks only have {pdf_documents} document sets"
            )
        
        # Note: It's OK to have more PDF documents than Excel rows (extras will be ignored)
        if pdf_documents > valid_packages:
            self.log(f"PDF stacks have {pdf_documents} documents but only {valid_packages} will be processed")
        
        return errors
    
    def _validate_sample_package_generation(self, excel_path: str, deed_path: str, pt61_path: str, mortgage_path: str) -> List[str]:
        """Test package generation with first valid row to catch any structural issues"""
        try:
            # Load Excel and find first valid row
            excel_df = pd.read_excel(excel_path, dtype=str)
            
            first_valid_row = None
            for index, row in excel_df.iterrows():
                row_dict = row.to_dict()
                is_valid, _ = self.workflow.is_row_valid(row_dict)
                
                if is_valid:
                    first_valid_row = row_dict
                    break
            
            if not first_valid_row:
                return ["No valid rows found for sample package generation"]
            
            # Transform the row data
            package_data = self.workflow.transform_row_data(first_valid_row)
            package_data["document_index"] = 0  # Use first document set
            
            # Extract PDF documents
            pdf_documents = self.pdf_processor.get_fcl_documents(0, deed_path, pt61_path, mortgage_path)
            
            # Test document building
            from .document_builder import DocumentBuilder
            document_builder = DocumentBuilder(self.county_config)
            
            # Build sample package
            api_payload = document_builder.build_fcl_package(package_data, pdf_documents)
            
            # Validate the package
            validation_errors = document_builder.validate_package(api_payload)
            
            if validation_errors:
                return [f"Sample package validation failed: {'; '.join(validation_errors)}"]
            
            self.log("Sample package generation successful")
            return []
            
        except Exception as e:
            return [f"Error generating sample package: {str(e)}"]
    
    def cleanup(self):
        """Clean up resources"""
        self.pdf_processor.cleanup()