# simplifile3/core/validator.py - Pre-processing validation for simplifile3
import os
import pandas as pd
from typing import Dict, List, Any, Tuple
from ..utils.logging import Logger, StepLogger


class Simplifile3Validator:
    """Comprehensive validator to ensure all data is valid before API submission"""
    
    def __init__(self, workflow_id: str, logger: Logger):
        self.workflow_id = workflow_id
        self.logger = logger
        self.step_logger = StepLogger(logger)
        
        # Initialize components
        self.workflow = self._get_workflow()
        self.pdf_processor = self._get_pdf_processor()
    
    def _get_workflow(self):
        """Get workflow instance for workflow type"""
        if self.workflow_id == "bea_hor_countys_deedback":
            from ..workflows.bea_hor_countys_deedback.workflow import BeaHorCountysDeedbackWorkflow
            return BeaHorCountysDeedbackWorkflow(self.logger)
        else:
            raise ValueError(f"Workflow '{self.workflow_id}' not supported")
    
    def _get_pdf_processor(self):
        """Get PDF processor for workflow"""
        if self.workflow_id == "bea_hor_countys_deedback":
            from ..workflows.bea_hor_countys_deedback.pdf_processor import BeaHorCountysDeedbackPDFProcessor
            return BeaHorCountysDeedbackPDFProcessor(self.logger)
        else:
            raise ValueError(f"PDF processor not available for workflow '{self.workflow_id}'")
    
    def validate_all(self, workflow_config: Dict[str, Any], file_paths: Dict[str, str]) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Comprehensive validation of all inputs before processing"""
        errors = []
        validation_summary = {
            "files_checked": 0,
            "excel_rows": 0,
            "valid_packages": 0,
            "pdf_documents": 0,
            "issues_found": []
        }
        
        self.logger.info("Starting comprehensive validation...")
        self.step_logger.reset()
        
        # Step 1: File existence validation
        self.step_logger.start_step("Validating file existence")
        file_errors = self._validate_file_existence(workflow_config, file_paths)
        if file_errors:
            errors.extend(file_errors)
            return False, errors, validation_summary
        
        validation_summary["files_checked"] = len(file_paths)
        self.step_logger.step_success("All files exist and are readable")
        
        # Step 2: Excel validation
        self.step_logger.start_step("Validating Excel structure and data")
        excel_valid, excel_errors, excel_summary = self._validate_excel_comprehensive(file_paths.get("excel", ""))
        if not excel_valid:
            errors.extend(excel_errors)
            return False, errors, validation_summary
        
        validation_summary.update(excel_summary)
        self.step_logger.step_success(f"{excel_summary.get('valid_packages', 0)} valid packages out of {excel_summary.get('excel_rows', 0)} rows")
        
        # Step 3: PDF validation
        self.step_logger.start_step("Validating PDF files")
        pdf_errors, pdf_summary = self._validate_pdf_files(file_paths, excel_summary.get("excel_data", []))
        if pdf_errors:
            errors.extend(pdf_errors)
            return False, errors, validation_summary
        
        validation_summary.update(pdf_summary)
        self.step_logger.step_success(f"{pdf_summary.get('pdf_documents', 0)} PDF documents validated")
        
        # Step 4: Sample package validation
        self.step_logger.start_step("Validating sample package generation")
        package_errors = self._validate_sample_package_generation(file_paths, excel_summary.get("excel_data", []))
        if package_errors:
            errors.extend(package_errors)
            return False, errors, validation_summary
        
        self.step_logger.step_success("Sample package generation successful")
        
        self.logger.info("All validations passed successfully!")
        return True, [], validation_summary
    
    def _validate_file_existence(self, workflow_config: Dict[str, Any], file_paths: Dict[str, str]) -> List[str]:
        """Validate that all required files exist and are readable"""
        errors = []
        
        required_files = workflow_config.get("required_files", [])
        
        for file_config in required_files:
            key = file_config["key"]
            file_type = file_config["label"]
            file_path = file_paths.get(key, "")
            
            if not file_path or not file_path.strip():
                errors.append(f"{file_type} path is empty")
                continue
                
            if not os.path.exists(file_path):
                errors.append(f"{file_type} does not exist: {file_path}")
                continue
                
            if file_config["type"] == "directory":
                if not os.path.isdir(file_path):
                    errors.append(f"{file_type} is not a directory: {file_path}")
                    continue
            else:
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
            excel_data = excel_df.to_dict('records')
            
            for index, row in enumerate(excel_data):
                row_number = index + 2  # +2 for 1-based indexing and header row
                row_dict = row
                
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
                "issues_found": validation_issues,
                "excel_data": excel_data  # Pass data for PDF validation
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
    
    def _validate_pdf_files(self, file_paths: Dict[str, str], excel_data: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Any]]:
        """Validate PDF files against Excel data"""
        try:
            # Validate PDFs
            pdf_errors = self.pdf_processor.validate_pdfs(file_paths, excel_data)
            
            if pdf_errors:
                return pdf_errors, {}
            
            # Get PDF summary for validation info
            summary = self.pdf_processor.get_pdf_summary(file_paths, excel_data)
            
            pdf_validation_summary = {
                "pdf_documents": summary.get("document_count", 0),
                "total_pdf_pages": summary.get("total_pages", 0),
                "workflow_type": summary.get("workflow_type", "unknown")
            }
            
            # Add workflow-specific info
            if "multi_unit_contracts" in summary:
                pdf_validation_summary["multi_unit_contracts"] = summary["multi_unit_contracts"]
                pdf_validation_summary["unique_contracts"] = summary["unique_contracts"]
                pdf_validation_summary["skipped_project_98"] = summary.get("skipped_project_98", 0)
            
            return [], pdf_validation_summary
            
        except Exception as e:
            return [f"Error validating PDF files: {str(e)}"], {}
    
    def _validate_sample_package_generation(self, file_paths: Dict[str, str], excel_data: List[Dict[str, Any]]) -> List[str]:
        """Test package generation with first valid row to catch any structural issues"""
        try:
            # Find first valid row
            first_valid_row = None
            for row in excel_data:
                is_valid, _ = self.workflow.is_row_valid(row)
                
                if is_valid:
                    first_valid_row = row
                    break
            
            if not first_valid_row:
                return ["No valid rows found for sample package generation"]
            
            # Transform the row data
            target_county = self.workflow.route_to_county(first_valid_row)
            package_data = self.workflow.transform_row_data(first_valid_row, target_county)
            package_data["document_index"] = 0  # Use first document set
            
            # Test PDF extraction (but don't actually extract)
            # Just validate that the PDF processor can handle the request
            if hasattr(self.pdf_processor, 'reset_for_new_batch'):
                self.pdf_processor.reset_for_new_batch()
            
            # Test document building
            from ..workflows.bea_hor_countys_deedback.payload_builder import BeaHorCountysDeedbackPayloadBuilder
            payload_builder = BeaHorCountysDeedbackPayloadBuilder(self.logger)
            
            # Create dummy PDF documents for validation
            dummy_pdf_documents = {"deed_pdf": "dummy_base64_data"}
            
            # Build sample package
            api_payload = payload_builder.build_package(package_data, dummy_pdf_documents)
            
            # Validate the package
            validation_errors = payload_builder.validate_package(api_payload)
            
            if validation_errors:
                return [f"Sample package validation failed: {'; '.join(validation_errors)}"]
            
            return []
            
        except Exception as e:
            return [f"Error generating sample package: {str(e)}"]
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self.pdf_processor, 'cleanup'):
            self.pdf_processor.cleanup()