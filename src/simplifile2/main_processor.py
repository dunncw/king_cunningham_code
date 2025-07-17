# simplifile2/main_processor.py - Main processing orchestrator
import pandas as pd
import requests
import json
from typing import Dict, List, Any, Tuple, Callable
from datetime import datetime

from .county_config import get_county_config
from .workflow_definition import get_workflow
from .pdf_stack_processor import FultonFCLPDFProcessor
from .document_builder import DocumentBuilder


class SimplifileProcessor:
    """Main processor that orchestrates the complete Simplifile workflow"""
    
    def __init__(self, api_token: str, county_id: str, workflow_type: str, log_callback: Callable[[str], None] = None):
        """
        Initialize the processor
        
        Args:
            api_token: Simplifile API token
            county_id: County identifier (e.g., "GAC3TH")
            workflow_type: Workflow type (e.g., "fcl")
            log_callback: Function to call for logging messages
        """
        self.api_token = api_token
        self.county_id = county_id
        self.workflow_type = workflow_type
        self.log = log_callback or print
        
        # Initialize components
        self.county_config = get_county_config(county_id)
        self.workflow = get_workflow(county_id, workflow_type)
        self.pdf_processor = FultonFCLPDFProcessor()
        self.document_builder = DocumentBuilder(self.county_config)
        
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
    
    def process_batch(self, excel_path: str, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, Any]:
        """
        Process complete batch from Excel and PDF files
        
        Args:
            excel_path: Path to Excel file with package data
            deed_path: Path to deed stack PDF
            pt61_path: Path to PT-61 stack PDF
            mortgage_path: Path to mortgage satisfaction stack PDF
        
        Returns:
            Dictionary with processing results and statistics
        """
        try:
            start_time = datetime.now()
            self.log(f"Starting {self.county_config.COUNTY_NAME} {self.workflow_type.upper()} batch processing...")
            
            # Step 1: Validate PDF stacks
            self.log("Step 1: Validating PDF stacks...")
            pdf_errors = self._validate_pdf_stacks(deed_path, pt61_path, mortgage_path)
            if pdf_errors:
                for error in pdf_errors:
                    self.log(f"PDF Error: {error}")
                return self._create_error_result("PDF validation failed", pdf_errors)
            
            # Step 2: Load and validate Excel
            self.log("Step 2: Loading and validating Excel file...")
            excel_df = self._load_and_validate_excel(excel_path)
            if excel_df is None:
                return self._create_error_result("Excel validation failed", self.stats["errors"])
            
            # Step 3: Process Excel data and create packages
            self.log("Step 3: Processing Excel data...")
            valid_packages_data = self._process_excel_data(excel_df)
            
            if not valid_packages_data:
                return self._create_error_result("No valid packages to process", self.stats["errors"])
            
            self.log(f"Created {len(valid_packages_data)} valid packages from {self.stats['total_rows']} Excel rows")
            if self.stats["skipped_rows"] > 0:
                self.log(f"Skipped {self.stats['skipped_rows']} invalid rows")
            
            # Step 4: Generate API payloads and upload
            self.log("Step 4: Generating API payloads and uploading...")
            upload_results = self._upload_packages(valid_packages_data, deed_path, pt61_path, mortgage_path)
            
            # Step 5: Generate final results
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            self.log("-" * 60)
            self.log("BATCH PROCESSING COMPLETED")
            self.log(f"Total processing time: {processing_time:.1f} seconds")
            self.log(f"Packages processed: {self.stats['processed_packages']}")
            self.log(f"Successful uploads: {self.stats['successful_uploads']}")
            self.log(f"Failed uploads: {self.stats['failed_uploads']}")
            
            return {
                "success": True,
                "stats": self.stats,
                "processing_time": processing_time,
                "upload_results": upload_results
            }
            
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")
            return self._create_error_result(f"Processing failed: {str(e)}", [str(e)])
        
        finally:
            # Cleanup
            self.pdf_processor.cleanup()
    
    def _validate_pdf_stacks(self, deed_path: str, pt61_path: str, mortgage_path: str) -> List[str]:
        """Validate PDF stack alignment and structure"""
        try:
            errors = self.pdf_processor.validate_fcl_stacks(deed_path, pt61_path, mortgage_path)
            
            if not errors:
                # Get stack summary for logging
                summary = self.pdf_processor.get_fcl_stack_summary(deed_path, pt61_path, mortgage_path)
                self.log(f"Deed Stack: {summary['deed_stack']['complete_documents']} documents ({summary['deed_stack']['total_pages']} pages)")
                self.log(f"PT-61 Stack: {summary['pt61_stack']['complete_documents']} documents ({summary['pt61_stack']['total_pages']} pages)")
                self.log(f"Mortgage Stack: {summary['mortgage_stack']['complete_documents']} documents ({summary['mortgage_stack']['total_pages']} pages)")
                self.log(f"Maximum packages: {summary['max_packages']}")
            
            return errors
            
        except Exception as e:
            return [f"Error validating PDF stacks: {str(e)}"]
    
    def _load_and_validate_excel(self, excel_path: str) -> pd.DataFrame:
        """Load and validate Excel file"""
        try:
            # Load Excel file with all columns as strings except specific numeric columns
            excel_df = pd.read_excel(excel_path, dtype=str)
            self.stats["total_rows"] = len(excel_df)
            self.log(f"Loaded Excel file with {self.stats['total_rows']} rows")
            
            # Validate Excel structure
            structure_errors = self.workflow.validate_excel_structure(excel_df)
            if structure_errors:
                self.log("Excel structure validation failed:")
                for error in structure_errors:
                    self.log(f"  - {error}")
                self.stats["errors"].extend(structure_errors)
                return None
            
            # Validate Excel data
            data_errors = self.workflow.validate_excel_data(excel_df)
            if data_errors:
                self.log("Excel data validation warnings:")
                for error in data_errors:
                    self.log(f"  - WARNING: {error}")
                # Data errors are warnings, don't stop processing
            
            self.log("Excel validation completed successfully")
            return excel_df
            
        except Exception as e:
            error_msg = f"Error loading Excel file: {str(e)}"
            self.log(error_msg)
            self.stats["errors"].append(error_msg)
            return None
    
    def _process_excel_data(self, excel_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process Excel data into valid package data"""
        valid_packages = []
        
        for index, row in excel_df.iterrows():
            row_number = index + 2  # +2 for 1-based indexing and header row
            
            try:
                # Convert row to dictionary
                row_dict = row.to_dict()
                
                # Validate row data
                is_valid, validation_error = self.workflow.is_row_valid(row_dict)
                
                if not is_valid:
                    self.log(f"SKIPPING Row {row_number}: {validation_error}")
                    self.stats["skipped_rows"] += 1
                    continue
                
                # Transform row data
                package_data = self.workflow.transform_row_data(row_dict)
                package_data["excel_row"] = row_number
                package_data["document_index"] = len(valid_packages)  # 0-based index for PDF extraction
                
                valid_packages.append(package_data)
                
            except Exception as e:
                error_msg = f"Error processing row {row_number}: {str(e)}"
                self.log(f"SKIPPING Row {row_number}: {error_msg}")
                self.stats["skipped_rows"] += 1
                self.stats["errors"].append(error_msg)
        
        return valid_packages
    
    def _upload_packages(self, packages_data: List[Dict[str, Any]], deed_path: str, pt61_path: str, mortgage_path: str) -> List[Dict[str, Any]]:
        """Upload packages to Simplifile API"""
        upload_results = []
        
        for package_data in packages_data:
            try:
                package_name = package_data["package_name"]
                document_index = package_data["document_index"]
                
                self.log(f"Processing package: {package_name}")
                
                # Extract PDF documents for this package
                pdf_documents = self.pdf_processor.get_fcl_documents(
                    document_index, deed_path, pt61_path, mortgage_path
                )
                
                # Build API payload
                api_payload = self.document_builder.build_fcl_package(package_data, pdf_documents)
                
                # Validate payload
                validation_errors = self.document_builder.validate_package(api_payload)
                if validation_errors:
                    error_msg = f"Package validation failed: {'; '.join(validation_errors)}"
                    self.log(f"  VALIDATION ERROR: {error_msg}")
                    
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
                    self.log(f"  Successfully uploaded: {package_name}")
                else:
                    self.stats["failed_uploads"] += 1
                    self.log(f"  Upload failed: {package_name} - {upload_result['error']}")
                
            except Exception as e:
                error_msg = f"Error processing package {package_data.get('package_name', 'Unknown')}: {str(e)}"
                self.log(f"  ERROR: {error_msg}")
                
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
            self.log(f"API Raw Response [{response.status_code}] for {package_name}: {response.text}")
            
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
            self.log(f"API Raw Response [{response.status_code}]: {response.text}")
            
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