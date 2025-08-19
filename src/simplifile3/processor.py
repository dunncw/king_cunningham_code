"""Thin processor that delegates to workflow classes."""

import json
import pandas as pd
import requests
from typing import Dict, List, Any, Optional

from .logging import Logger


class Processor:
    """Thin orchestrator that delegates to workflow implementations."""
    
    SUBMITTER_ID = "SCTP3G"
    API_BASE = "https://api.simplifile.com/sf/rest/api/erecord"
    
    def __init__(self, api_token: str, workflow_class, logger: Optional[Logger] = None):
        self.api_token = api_token
        self.logger = logger or Logger()
        self.workflow = workflow_class(logger)
        
        self.stats = {
            "total_rows": 0,
            "skipped_rows": 0,
            "successful_uploads": 0,
            "failed_uploads": 0
        }

    def process_batch(self, excel_path: str, pdf_paths: Dict[str, str]) -> Dict[str, Any]:
        """Process batch using workflow implementation."""
        try:
            self.logger.info(f"Starting {self.workflow.display_name} processing")
            
            # Load Excel with only required columns plus known optional columns
            required_columns = self.workflow.required_columns
            
            # Get all possible columns this workflow might use
            all_possible_columns = set(required_columns)
            if hasattr(self.workflow, 'field_mappings'):
                all_possible_columns.update(self.workflow.field_mappings.keys())
            
            # Convert to list for pandas
            columns_to_read = list(all_possible_columns)
            
            try:
                # First try to read all possible columns
                df = pd.read_excel(excel_path, dtype=str, usecols=columns_to_read)
            except ValueError:
                # If some columns don't exist, just read what's available
                # Get actual column names from the Excel file
                temp_df = pd.read_excel(excel_path, nrows=0)  # Just get headers
                available_columns = [col for col in columns_to_read if col in temp_df.columns]
                
                # Ensure we have at least the required columns
                missing_required = [col for col in required_columns if col not in available_columns]
                if missing_required:
                    raise ValueError(f"Missing required columns: {missing_required}")
                
                df = pd.read_excel(excel_path, dtype=str, usecols=available_columns)
            
            self.stats["total_rows"] = len(df)
            
            # Validate (this also pre-processes multi-unit contracts for BEA_HOR_DEEDBACK)
            errors = self.workflow.validate_excel(df)
            if errors:
                for error in errors:
                    self.logger.error(error)
                raise ValueError("Excel validation failed")
            
            # Use pre-processed DataFrame if available (for multi-unit workflows)
            if hasattr(self.workflow, 'processed_df'):
                working_df = self.workflow.processed_df
                self.logger.info(f"Using pre-processed DataFrame: {len(working_df)} packages")
            else:
                working_df = df
            
            # Process rows
            packages = []
            for idx, row in working_df.iterrows():
                row_dict = row.to_dict()
                excel_row_num = idx + 2  # +2 for 1-based and header
                
                if not self.workflow.is_row_valid(row_dict):
                    self.stats["skipped_rows"] += 1
                    continue
                
                # Transform row
                package_data = self.workflow.transform_row(row_dict)
                package_data["_index"] = idx  # For PDF extraction
                
                packages.append(package_data)
            
            # Upload packages
            for package_data in packages:
                try:
                    # Extract PDFs
                    pdfs = self.workflow.extract_pdfs(package_data, pdf_paths)
                    
                    # Build payload
                    payload = self.workflow.build_payload(package_data, pdfs)
                    
                    # Upload
                    success = self._upload(payload, package_data.get("package_name", "Unknown"))
                    
                    if success:
                        self.stats["successful_uploads"] += 1
                    else:
                        self.stats["failed_uploads"] += 1
                        
                except Exception as e:
                    self.logger.error(f"Package failed: {e}")
                    self.stats["failed_uploads"] += 1
            
            self.logger.info(f"Complete: {self.stats['successful_uploads']} successful, {self.stats['failed_uploads']} failed")
            return {"success": True, "stats": self.stats}
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return {"success": False, "error": str(e), "stats": self.stats}

    def _upload(self, payload: Dict[str, Any], package_name: str) -> bool:
        """Upload package to API."""
        url = f"{self.API_BASE}/submitters/{self.SUBMITTER_ID}/packages/create"
        headers = {
            "Content-Type": "application/json",
            "api_token": self.api_token
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("resultCode") == "SUCCESS":
                    self.logger.info(f"Uploaded: {package_name}")
                    return True
            
            self.logger.error(f"Upload failed for {package_name}: {response.text}")
            return False
            
        except Exception as e:
            self.logger.error(f"Upload error for {package_name}: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test API connection."""
        url = f"{self.API_BASE}/submitters/{self.SUBMITTER_ID}/recipients"
        headers = {"api_token": self.api_token}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            return response.status_code == 200
        except:
            return False