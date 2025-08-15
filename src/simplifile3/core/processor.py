# simplifile3/core/processor.py - Main processing orchestrator for simplifile3
import pandas as pd
import requests
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime

from ..utils.logging import Logger, StepLogger


class Simplifile3Processor:
    """Main processor that orchestrates the complete Simplifile3 workflow"""
    
    def __init__(self, api_token: str, workflow_id: str, logger: Logger):
        """
        Initialize the processor
        
        Args:
            api_token: Simplifile API token
            workflow_id: Workflow identifier (e.g., "bea_hor_countys_deedback")
            logger: Logger instance for output
        """
        self.api_token = api_token
        self.workflow_id = workflow_id
        self.logger = logger
        self.step_logger = StepLogger(logger)
        
        # Initialize components
        self.workflow = self._get_workflow()
        self.pdf_processor = self._get_pdf_processor()
        self.payload_builder = self._get_payload_builder()
        
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
    
    def _get_payload_builder(self):
        """Get payload builder for workflow"""
        if self.workflow_id == "bea_hor_countys_deedback":
            from ..workflows.bea_hor_countys_deedback.payload_builder import BeaHorCountysDeedbackPayloadBuilder
            return BeaHorCountysDeedbackPayloadBuilder(self.logger)
        else:
            raise ValueError(f"Payload builder not available for workflow '{self.workflow_id}'")
    
    def process_batch(self, workflow_config: Dict[str, Any], file_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        Process complete batch from workflow config and file paths
        
        Args:
            workflow_config: Workflow configuration dictionary
            file_paths: Dictionary of file paths from UI
        
        Returns:
            Dictionary with processing results and statistics
        """
        try:
            start_time = datetime.now()
            self.logger.header(f"{self.workflow_id.upper()} batch processing started")
            self.step_logger.reset()
            
            # Step 1: Load and validate Excel
            self.step_logger.start_step("Loading and validating Excel file")
            excel_df = self._load_and_validate_excel(file_paths.get("excel", ""))
            if excel_df is None:
                return self._create_error_result("Excel validation failed", self.stats["errors"])
            
            # Step 2: Process Excel data and create packages
            self.step_logger.start_step("Processing Excel data")
            valid_packages_data = self._process_excel_data(excel_df)
            
            if not valid_packages_data:
                return self._create_error_result("No valid packages to process", self.stats["errors"])
            
            self.logger.info(f"Created {len(valid_packages_data)} valid packages from {self.stats['total_rows']} Excel rows")
            if self.stats["skipped_rows"] > 0:
                self.logger.info(f"Skipped {self.stats['skipped_rows']} invalid rows")
            
            # Step 3: Generate API payloads and upload
            self.step_logger.start_step("Generating API payloads and uploading")
            upload_results = self._upload_packages(valid_packages_data, file_paths)
            
            # Step 4: Generate final results
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.logger.separator()
            self.logger.info("BATCH PROCESSING COMPLETED")
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
            if hasattr(self.pdf_processor, 'cleanup'):
                self.pdf_processor.cleanup()
    
    def _load_and_validate_excel(self, excel_path: str) -> pd.DataFrame:
        """Load and validate Excel file"""
        try:
            # Load Excel file with all columns as strings
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
        """Process Excel data into valid package data, handling multi-unit contracts"""
        valid_packages = []
        
        # Convert DataFrame to list of dictionaries
        excel_data = excel_df.to_dict('records')
        
        # Handle multi-unit contracts (for BEA-HOR-COUNTYS-DEEDBACK)
        if hasattr(self.workflow, 'group_multi_unit_contracts'):
            multi_unit_groups = self.workflow.group_multi_unit_contracts(excel_data)
            processed_contracts = set()
            
            for index, row in enumerate(excel_data):
                row_number = index + 2  # +2 for 1-based indexing and header row
                
                try:
                    # Convert row to dictionary
                    row_dict = row
                    
                    # Validate row data
                    is_valid, validation_error = self.workflow.is_row_valid(row_dict)
                    
                    if not is_valid:
                        self.logger.info(f"SKIPPING Row {row_number}: {validation_error}")
                        self.stats["skipped_rows"] += 1
                        continue
                    
                    # Check for multi-unit contract
                    project = row_dict.get("Project", "")
                    number = row_dict.get("Number", "")
                    contract_key = f"{project}-{number}"
                    
                    if contract_key in multi_unit_groups:
                        # Multi-unit contract
                        if contract_key in processed_contracts:
                            # Skip duplicate contract
                            self.logger.info(f"SKIPPING Row {row_number}: Duplicate contract {contract_key}")
                            self.stats["skipped_rows"] += 1
                            continue
                        else:
                            # Process as combined contract
                            group_indices = multi_unit_groups[contract_key]
                            group_rows = [excel_data[i] for i in group_indices]
                            
                            # Determine target county from first row
                            target_county = self.workflow.route_to_county(row_dict)
                            
                            # Combine multi-unit data
                            package_data = self.workflow.combine_multi_unit_data(group_rows, target_county)
                            package_data["excel_row"] = row_number
                            package_data["document_index"] = len(valid_packages)
                            package_data["is_multi_unit"] = True
                            package_data["unit_count"] = len(group_rows)
                            
                            valid_packages.append(package_data)
                            processed_contracts.add(contract_key)
                    else:
                        # Single unit contract
                        target_county = self.workflow.route_to_county(row_dict)
                        package_data = self.workflow.transform_row_data(row_dict, target_county)
                        package_data["excel_row"] = row_number
                        package_data["document_index"] = len(valid_packages)
                        package_data["is_multi_unit"] = False
                        package_data["unit_count"] = 1
                        
                        valid_packages.append(package_data)
                
                except Exception as e:
                    error_msg = f"Error processing row {row_number}: {str(e)}"
                    self.logger.info(f"SKIPPING Row {row_number}: {error_msg}")
                    self.stats["skipped_rows"] += 1
                    self.stats["errors"].append(error_msg)
        else:
            # Standard processing (non-multi-unit workflows)
            for index, row in enumerate(excel_data):
                row_number = index + 2
                
                try:
                    row_dict = row
                    
                    is_valid, validation_error = self.workflow.is_row_valid(row_dict)
                    
                    if not is_valid:
                        self.logger.info(f"SKIPPING Row {row_number}: {validation_error}")
                        self.stats["skipped_rows"] += 1
                        continue
                    
                    target_county = self.workflow.route_to_county(row_dict)
                    package_data = self.workflow.transform_row_data(row_dict, target_county)
                    package_data["excel_row"] = row_number
                    package_data["document_index"] = len(valid_packages)
                    
                    valid_packages.append(package_data)
                    
                except Exception as e:
                    error_msg = f"Error processing row {row_number}: {str(e)}"
                    self.logger.info(f"SKIPPING Row {row_number}: {error_msg}")
                    self.stats["skipped_rows"] += 1
                    self.stats["errors"].append(error_msg)
        
        return valid_packages
    
    def _upload_packages(self, packages_data: List[Dict[str, Any]], file_paths: Dict[str, str]) -> List[Dict[str, Any]]:
        """Upload packages to Simplifile API"""
        upload_results = []
        
        # Reset PDF processor for new batch
        if hasattr(self.pdf_processor, 'reset_for_new_batch'):
            self.pdf_processor.reset_for_new_batch()
        
        for package_data in packages_data:
            try:
                package_name = package_data["package_name"]
                
                self.logger.info(f"Processing package: {package_name}")
                
                # Extract PDF documents for this package
                pdf_documents = self.pdf_processor.get_documents_for_row(package_data, file_paths)
                
                # Skip if no PDF (duplicate contract case)
                if not pdf_documents:
                    self.logger.info(f"  Skipping PDF extraction for duplicate contract: {package_name}")
                    continue
                
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