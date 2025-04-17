# batch_processor.py - Updated to use centralized models and processors
import os
import json
import requests
import base64
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .models import SimplifilePackage, SimplifileDocument, Party
from .pdf_processor import SimplifilePDFProcessor
from .excel_processor import SimplifileExcelProcessor

class SimplifileBatchPreview(QObject):
    """Generate a comprehensive preview of batch processing without hitting the API"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    preview_ready = pyqtSignal(str)  # JSON string of preview data


    def __init__(self):
        super().__init__()
        self.pdf_processor = SimplifilePDFProcessor()
        self.excel_processor = SimplifileExcelProcessor()


    def generate_preview(self, excel_path, deeds_path, mortgage_path, affidavits_path=None):
        """Generate an enhanced preview of the batch processing with reduced verbosity"""
        try:
            # Only emit one status message at the start
            self.status.emit("Processing...")
            self.progress.emit(5)
            
            # Load Excel data
            if not excel_path:
                self.error.emit("Excel file is required for preview")
                return False
                
            excel_data = self.excel_processor.load_excel_file(excel_path)
            if excel_data is None:
                return False
            
            self.progress.emit(20)
            
            # Generate preview of PDF splits without actually creating files
            deed_splits = []
            mortgage_splits = []
            affidavit_splits = []
            has_merged_docs = False
            
            if deeds_path:
                # Note: Not emitting status for individual steps anymore
                deed_splits = self.pdf_processor.analyze_deed_pdf(deeds_path)
                if not deed_splits and deeds_path:
                    self.error.emit("Failed to analyze deed documents")
                    return False
            
            self.progress.emit(30)
            
            if affidavits_path:
                affidavit_splits = self.pdf_processor.analyze_affidavit_pdf(affidavits_path)
                if not affidavit_splits and affidavits_path:
                    self.error.emit("Failed to analyze affidavit documents")
                    return False
                
                # Check if we can merge deeds and affidavits
                if deed_splits and affidavit_splits:
                    has_merged_docs = True
            
            self.progress.emit(40)
            
            if mortgage_path:
                mortgage_splits = self.pdf_processor.analyze_mortgage_pdf(mortgage_path)
                if not mortgage_splits and mortgage_path:
                    self.error.emit("Failed to analyze mortgage satisfaction documents")
                    return False
            
            self.progress.emit(60)
            
            # Create preview packages from Excel data
            packages = self.excel_processor.process_excel_data(excel_data)
            
            # Enhance packages with PDF information
            self.enhance_packages_with_pdf_info(packages, deed_splits, mortgage_splits, 
                                            affidavit_splits, has_merged_docs)
            
            # Build the preview data structure
            preview_data = self.build_preview_data(packages, excel_data, deed_splits, 
                                                mortgage_splits, affidavit_splits, has_merged_docs)
            
            self.progress.emit(90)
            
            # Convert to JSON string
            preview_json = json.dumps(preview_data, default=lambda o: o.__dict__, indent=2)
            
            # Final status update before completing
            self.status.emit("Preview completed")
            self.progress.emit(100)
            self.preview_ready.emit(preview_json)
            return True
            
        except Exception as e:
            self.error.emit(f"Error in preview generation: {str(e)}")
            return False
        finally:
            # Clean up any temporary files
            self.pdf_processor.cleanup()


    def enhance_packages_with_pdf_info(self, packages, deed_splits, mortgage_splits, 
                                     affidavit_splits, has_merged_docs):
        """Enhance package objects with PDF file information"""
        total_packages = len(packages)
        
        for i, package in enumerate(packages):
            # Update documents with PDF info
            for doc in package.documents:
                # For deed documents
                if doc.type == "Deed - Timeshare" and i < len(deed_splits):
                    deed_info = deed_splits[i]
                    doc.page_range = deed_info["page_range"]
                    doc.page_count = deed_info["page_count"]
                    
                    if has_merged_docs and i < len(affidavit_splits):
                        # This would be a merged document in actual processing
                        affidavit_info = affidavit_splits[i]
                        doc.page_range = f"{deed_info['page_range']},{affidavit_info['page_range']}"
                        doc.page_count = deed_info["page_count"] + affidavit_info["page_count"]
                
                # For mortgage documents
                elif doc.type == "Mortgage Satisfaction" and i < len(mortgage_splits):
                    mortgage_info = mortgage_splits[i]
                    doc.page_range = mortgage_info["page_range"]
                    doc.page_count = mortgage_info["page_count"]


    def build_preview_data(self, packages, excel_data, deed_splits, mortgage_splits, 
                        affidavit_splits, has_merged_docs):
        """Build a comprehensive preview data structure with enhanced validation information"""
        # Count how many packages will be created
        total_packages = len(packages)
        
        # How many Excel rows we have to work with
        total_rows = len(excel_data)
        
        # Create summary with detailed information
        preview_data = {
            "summary": {
                "total_packages": total_packages,
                "deed_documents": len(deed_splits),
                "mortgage_documents": len(mortgage_splits),
                "excel_rows": total_rows,
                "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "warnings": []
            },
            "packages": [],
            "validation": {
                "missing_data": [],
                "format_issues": self.excel_processor.validation_warnings,  # Include all Excel validation warnings
                "document_issues": []
            }
        }
        
        # Add information about affidavits and merged documents
        if affidavit_splits:
            preview_data["summary"]["affidavit_documents"] = len(affidavit_splits)
            
            if has_merged_docs:
                preview_data["summary"]["merged_documents"] = min(len(deed_splits), len(affidavit_splits))
                preview_data["summary"]["merge_status"] = "Each 2-page deed will be merged with a 2-page affidavit to create 4-page documents for upload"
                
                # Add warning if counts don't match
                if len(deed_splits) != len(affidavit_splits):
                    diff = abs(len(deed_splits) - len(affidavit_splits))
                    if len(deed_splits) > len(affidavit_splits):
                        preview_data["summary"]["warnings"].append(
                            f"Warning: Found {diff} more deed documents than affidavit documents. Extra deeds will not be merged."
                        )
                    else:
                        preview_data["summary"]["warnings"].append(
                            f"Warning: Found {diff} more affidavit documents than deed documents. Extra affidavits will not be used."
                        )
        
        # Add warnings about missing recommended columns
        if self.excel_processor.missing_recommended_columns:
            preview_data["validation"]["format_issues"].extend([
                f"Missing recommended column: {col}" for col in self.excel_processor.missing_recommended_columns
            ])
        
        # Add warnings to summary
        if total_rows < total_packages:
            preview_data["summary"]["warnings"].append(
                f"Excel has fewer rows ({total_rows}) than documents to process ({total_packages})"
            )
        
        if len(deed_splits) != len(mortgage_splits):
            preview_data["summary"]["warnings"].append(
                f"Mismatch between deed documents ({len(deed_splits)}) and mortgage documents ({len(mortgage_splits)})"
            )
        
        # Convert packages to display dictionaries for preview
        for package in packages:
            # Check package validity
            if not package.is_valid:
                for issue in package.validation_issues:
                    preview_data["validation"]["missing_data"].append(
                        f"Row {package.excel_row}: {issue}"
                    )
            
            # Add package display info to preview data
            preview_data["packages"].append(package.to_display_dict())
            
            # Check for document issues
            for doc in package.documents:
                if not doc.is_valid:
                    doc_id = doc.document_id
                    for issue in doc.validation_issues:
                        preview_data["validation"]["document_issues"].append(
                            f"Package {package.package_id}: {doc_id} - {issue}"
                        )
        
        # Add validation summary
        preview_data["validation_summary"] = {
            "total_packages": len(packages),
            "valid_packages": sum(1 for p in packages if p.is_valid),
            "invalid_packages": sum(1 for p in packages if not p.is_valid),
            "missing_data_issues": len(preview_data["validation"]["missing_data"]),
            "format_issues": len(preview_data["validation"]["format_issues"]),
            "document_issues": len(preview_data["validation"]["document_issues"])
        }
        
        return preview_data


class SimplifileBatchProcessor(QObject):
    """Process and upload batch files to Simplifile"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(dict)


    def __init__(self, api_token=None, submitter_id=None, recipient_id=None):
        super().__init__()
        self.api_token = api_token
        self.submitter_id = submitter_id
        self.recipient_id = recipient_id
        self.pdf_processor = SimplifilePDFProcessor()
        self.excel_processor = SimplifileExcelProcessor()
        self.preview_mode = True  # Default to preview mode


    def process_batch(self, excel_path, deeds_path, mortgage_path, preview_mode=True, affidavits_path=None, skip_validation=True):
        """Process batch upload with reduced status messages"""
        try:
            self.preview_mode = preview_mode
            # Only emit a single status message to start
            self.status.emit("Processing... Please wait")
            self.progress.emit(5)
            
            # Load Excel data
            excel_data = self.excel_processor.load_excel_file(excel_path)
            if excel_data is None:
                return False
            
            self.progress.emit(10)
            
            # Process PDF files
            deed_files = []
            mortgage_files = []
            affidavit_files = []
            
            if deeds_path:
                deed_files = self.pdf_processor.split_deed_pdf(deeds_path)
                if not deed_files and deeds_path:
                    self.error.emit("Failed to process deed documents")
                    return False
            
            self.progress.emit(30)
            
            if affidavits_path:
                affidavit_files = self.pdf_processor.split_affidavit_pdf(affidavits_path)
                if not affidavit_files and affidavits_path:
                    self.error.emit("Failed to process affidavit documents")
                    return False
                
                # If we have both deed and affidavit files, merge them
                if deed_files and affidavit_files:
                    deed_files = self.pdf_processor.merge_deeds_and_affidavits(deed_files, affidavit_files)
            
            self.progress.emit(50)
            
            if mortgage_path:
                mortgage_files = self.pdf_processor.split_mortgage_pdf(mortgage_path)
                if not mortgage_files and mortgage_path:
                    self.error.emit("Failed to process mortgage satisfaction documents")
                    return False
            
            self.progress.emit(60)
            
            # Create packages from Excel data
            packages = self.excel_processor.process_excel_data(excel_data)
            
            # Assign PDF files to packages
            self.assign_pdf_files_to_packages(packages, deed_files, mortgage_files)
            
            self.progress.emit(70)
            
            # In preview mode, just return the packages without uploading
            if self.preview_mode:
                package_info = {
                    "resultCode": "SUCCESS",
                    "message": "Batch processing preview completed",
                    "packages": [p.to_display_dict() for p in packages]
                }
                    
                self.status.emit("Batch processing preview completed")
                self.progress.emit(100)
                self.finished.emit(package_info)
            else:
                # In actual upload mode, send packages to API
                if not self.api_token or not self.submitter_id or not self.recipient_id:
                    self.error.emit("Missing API credentials. Cannot proceed with upload.")
                    return False
                
                self.status.emit("Starting API upload...")
                upload_results = self.upload_packages_to_api(packages)
                
                # Report results
                self.status.emit("API upload process completed")
                self.progress.emit(100)
                self.finished.emit(upload_results)
            
            # Return success
            return True
            
        except Exception as e:
            self.error.emit(f"Error in batch processing: {str(e)}")
            return False
        finally:
            # Clean up temporary files
            self.pdf_processor.cleanup()


    def assign_pdf_files_to_packages(self, packages, deed_files, mortgage_files):
        """Assign PDF files to the corresponding packages and documents"""
        for i, package in enumerate(packages):
            if i < len(deed_files):
                # For each document in the package
                for doc in package.documents:
                    if doc.type == "Deed - Timeshare" and i < len(deed_files):
                        # Assign deed file
                        doc.file_path = deed_files[i]["path"]
                        doc.page_range = deed_files[i]["page_range"]
                        doc.page_count = deed_files[i]["page_count"]
                    
                    elif doc.type == "Mortgage Satisfaction" and i < len(mortgage_files):
                        # Assign mortgage file
                        doc.file_path = mortgage_files[i]["path"]
                        doc.page_range = mortgage_files[i]["page_range"]
                        doc.page_count = mortgage_files[i]["page_count"]


    def upload_packages_to_api(self, packages):
        """Upload packages to Simplifile API with improved error categorization and summary"""
        try:
            self.status.emit("Uploading packages to API...")
            
            # Prepare enhanced results structure with better error categorization
            results = {
                "resultCode": "SUCCESS",
                "message": "Packages uploaded to Simplifile API",
                "packages": [],
                "summary": {
                    "total": len(packages),
                    "successful": 0,
                    "failed": 0
                },
                "error_categories": {}  # Add categorized errors for better summary
            }
            
            # Process packages in smaller batches
            batch_size = 5  # Process 5 packages before yielding control
            for batch_idx in range(0, len(packages), batch_size):
                batch_end = min(batch_idx + batch_size, len(packages))
                batch = packages[batch_idx:batch_end]
                
                # Update status for this batch
                self.status.emit(f"Processing packages {batch_idx+1}-{batch_end} of {len(packages)}...")
                self.progress.emit(70 + (batch_idx * 30 // len(packages)))
                
                # Process each package in the batch
                for i, package in enumerate(batch):
                    package_name = package.package_name
                    package_id = package.package_id
                    documents = package.documents
                    
                    # Update progress
                    if i == 0 or i == len(batch)-1 or i % 2 == 0:
                        self.status.emit(f"Uploading package {batch_idx+i+1}/{len(packages)}...")
                    
                    # Process UI events frequently to keep UI responsive
                    QApplication.processEvents()
                    
                    # Create API payload
                    api_payload = package.to_api_dict()
                    api_payload["recipient"] = self.recipient_id  # Add recipient ID
                    
                    # Make the actual API request
                    try:
                        # Build API URL
                        base_url = f"https://api.simplifile.com/sf/rest/api/erecord/submitters/{self.submitter_id}/packages/create"
                        
                        headers = {
                            "Content-Type": "application/json",
                            "api_token": self.api_token
                        }
                        
                        # Post to API
                        response = requests.post(
                            base_url,
                            headers=headers,
                            data=json.dumps(api_payload),
                            timeout=300  # 5 minute timeout for large packages
                        )
                        
                        # Process response
                        if response.status_code == 200:
                            response_data = response.json()
                            if response_data.get("resultCode") == "SUCCESS":
                                results["packages"].append({
                                    "package_id": package_id,
                                    "status": "success",
                                    "message": "Package uploaded successfully",
                                    "package_name": package_name,
                                    "document_count": len(documents),
                                    "api_response": response_data
                                })
                                results["summary"]["successful"] += 1
                            else:
                                # Enhanced error categorization
                                error_msg = response_data.get("message", "Unknown API error")
                                error_details = []
                                
                                # Extract all error information available
                                if "errors" in response_data:
                                    for err in response_data.get("errors", []):
                                        error_path = err.get("path", "Unknown field")
                                        error_message = err.get("message", "Unknown error")
                                        error_details.append(f"{error_path}: {error_message}")
                                
                                # If we have specific errors, join them into a single string
                                error_details_str = "; ".join(error_details) if error_details else ""
                                
                                # Create error category for grouping similar errors
                                error_category = "api_error"
                                error_subcategory = "unknown"
                                
                                # Try to detect common error patterns for categorization
                                if "validation" in error_msg.lower() or "required" in error_msg.lower():
                                    error_subcategory = "validation"
                                elif "unauthorized" in error_msg.lower() or "authentication" in error_msg.lower():
                                    error_subcategory = "auth"
                                elif "not found" in error_msg.lower():
                                    error_subcategory = "not_found"
                                
                                # Create composite category
                                category_key = f"{error_category}_{error_subcategory}"
                                
                                # Update error categories count
                                if category_key not in results["error_categories"]:
                                    results["error_categories"][category_key] = {
                                        "count": 0,
                                        "description": f"API {error_subcategory} error",
                                        "examples": []
                                    }
                                
                                results["error_categories"][category_key]["count"] += 1
                                
                                # Add to examples if we have room
                                if len(results["error_categories"][category_key]["examples"]) < 3:
                                    example = {
                                        "package_id": package_id,
                                        "message": error_msg
                                    }
                                    results["error_categories"][category_key]["examples"].append(example)
                                    
                                detailed_error = f"{error_msg} {error_details_str}".strip()
                                if not detailed_error:
                                    detailed_error = f"API returned error with no message details"
                                    
                                self.status.emit(f"❌ Package {package_name} failed: {detailed_error}")
                                        
                                results["packages"].append({
                                    "package_id": package_id,
                                    "status": error_category,
                                    "status_subcategory": error_subcategory,
                                    "message": detailed_error,
                                    "package_name": package_name,
                                    "document_count": len(documents),
                                    "api_response": response_data,
                                    "raw_response": json.dumps(response_data)
                                })
                                
                                results["summary"]["failed"] += 1
                        else:
                            # Enhanced HTTP error categorization
                            error_category = "http_error"
                            error_subcategory = str(response.status_code)
                            
                            try:
                                # Try to parse as JSON first
                                error_data = response.json()
                                error_message = error_data.get("message", f"HTTP Error {response.status_code}")
                                
                                # Update error categories count
                                category_key = f"{error_category}_{error_subcategory}"
                                if category_key not in results["error_categories"]:
                                    results["error_categories"][category_key] = {
                                        "count": 0,
                                        "description": f"HTTP {response.status_code} error",
                                        "examples": []
                                    }
                                
                                results["error_categories"][category_key]["count"] += 1
                                
                                # Add to examples if we have room
                                if len(results["error_categories"][category_key]["examples"]) < 3:
                                    example = {
                                        "package_id": package_id,
                                        "message": error_message
                                    }
                                    results["error_categories"][category_key]["examples"].append(example)
                                
                                self.status.emit(f"❌ Package {package_name} failed: HTTP Error {response.status_code}: {error_message}")
                                
                                results["packages"].append({
                                    "package_id": package_id,
                                    "status": error_category,
                                    "status_subcategory": error_subcategory,
                                    "message": f"HTTP Error {response.status_code}: {error_message}",
                                    "package_name": package_name,
                                    "document_count": len(documents),
                                    "response_json": error_data,
                                    "raw_response": json.dumps(error_data)
                                })
                            except json.JSONDecodeError:
                                # If not JSON, use text response
                                error_text = response.text
                                
                                # Update error categories count
                                category_key = f"{error_category}_{error_subcategory}"
                                if category_key not in results["error_categories"]:
                                    results["error_categories"][category_key] = {
                                        "count": 0,
                                        "description": f"HTTP {response.status_code} error",
                                        "examples": []
                                    }
                                
                                results["error_categories"][category_key]["count"] += 1
                                
                                # Add to examples if we have room
                                if len(results["error_categories"][category_key]["examples"]) < 3:
                                    example = {
                                        "package_id": package_id,
                                        "message": error_text[:100] + ("..." if len(error_text) > 100 else "")
                                    }
                                    results["error_categories"][category_key]["examples"].append(example)
                                
                                self.status.emit(f"❌ Package {package_name} failed: HTTP Error {response.status_code}")
                                
                                results["packages"].append({
                                    "package_id": package_id,
                                    "status": error_category,
                                    "status_subcategory": error_subcategory,
                                    "message": f"HTTP Error {response.status_code}",
                                    "package_name": package_name,
                                    "document_count": len(documents),
                                    "response_text": error_text
                                })
                            
                            results["summary"]["failed"] += 1
                            
                    except requests.RequestException as req_err:
                        # Enhanced request exception categorization
                        error_category = "request_error"
                        error_subcategory = "general"
                        
                        # Determine more specific subcategory
                        if isinstance(req_err, requests.ConnectionError):
                            error_subcategory = "connection"
                            error_message = f"Connection error: Failed to connect to Simplifile API"
                        elif isinstance(req_err, requests.Timeout):
                            error_subcategory = "timeout"
                            error_message = f"Timeout error: The request took too long to complete"
                        elif isinstance(req_err, requests.TooManyRedirects):
                            error_subcategory = "redirect"
                            error_message = f"Redirect error: Too many redirects"
                        else:
                            error_message = f"Request error: {str(req_err)}"
                        
                        # Update error categories count
                        category_key = f"{error_category}_{error_subcategory}"
                        if category_key not in results["error_categories"]:
                            results["error_categories"][category_key] = {
                                "count": 0,
                                "description": f"{error_subcategory.capitalize()} error",
                                "examples": []
                            }
                        
                        results["error_categories"][category_key]["count"] += 1
                        
                        # Add to examples if we have room
                        if len(results["error_categories"][category_key]["examples"]) < 3:
                            example = {
                                "package_id": package_id,
                                "message": error_message
                            }
                            results["error_categories"][category_key]["examples"].append(example)
                        
                        self.status.emit(f"❌ Package {package_name} failed: {error_message}")
                        
                        results["packages"].append({
                            "package_id": package_id,
                            "status": error_category,
                            "status_subcategory": error_subcategory,
                            "message": error_message,
                            "package_name": package_name,
                            "document_count": len(documents),
                            "error_details": str(req_err)
                        })
                        
                        results["summary"]["failed"] += 1
                        
                    except Exception as e:
                        # General exception categorization
                        error_category = "exception"
                        error_subcategory = type(e).__name__
                        error_message = f"Exception ({error_subcategory}): {str(e)}"
                        
                        # Update error categories count
                        category_key = f"{error_category}_{error_subcategory}"
                        if category_key not in results["error_categories"]:
                            results["error_categories"][category_key] = {
                                "count": 0,
                                "description": f"{error_subcategory} exception",
                                "examples": []
                            }
                        
                        results["error_categories"][category_key]["count"] += 1
                        
                        # Add to examples if we have room
                        if len(results["error_categories"][category_key]["examples"]) < 3:
                            example = {
                                "package_id": package_id,
                                "message": str(e)
                            }
                            results["error_categories"][category_key]["examples"].append(example)
                        
                        self.status.emit(f"❌ Package {package_name} failed: {error_message}")
                        
                        results["packages"].append({
                            "package_id": package_id,
                            "status": error_category,
                            "status_subcategory": error_subcategory,
                            "message": error_message,
                            "package_name": package_name,
                            "document_count": len(documents),
                            "error_details": str(e)
                        })
                        
                        results["summary"]["failed"] += 1
                    
                    # Process UI events after each package to keep UI responsive
                    QApplication.processEvents()
                
                # Process events after each batch to ensure UI responsiveness
                QApplication.processEvents()
            
            # Update final result code based on summary
            if results["summary"]["failed"] > 0:
                if results["summary"]["successful"] > 0:
                    results["resultCode"] = "PARTIAL_SUCCESS"
                    results["message"] = f"Completed with {results['summary']['successful']} successful and {results['summary']['failed']} failed packages"
                else:
                    results["resultCode"] = "FAILED"
                    results["message"] = "All packages failed to upload"
                    
                # Add error category summary to the message
                categories_summary = []
                for category, info in results["error_categories"].items():
                    categories_summary.append(f"{info['count']} {info['description']}")
                
                if categories_summary:
                    results["error_summary"] = ", ".join(categories_summary)
                    results["message"] += f". Errors: {results['error_summary']}"
            
            # Post-processing: Add timing information
            results["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Final UI update
            QApplication.processEvents()
            
            return results
                
        except Exception as e:
            # Enhanced top-level error handling
            import traceback
            tb = traceback.format_exc()
            
            error_message = f"Error in API upload process: {str(e)}"
            self.error.emit(error_message)
            self.status.emit(f"Error traceback: {tb}")
            
            # Process UI events to ensure error message is shown
            QApplication.processEvents()
            
            return {
                "resultCode": "ERROR",
                "message": error_message,
                "error_details": str(e),
                "traceback": tb,
                "packages": [],
                "summary": {
                    "total": len(packages),
                    "successful": 0,
                    "failed": len(packages)
                }
            }


# Helper functions to create threads for batch operations
def run_simplifile_batch_preview(excel_path, deeds_path, mortgage_path, affidavits_path=None):
    """Create and run a thread for Simplifile batch preview"""
    thread = QThread()
    worker = SimplifileBatchPreview()
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(lambda: worker.generate_preview(excel_path, deeds_path, mortgage_path, affidavits_path))
    worker.preview_ready.connect(thread.quit)
    worker.error.connect(lambda e: thread.quit())
    worker.preview_ready.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker


def run_simplifile_batch_process(excel_path, deeds_path, mortgage_path, api_token=None, submitter_id=None, recipient_id=None, preview_mode=True, affidavits_path=None):
    """Create and run a thread for Simplifile batch processing with improved thread handling"""
    thread = QThread()
    worker = SimplifileBatchProcessor(api_token, submitter_id, recipient_id)
    worker.moveToThread(thread)
    
    # Connect thread started signal to avoid direct function calls across threads
    thread.started.connect(lambda: worker.process_batch(excel_path, deeds_path, mortgage_path, preview_mode, affidavits_path))
    
    # Connect cleanup signals
    worker.finished.connect(lambda: thread.quit())
    worker.error.connect(lambda e: thread.quit())
    
    # Use deleteLater to ensure proper cleanup
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker

def run_simplifile_batch_thread(api_token, submitter_id, recipient_id, excel_path, deeds_path, mortgage_path, affidavits_path=None):
    """Create and run a thread for Simplifile batch operations with actual API upload"""
    thread = QThread()
    worker = SimplifileBatchProcessor(api_token, submitter_id, recipient_id)
    worker.moveToThread(thread)
    
    # Connect thread started signal to avoid direct function calls across threads
    thread.started.connect(lambda: worker.process_batch(excel_path, deeds_path, mortgage_path, False, affidavits_path))
    
    # Connect cleanup signals
    worker.finished.connect(lambda: thread.quit())
    worker.error.connect(lambda e: thread.quit())
    
    # Use deleteLater to ensure proper cleanup
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker