import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
import json
import requests
import base64
from io import StringIO

class SimplifileBatchPreview(QObject):
    """Generate a preview of batch processing without hitting the API"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    preview_ready = pyqtSignal(str)  # JSON string of preview data
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        
    def generate_preview(self, excel_path, deeds_path, mortgage_path):
        """Generate a preview of the batch processing"""
        try:
            self.status.emit("Starting preview generation...")
            self.progress.emit(5)
            
            # Load Excel data
            if not excel_path:
                self.error.emit("Excel file is required for preview")
                return False
                
            excel_data = self.load_excel_data(excel_path)
            if excel_data is None:
                return False
            
            self.progress.emit(20)
            
            # Generate preview of PDF splits without actually creating files
            deed_splits = []
            mortgage_splits = []
            
            if deeds_path:
                self.status.emit("Analyzing deed documents...")
                deed_splits = self.preview_deed_splits(deeds_path)
                if not deed_splits and deeds_path:
                    self.error.emit("Failed to analyze deed documents")
                    return False
            
            self.progress.emit(40)
            
            if mortgage_path:
                self.status.emit("Analyzing mortgage satisfaction documents...")
                mortgage_splits = self.preview_mortgage_splits(mortgage_path)
                if not mortgage_splits and mortgage_path:
                    self.error.emit("Failed to analyze mortgage satisfaction documents")
                    return False
            
            self.progress.emit(60)
            
            # Create preview data
            preview_data = self.build_preview_data(excel_data, deed_splits, mortgage_splits)
            if not preview_data:
                self.error.emit("Failed to create preview data")
                return False
            
            self.progress.emit(80)
            
            # Convert to JSON string
            preview_json = json.dumps(preview_data, indent=2)
            
            self.status.emit("Preview generation completed successfully")
            self.progress.emit(100)
            self.preview_ready.emit(preview_json)
            return True
            
        except Exception as e:
            self.error.emit(f"Error in preview generation: {str(e)}")
            return False
    
    def load_excel_data(self, excel_path):
        """Load Excel data for preview"""
        try:
            self.status.emit(f"Loading Excel data from {os.path.basename(excel_path)}...")
            excel_data = pd.read_excel(excel_path)
            
            # Verify required columns
            required_columns = ['Account']
            recommended_columns = ['Last Name #1', 'First Name #1', 'Last Name #2', 'First Name #2', 
                                  'Deed Book', 'Deed Page', 'Mortgage Book', 'Mortgage Page', 'TMS #']
            
            missing_required = [col for col in required_columns if col not in excel_data.columns]
            missing_recommended = [col for col in recommended_columns if col not in excel_data.columns]
            
            if missing_required:
                self.error.emit(f"Missing required columns in Excel: {', '.join(missing_required)}")
                return None
            
            if missing_recommended:
                self.status.emit(f"Warning: Some recommended columns are missing: {', '.join(missing_recommended)}")
            
            # Check for empty cells in required columns
            empty_rows = excel_data[excel_data['Account'].isna()].index.tolist()
            if empty_rows:
                self.status.emit(f"Warning: Empty account numbers in rows: {', '.join(map(str, [i+2 for i in empty_rows]))}")
            
            self.status.emit(f"Excel data loaded: {len(excel_data)} records")
            return excel_data
            
        except Exception as e:
            self.error.emit(f"Error loading Excel file: {str(e)}")
            return None
    
    def preview_deed_splits(self, pdf_path):
        """Analyze deed PDF to determine how it would be split (without creating files)"""
        try:
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            pages_per_doc = 4  # Deeds are 4 pages each
            doc_count = (total_pages + pages_per_doc - 1) // pages_per_doc  # Ceiling division
            
            self.status.emit(f"Deed PDF contains {total_pages} pages which would be split into {doc_count} documents (4 pages each)")
            
            # Create split information
            deed_splits = []
            for i in range(doc_count):
                start_page = i * pages_per_doc
                end_page = min(start_page + pages_per_doc, total_pages)
                
                deed_splits.append({
                    "index": i,
                    "start_page": start_page + 1,  # 1-based for display
                    "end_page": end_page,
                    "page_count": end_page - start_page,
                    "type": "Deed - Timeshare"
                })
            
            return deed_splits
            
        except Exception as e:
            self.error.emit(f"Error analyzing deed PDF: {str(e)}")
            return []
    
    def preview_mortgage_splits(self, pdf_path):
        """Analyze mortgage PDF to determine how it would be split (without creating files)"""
        try:
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            
            self.status.emit(f"Mortgage PDF contains {total_pages} pages which would become {total_pages} individual documents (1 page each)")
            
            # Create split information 
            mortgage_splits = []
            for i in range(total_pages):
                mortgage_splits.append({
                    "index": i,
                    "start_page": i + 1,  # 1-based for display
                    "end_page": i + 1,
                    "page_count": 1,
                    "type": "Mortgage Satisfaction"
                })
            
            return mortgage_splits
            
        except Exception as e:
            self.error.emit(f"Error analyzing mortgage PDF: {str(e)}")
            return []
    
    def build_preview_data(self, excel_data, deed_splits, mortgage_splits):
        """Build preview data structure"""
        try:
            # Count how many packages will be created
            total_packages = max(len(deed_splits), len(mortgage_splits))
            if total_packages == 0:
                self.error.emit("No documents to process in preview")
                return None
            
            # How many Excel rows we have to work with
            total_rows = len(excel_data)
            
            if total_rows < total_packages:
                self.status.emit(f"Warning: Excel has fewer rows ({total_rows}) than documents to be created ({total_packages})")
            
            preview_data = {
                "summary": {
                    "total_packages": total_packages,
                    "deed_documents": len(deed_splits),
                    "mortgage_documents": len(mortgage_splits),
                    "excel_rows": total_rows
                },
                "packages": []
            }
            
            # Create package previews
            for i in range(min(total_packages, total_rows)):
                row = excel_data.iloc[i]
                
                # Get data from Excel
                account_number = str(row.get('Account', ''))
                
                # Get name data, handling cases where columns might not exist
                last_name1 = str(row.get('Last Name #1', '')) if 'Last Name #1' in row else ''
                first_name1 = str(row.get('First Name #1', '')) if 'First Name #1' in row else ''
                last_name2 = str(row.get('Last Name #2', '')) if 'Last Name #2' in row else ''
                first_name2 = str(row.get('First Name #2', '')) if 'First Name #2' in row else ''
                
                # Get book/page data
                deed_book = str(row.get('Deed Book', '')) if 'Deed Book' in row else ''
                deed_page = str(row.get('Deed Page', '')) if 'Deed Page' in row else ''
                mortgage_book = str(row.get('Mortgage Book', '')) if 'Mortgage Book' in row else ''
                mortgage_page = str(row.get('Mortgage Page', '')) if 'Mortgage Page' in row else ''
                tms = str(row.get('TMS #', '')) if 'TMS #' in row else ''
                
                # Prepare package data
                package = {
                    "package_id": f"P-{account_number}",
                    "package_name": f"{account_number} {last_name1}",
                    "excel_row": i + 2,  # Excel row (1-based, with header)
                    "account_number": account_number,
                    "grantor_name1": f"{first_name1} {last_name1}".strip(),
                    "grantor_name2": f"{first_name2} {last_name2}".strip() if first_name2 or last_name2 else None,
                    "tms_number": tms,
                    "documents": []
                }
                
                # Add deed document if available for this index
                if i < len(deed_splits):
                    deed = deed_splits[i]
                    package["documents"].append({
                        "document_id": f"D-{account_number}-TD",
                        "name": f"{account_number} {last_name1} TD",
                        "type": deed["type"],
                        "page_range": f"{deed['start_page']}-{deed['end_page']}",
                        "page_count": deed["page_count"],
                        "reference_book": deed_book,
                        "reference_page": deed_page,
                        "legal_description": "ANDERSON OCEAN CLUB HPR U/W",
                        "parcel_id": tms,
                        "consideration": "0.00"
                    })
                
                # Add mortgage document if available for this index
                if i < len(mortgage_splits):
                    mortgage = mortgage_splits[i]
                    package["documents"].append({
                        "document_id": f"D-{account_number}-SAT",
                        "name": f"{account_number} {last_name1} SAT",
                        "type": mortgage["type"],
                        "page_range": f"{mortgage['start_page']}-{mortgage['end_page']}",
                        "page_count": mortgage["page_count"],
                        "reference_book": mortgage_book,
                        "reference_page": mortgage_page,
                        "legal_description": "ANDERSON OCEAN CLUB HPR U/W" if deed_book else "",
                        "parcel_id": tms
                    })
                
                preview_data["packages"].append(package)
            
            return preview_data
            
        except Exception as e:
            self.error.emit(f"Error building preview data: {str(e)}")
            return None


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
        self.temp_dir = tempfile.mkdtemp()
        self.preview_mode = True  # Default to preview mode
        
    def process_batch(self, excel_path, deeds_path, mortgage_path, preview_mode=True):
        """Process batch upload"""
        try:
            self.preview_mode = preview_mode
            self.status.emit("Starting batch process...")
            self.progress.emit(5)
            
            # Load Excel data
            excel_data = self.load_excel_data(excel_path)
            if excel_data is None:
                return False
            
            # Process PDF files
            deed_files = []
            mortgage_files = []
            
            if deeds_path:
                self.status.emit("Processing deed documents...")
                deed_files = self.split_deeds_pdf(deeds_path)
                if not deed_files and deeds_path:
                    self.error.emit("Failed to process deed documents")
                    return False
            
            if mortgage_path:
                self.status.emit("Processing mortgage satisfaction documents...")
                mortgage_files = self.split_mortgage_pdf(mortgage_path)
                if not mortgage_files and mortgage_path:
                    self.error.emit("Failed to process mortgage satisfaction documents")
                    return False
            
            # Match Excel data with PDF files and prepare upload packages
            self.status.emit("Preparing packages...")
            
            packages = self.prepare_packages(excel_data, deed_files, mortgage_files)
            if not packages:
                self.error.emit("Failed to prepare packages")
                return False
            
            # In preview mode, just return the packages without uploading
            if self.preview_mode:
                package_info = {
                    "resultCode": "SUCCESS",
                    "message": "Batch processing preview completed",
                    "packages": packages
                }
                    
                self.status.emit("Batch processing preview completed successfully")
                self.progress.emit(100)
                self.finished.emit(package_info)
            else:
                # In actual upload mode, send packages to API
                if not self.api_token or not self.submitter_id or not self.recipient_id:
                    self.error.emit("Missing API credentials. Cannot proceed with upload.")
                    return False
                
                self.status.emit("Starting actual API upload process...")
                upload_results = self.upload_packages_to_api(packages)
                
                # Report results
                self.status.emit("API upload process completed")
                self.progress.emit(100)
                self.finished.emit(upload_results)
            
            # Cleanup temporary files
            self.cleanup_temp_files()
            
            return True
            
        except Exception as e:
            self.error.emit(f"Error in batch processing: {str(e)}")
            return False
    
    def load_excel_data(self, excel_path):
        """Load and validate Excel data"""
        try:
            self.status.emit(f"Loading Excel data from {os.path.basename(excel_path)}...")
            excel_data = pd.read_excel(excel_path)
            
            # Check if Excel has required columns
            required_columns = ['Account']
            recommended_columns = ['Last Name #1', 'First Name #1']
            
            missing_required = [col for col in required_columns if col not in excel_data.columns]
            missing_recommended = [col for col in recommended_columns if col not in excel_data.columns]
            
            if missing_required:
                self.error.emit(f"Missing required columns in Excel: {', '.join(missing_required)}")
                return None
            
            if missing_recommended:
                self.status.emit(f"Warning: Some recommended columns are missing: {', '.join(missing_recommended)}")
            
            self.status.emit(f"Excel data loaded: {len(excel_data)} records")
            return excel_data
            
        except Exception as e:
            self.error.emit(f"Error loading Excel file: {str(e)}")
            return None
    
    def split_deeds_pdf(self, pdf_path):
        """Split deed document PDF into individual files (every 4 pages)"""
        try:
            deed_files = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            pages_per_doc = 4  # Deeds are 4 pages each
            doc_count = (total_pages + pages_per_doc - 1) // pages_per_doc  # Ceiling division
            
            self.status.emit(f"Splitting {total_pages} pages into {doc_count} deed documents...")
            
            for i in range(doc_count):
                start_page = i * pages_per_doc
                end_page = min(start_page + pages_per_doc, total_pages)
                
                # Create a new PDF writer for this chunk
                output_pdf = PdfWriter()
                
                # Add pages from the original document
                for page_num in range(start_page, end_page):
                    output_pdf.add_page(pdf.pages[page_num])
                
                # Save the split document
                output_path = os.path.join(self.temp_dir, f"deed_{i+1}.pdf")
                with open(output_path, "wb") as output_file:
                    output_pdf.write(output_file)
                
                deed_files.append({
                    "index": i,
                    "path": output_path,
                    "type": "Deed - Timeshare"
                })
                
                self.progress.emit(10 + (i * 30 // doc_count))
            
            self.status.emit(f"Created {len(deed_files)} deed documents")
            return deed_files
            
        except Exception as e:
            self.error.emit(f"Error splitting deed PDF: {str(e)}")
            return []
    
    def split_mortgage_pdf(self, pdf_path):
        """Split mortgage satisfaction PDF into individual files (1 page per document)"""
        try:
            mortgage_files = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            
            self.status.emit(f"Splitting {total_pages} mortgage satisfaction pages...")
            
            for i in range(total_pages):
                # Create a new PDF writer for this page
                output_pdf = PdfWriter()
                
                # Add just this page
                output_pdf.add_page(pdf.pages[i])
                
                # Save the split document
                output_path = os.path.join(self.temp_dir, f"mortgage_{i+1}.pdf")
                with open(output_path, "wb") as output_file:
                    output_pdf.write(output_file)
                
                mortgage_files.append({
                    "index": i,
                    "path": output_path,
                    "type": "Mortgage Satisfaction"
                })
                
                self.progress.emit(40 + (i * 30 // total_pages))
            
            self.status.emit(f"Created {len(mortgage_files)} mortgage satisfaction documents")
            return mortgage_files
            
        except Exception as e:
            self.error.emit(f"Error splitting mortgage PDF: {str(e)}")
            return []
    
    def prepare_packages(self, excel_data, deed_files, mortgage_files):
        """Prepare packages for upload (without actually uploading)"""
        try:
            total_rows = len(excel_data)
            total_packages = max(len(deed_files), len(mortgage_files))
            
            if total_packages == 0:
                self.error.emit("No documents to process")
                return []
            
            if total_rows < total_packages:
                self.status.emit(f"Warning: Excel has fewer rows ({total_rows}) than documents ({total_packages})")
            
            packages = []
            
            # Process each row from Excel with corresponding PDFs
            for i in range(min(total_rows, total_packages)):
                row = excel_data.iloc[i]
                
                # Get account number and last name from Excel
                account_number = str(row.get('Account', ''))
                last_name = str(row.get('Last Name #1', '')) if 'Last Name #1' in row else ''
                first_name = str(row.get('First Name #1', '')) if 'First Name #1' in row else ''
                
                # Add second person if available
                last_name2 = str(row.get('Last Name #2', '')) if 'Last Name #2' in row else ''
                first_name2 = str(row.get('First Name #2', '')) if 'First Name #2' in row else ''
                
                # Get book/page references if available
                deed_book = str(row.get('Deed Book', '')) if 'Deed Book' in row else ''
                deed_page = str(row.get('Deed Page', '')) if 'Deed Page' in row else ''
                tms = str(row.get('TMS #', '')) if 'TMS #' in row else ''
                
                self.status.emit(f"Preparing package {i+1}/{total_packages}: {account_number} {last_name}")
                
                # Prepare documents for this package
                package_docs = []
                
                # Prepare grantor list for deeds
                grantors = []
                
                # Add default grantors (organizations)
                grantors.append({
                    "type": "ORGANIZATION",
                    "nameUnparsed": "KING CUNNINGHAM LLC TR"
                })
                grantors.append({
                    "type": "ORGANIZATION",
                    "nameUnparsed": "OCEAN CLUB VACATIONS LLC"
                })
                
                # Add person grantors if available
                if first_name and last_name:
                    grantors.append({
                        "type": "Individual",
                        "firstName": first_name.upper(),
                        "lastName": last_name.upper()
                    })
                
                if first_name2 and last_name2:
                    grantors.append({
                        "type": "Individual",
                        "firstName": first_name2.upper(),
                        "lastName": last_name2.upper()
                    })
                
                # Default grantees
                grantees = [{
                    "type": "ORGANIZATION",
                    "nameUnparsed": "OCEAN CLUB VACATIONS LLC"
                }]
                
                # Add deed document if available
                if i < len(deed_files):
                    deed = deed_files[i]
                    
                    # Reference information for deed
                    reference_info = None
                    if deed_book and deed_page:
                        reference_info = [{
                            "documentType": "Deed - Timeshare",
                            "book": deed_book,
                            "page": int(deed_page) if deed_page.isdigit() else 0
                        }]
                    
                    deed_doc = {
                        "file_path": deed["path"],
                        "document_id": f"D-{account_number}-TD",
                        "name": f"{account_number} {last_name} TD",
                        "type": deed["type"],
                        "consideration": "0.00",
                        "execution_date": datetime.now().strftime('%m/%d/%Y'),
                        "legal_description": "ANDERSON OCEAN CLUB HPR U/W",
                        "parcel_id": tms,
                        "grantors": grantors,
                        "grantees": grantees,
                        "reference_info": reference_info
                    }
                    
                    package_docs.append(deed_doc)
                
                # Add mortgage satisfaction document if available
                if i < len(mortgage_files):
                    mortgage = mortgage_files[i]
                    
                    # Reference info for mortgage
                    mortgage_book = str(row.get('Mortgage Book', '')) if 'Mortgage Book' in row else ''
                    mortgage_page = str(row.get('Mortgage Page', '')) if 'Mortgage Page' in row else ''
                    
                    reference_info = None
                    if mortgage_book and mortgage_page:
                        reference_info = [{
                            "documentType": "Mortgage",
                            "book": mortgage_book,
                            "page": int(mortgage_page) if mortgage_page.isdigit() else 0
                        }]
                    
                    mortgage_doc = {
                        "file_path": mortgage["path"],
                        "document_id": f"D-{account_number}-SAT",
                        "name": f"{account_number} {last_name} SAT",
                        "type": mortgage["type"],
                        "execution_date": datetime.now().strftime('%m/%d/%Y'),
                        "legal_description": "ANDERSON OCEAN CLUB HPR U/W" if reference_info else "",
                        "parcel_id": tms,
                        "grantors": grantors,
                        "grantees": grantees,
                        "reference_info": reference_info
                    }
                    
                    package_docs.append(mortgage_doc)
                
                # Create package info
                package = {
                    "package_id": f"P-{account_number}",
                    "package_name": f"Package {account_number} {last_name}",
                    "documents": package_docs,
                    "excel_row": i + 2  # Excel row (1-based, with header)
                }
                
                packages.append(package)
                
                self.progress.emit(70 + (i * 25 // total_packages))
            
            self.status.emit(f"Prepared {len(packages)} packages")
            return packages
            
        except Exception as e:
            self.error.emit(f"Error preparing packages: {str(e)}")
            return []
    
    def encode_file(self, file_path):
        """Convert a file to base64 encoding"""
        try:
            with open(file_path, "rb") as file:
                encoded_data = base64.b64encode(file.read()).decode('utf-8')
                return encoded_data
        except Exception as e:
            self.error.emit(f"Error encoding file {os.path.basename(file_path)}: {str(e)}")
            return None
    
    def upload_packages_to_api(self, packages):
        """Upload packages to Simplifile API"""
        try:
            self.status.emit("Starting API upload process...")
            
            # Prepare results structure
            results = {
                "resultCode": "SUCCESS",
                "message": "Packages uploaded to Simplifile API",
                "packages": [],
                "summary": {
                    "total": len(packages),
                    "successful": 0,
                    "failed": 0
                }
            }
            
            # Process each package
            for i, package in enumerate(packages):
                package_name = package["package_name"]
                package_id = package["package_id"]
                documents = package["documents"]
                
                self.status.emit(f"Uploading package {i+1}/{len(packages)}: {package_name}")
                self.progress.emit(70 + (i * 30 // len(packages)))
                
                # Create API payload for this package
                payload = self.create_api_payload(package)
                
                # If we're in preview mode, don't actually hit the API
                if self.preview_mode:
                    results["packages"].append({
                        "package_id": package_id,
                        "status": "preview_success",
                        "message": "Package prepared (preview mode)",
                        "package_name": package_name,
                        "document_count": len(documents)
                    })
                    results["summary"]["successful"] += 1
                    continue
                
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
                        data=json.dumps(payload),
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
                            error_msg = response_data.get("message", "Unknown API error")
                            results["packages"].append({
                                "package_id": package_id,
                                "status": "api_error",
                                "message": error_msg,
                                "package_name": package_name,
                                "document_count": len(documents),
                                "api_response": response_data
                            })
                            results["summary"]["failed"] += 1
                    else:
                        results["packages"].append({
                            "package_id": package_id,
                            "status": "http_error",
                            "message": f"HTTP error {response.status_code}",
                            "package_name": package_name,
                            "document_count": len(documents)
                        })
                        results["summary"]["failed"] += 1
                
                except Exception as e:
                    results["packages"].append({
                        "package_id": package_id,
                        "status": "exception",
                        "message": str(e),
                        "package_name": package_name,
                        "document_count": len(documents)
                    })
                    results["summary"]["failed"] += 1
            
            # Update final status
            if results["summary"]["failed"] > 0:
                if results["summary"]["successful"] > 0:
                    results["resultCode"] = "PARTIAL_SUCCESS"
                    results["message"] = f"Completed with {results['summary']['successful']} successful and {results['summary']['failed']} failed packages"
                else:
                    results["resultCode"] = "FAILED"
                    results["message"] = "All packages failed to upload"
            
            return results
            
        except Exception as e:
            self.error.emit(f"Error in API upload process: {str(e)}")
            return {
                "resultCode": "ERROR",
                "message": f"Error in upload process: {str(e)}",
                "packages": []
            }
    
    def create_api_payload(self, package):
        """Create API payload for a single package"""
        package_id = package["package_id"]
        package_name = package["package_name"]
        documents = package["documents"]
        
        # Create payload structure
        payload = {
            "documents": [],
            "recipient": self.recipient_id,
            "submitterPackageID": package_id,
            "name": package_name,
            "operations": {
                "draftOnErrors": True,
                "submitImmediately": False,
                "verifyPageMargins": True
            }
        }
        
        # Process each document
        for doc in documents:
            # Encode document file
            encoded_file = self.encode_file(doc["file_path"])
            if not encoded_file:
                continue
            
            # Prepare document entry
            document = {
                "submitterDocumentID": doc["document_id"],
                "name": doc["name"].upper(),
                "kindOfInstrument": [doc["type"]],
                "indexingData": {
                    "consideration": doc.get("consideration", "0.00"),
                    "executionDate": doc.get("execution_date", datetime.now().strftime('%m/%d/%Y')),
                    "grantors": doc.get("grantors", []),
                    "grantees": doc.get("grantees", []),
                    "legalDescriptions": [
                        {
                            "description": doc.get("legal_description", "").upper(),
                            "parcelId": doc.get("parcel_id", "").upper()
                        }
                    ]
                },
                "fileBytes": [encoded_file]
            }
            
            # Add reference information if available
            if "reference_info" in doc and doc["reference_info"]:
                document["indexingData"]["referenceInfo"] = doc["reference_info"]
            
            payload["documents"].append(document)
        
        return payload
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            self.status.emit("Cleaning up temporary files...")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            self.status.emit(f"Warning: Error cleaning up temporary files: {str(e)}")


def run_simplifile_batch_preview(excel_path, deeds_path, mortgage_path):
    """Create and run a thread for Simplifile batch preview"""
    thread = QThread()
    worker = SimplifileBatchPreview()
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(lambda: worker.generate_preview(excel_path, deeds_path, mortgage_path))
    worker.preview_ready.connect(thread.quit)
    worker.error.connect(lambda e: thread.quit())
    worker.preview_ready.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker


def run_simplifile_batch_process(excel_path, deeds_path, mortgage_path, api_token=None, submitter_id=None, recipient_id=None, preview_mode=True):
    """Create and run a thread for Simplifile batch processing"""
    thread = QThread()
    worker = SimplifileBatchProcessor(api_token, submitter_id, recipient_id)
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(lambda: worker.process_batch(excel_path, deeds_path, mortgage_path, preview_mode))
    worker.finished.connect(thread.quit)
    worker.error.connect(lambda e: thread.quit())
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker

def run_simplifile_batch_thread(api_token, submitter_id, recipient_id, excel_path, deeds_path, mortgage_path):
    """Create and run a thread for Simplifile batch operations"""
    thread = QThread()
    worker = SimplifileBatchProcessor(api_token, submitter_id, recipient_id)
    worker.moveToThread(thread)
    
    # Connect signals
    thread.started.connect(lambda: worker.process_batch(excel_path, deeds_path, mortgage_path))
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    
    return thread, worker