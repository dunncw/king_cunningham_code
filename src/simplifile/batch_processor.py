import os
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from datetime import datetime
import json
import requests
import base64

from .api import SimplifileAPI

class SimplifileBatchPreview(QObject):
    """Generate a comprehensive preview of batch processing without hitting the API"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    preview_ready = pyqtSignal(str)  # JSON string of preview data
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        
    def generate_preview(self, excel_path, deeds_path, mortgage_path):
        """Generate an enhanced preview of the batch processing"""
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
            
            # Create comprehensive preview data
            preview_data = self.build_enhanced_preview_data(excel_data, deed_splits, mortgage_splits)
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
        """Load Excel data with enhanced validation"""
        try:
            self.status.emit(f"Loading Excel data from {os.path.basename(excel_path)}...")
            excel_data = pd.read_excel(excel_path)
            
            # Check for required columns according to instructions
            required_columns = [
                'KC File No.', 'Account', 'Last Name #1', 'First Name #1'
            ]
            
            recommended_columns = [
                'Deed Book', 'Deed Page', 'Mortgage Book', 'Mortgage Page', 
                'Execution Date', 'GRANTOR/GRANTEE', 'LEGAL DESCRIPTION',
                'Suite', 'Consideration', '&', 'Last Name #2', 'First Name #2'
            ]
            
            missing_required = [col for col in required_columns if col not in excel_data.columns]
            missing_recommended = [col for col in recommended_columns if col not in excel_data.columns]
            
            if missing_required:
                self.error.emit(f"Missing required columns in Excel: {', '.join(missing_required)}")
                return None
            
            if missing_recommended:
                self.missing_recommended_columns = missing_recommended
                self.status.emit(f"Warning: Some recommended columns are missing: {', '.join(missing_recommended)}")
            else:
                self.missing_recommended_columns = []
            
            # Check for empty cells in required columns
            empty_rows = excel_data[excel_data['Account'].isna()].index.tolist()
            if empty_rows:
                self.status.emit(f"Warning: Empty account numbers in rows: {', '.join(map(str, [i+2 for i in empty_rows]))}")
            
            # Format validation for key columns
            validation_warnings = []
            
            # Check if names are in ALL CAPS as required
            if 'Last Name #1' in excel_data.columns:
                for idx, value in excel_data['Last Name #1'].items():
                    if isinstance(value, str) and value != value.upper():
                        validation_warnings.append(f"Row {idx+2}: Last name '{value}' is not in ALL CAPS")
            
            if 'First Name #1' in excel_data.columns:
                for idx, value in excel_data['First Name #1'].items():
                    if isinstance(value, str) and value != value.upper():
                        validation_warnings.append(f"Row {idx+2}: First name '{value}' is not in ALL CAPS")
            
            # Report validation warnings
            if validation_warnings:
                self.status.emit(f"Found {len(validation_warnings)} formatting issues in Excel data.")
                for i, warning in enumerate(validation_warnings[:5]):  # Show first 5 warnings
                    self.status.emit(f"Warning: {warning}")
                if len(validation_warnings) > 5:
                    self.status.emit(f"... and {len(validation_warnings) - 5} more issues.")
            
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
            
            # Create enhanced split information
            deed_splits = []
            for i in range(doc_count):
                start_page = i * pages_per_doc
                end_page = min(start_page + pages_per_doc, total_pages)
                
                # Try to extract some text from first page for identification
                sample_text = ""
                if start_page < total_pages:
                    try:
                        page = pdf.pages[start_page]
                        sample_text = page.extract_text()[:100] if hasattr(page, 'extract_text') else ""
                        sample_text = sample_text.replace('\n', ' ').strip()
                    except:
                        sample_text = "Text extraction failed"
                
                deed_splits.append({
                    "index": i,
                    "start_page": start_page + 1,  # 1-based for display
                    "end_page": end_page,
                    "page_count": end_page - start_page,
                    "type": "Deed - Timeshare",
                    "sample_text": sample_text,
                    "file_size_kb": "~25-50KB"  # Estimated size after split
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
            
            # Create enhanced split information with text samples
            mortgage_splits = []
            for i in range(total_pages):
                # Try to extract some text for identification
                sample_text = ""
                try:
                    page = pdf.pages[i]
                    sample_text = page.extract_text()[:100] if hasattr(page, 'extract_text') else ""
                    sample_text = sample_text.replace('\n', ' ').strip()
                except:
                    sample_text = "Text extraction failed"
                    
                mortgage_splits.append({
                    "index": i,
                    "start_page": i + 1,  # 1-based for display
                    "end_page": i + 1,
                    "page_count": 1,
                    "type": "Mortgage Satisfaction",
                    "sample_text": sample_text,
                    "file_size_kb": "~10-15KB"  # Estimated size
                })
            
            return mortgage_splits
            
        except Exception as e:
            self.error.emit(f"Error analyzing mortgage PDF: {str(e)}")
            return []
    
    def format_name(self, name):
        """Format names according to requirements (uppercase, no hyphens)"""
        if not isinstance(name, str):
            return ""
        # Convert to uppercase
        name = name.upper()
        # Remove hyphens as specified in the guide
        name = name.replace('-', ' ')
        return name
    
    def build_enhanced_preview_data(self, excel_data, deed_splits, mortgage_splits):
        """Build comprehensive preview data structure with validation information"""
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
            
            # Create summary with more detailed information
            preview_data = {
                "summary": {
                    "total_packages": min(total_rows, total_packages),
                    "deed_documents": len(deed_splits),
                    "mortgage_documents": len(mortgage_splits),
                    "excel_rows": total_rows,
                    "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "warnings": []
                },
                "packages": [],
                "validation": {
                    "missing_data": [],
                    "format_issues": [],
                    "document_issues": []
                }
            }
            
            # Add this to the beginning of the method, right after declaring preview_data
            if hasattr(self, 'missing_recommended_columns') and self.missing_recommended_columns:
                preview_data["validation"]["format_issues"].extend([
                    f"Missing recommended column: {col}" for col in self.missing_recommended_columns
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
            
            # Create enhanced package previews
            for i in range(min(total_packages, total_rows)):
                row = excel_data.iloc[i]
                
                # Get essential data from Excel with proper error handling
                def get_cell_value(column, default=""):
                    try:
                        if column in row and pd.notna(row[column]):
                            return str(row[column])
                        return default
                    except:
                        return default
                
                # Extract all relevant data
                kc_file_no = get_cell_value('KC File No.')
                account_number = get_cell_value('Account')
                
                # Name data with formatting
                last_name1 = self.format_name(get_cell_value('Last Name #1'))
                first_name1 = self.format_name(get_cell_value('First Name #1'))
                
                # Check for second owner
                has_second_owner = '&' in get_cell_value('&', '')
                last_name2 = self.format_name(get_cell_value('Last Name #2')) if has_second_owner else ''
                first_name2 = self.format_name(get_cell_value('First Name #2')) if has_second_owner else ''
                
                # Reference data
                deed_book = get_cell_value('Deed Book')
                deed_page = get_cell_value('Deed Page')
                mortgage_book = get_cell_value('Mortgage Book')
                mortgage_page = get_cell_value('Mortgage Page')
                
                # Other fields
                suite = get_cell_value('Suite')
                consideration = get_cell_value('Consideration', '0.00')
                execution_date = get_cell_value('Execution Date', datetime.now().strftime('%m/%d/%Y'))
                grantor_grantee = self.format_name(get_cell_value('GRANTOR/GRANTEE', 'OCEAN CLUB VACATIONS LLC'))
                legal_description = self.format_name(get_cell_value('LEGAL DESCRIPTION', 'ANDERSON OCEAN CLUB HPR'))
                
                # Set package name following convention
                package_name = f"{account_number} {last_name1} TD {kc_file_no}"
                
                # Create enhanced package information
                package = {
                    "package_id": f"P-{account_number}",
                    "package_name": package_name,
                    "excel_row": i + 2,  # Excel row (1-based, with header)
                    "account_number": account_number,
                    "kc_file_no": kc_file_no,
                    "grantor_name1": f"{first_name1} {last_name1}".strip(),
                    "grantor_name2": f"{first_name2} {last_name2}".strip() if first_name2 or last_name2 else None,
                    "has_second_owner": has_second_owner,
                    "tms_number": suite,
                    "consideration": consideration,
                    "execution_date": execution_date,
                    "grantor_grantee": grantor_grantee,
                    "legal_description": legal_description,
                    "documents": [],
                    "validated": True,  # Will be set to False if issues found
                    "validation_issues": []
                }
                
                # Basic validation for this package
                if not account_number:
                    package["validated"] = False
                    package["validation_issues"].append("Missing account number")
                    preview_data["validation"]["missing_data"].append(
                        f"Row {i+2}: Missing account number"
                    )
                
                if not last_name1 or not first_name1:
                    package["validated"] = False
                    package["validation_issues"].append("Missing primary owner name")
                    preview_data["validation"]["missing_data"].append(
                        f"Row {i+2}: Missing primary owner name data"
                    )
                
                if has_second_owner and (not last_name2 or not first_name2):
                    package["validated"] = False
                    package["validation_issues"].append("Incomplete secondary owner information")
                    preview_data["validation"]["missing_data"].append(
                        f"Row {i+2}: Incomplete secondary owner information"
                    )
                
                # Add deed document if available for this index
                if i < len(deed_splits):
                    deed = deed_splits[i]
                    
                    deed_doc = {
                        "document_id": f"D-{account_number}-TD",
                        "name": f"{account_number} {last_name1} TD",
                        "type": deed["type"],
                        "page_range": f"{deed['start_page']}-{deed['end_page']}",
                        "page_count": deed["page_count"],
                        "reference_book": deed_book,
                        "reference_page": deed_page,
                        "legal_description": legal_description,
                        "parcel_id": suite,
                        "consideration": consideration,
                        "execution_date": execution_date,
                        "sample_text": deed["sample_text"],
                        "estimated_size": deed["file_size_kb"],
                        "validated": True,
                        "validation_issues": []
                    }
                    
                    # Validate deed document
                    if not deed_book or not deed_page:
                        deed_doc["validated"] = False
                        deed_doc["validation_issues"].append("Missing deed book/page reference")
                        package["validated"] = False
                        preview_data["validation"]["missing_data"].append(
                            f"Row {i+2}: Missing deed book/page reference for document {deed_doc['document_id']}"
                        )
                    
                    package["documents"].append(deed_doc)
                
                # Add mortgage document if available for this index
                if i < len(mortgage_splits):
                    mortgage = mortgage_splits[i]
                    
                    mortgage_doc = {
                        "document_id": f"D-{account_number}-SAT",
                        "name": f"{account_number} {last_name1} SAT",
                        "type": mortgage["type"],
                        "page_range": f"{mortgage['start_page']}-{mortgage['end_page']}",
                        "page_count": mortgage["page_count"],
                        "reference_book": mortgage_book,
                        "reference_page": mortgage_page,
                        "legal_description": legal_description,
                        "parcel_id": suite,
                        "execution_date": execution_date,
                        "sample_text": mortgage["sample_text"],
                        "estimated_size": mortgage["file_size_kb"],
                        "validated": True,
                        "validation_issues": []
                    }
                    
                    # Validate mortgage document
                    if not mortgage_book or not mortgage_page:
                        mortgage_doc["validated"] = False
                        mortgage_doc["validation_issues"].append("Missing mortgage book/page reference")
                        package["validated"] = False
                        preview_data["validation"]["missing_data"].append(
                            f"Row {i+2}: Missing mortgage book/page reference for document {mortgage_doc['document_id']}"
                        )
                    
                    package["documents"].append(mortgage_doc)
                
                # Check if package has both document types
                if i < len(deed_splits) and i >= len(mortgage_splits):
                    package["validation_issues"].append("Missing mortgage satisfaction document")
                    preview_data["validation"]["document_issues"].append(
                        f"Package {package['package_id']}: Missing mortgage satisfaction document"
                    )
                
                if i >= len(deed_splits) and i < len(mortgage_splits):
                    package["validation_issues"].append("Missing deed document")
                    preview_data["validation"]["document_issues"].append(
                        f"Package {package['package_id']}: Missing deed document"
                    )
                
                preview_data["packages"].append(package)
            
            # Add validation summary
            preview_data["validation_summary"] = {
                "total_packages": len(preview_data["packages"]),
                "valid_packages": sum(1 for p in preview_data["packages"] if p.get("validated", False)),
                "invalid_packages": sum(1 for p in preview_data["packages"] if not p.get("validated", False)),
                "missing_data_issues": len(preview_data["validation"]["missing_data"]),
                "format_issues": len(preview_data["validation"]["format_issues"]),
                "document_issues": len(preview_data["validation"]["document_issues"])
            }
            
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
        
    # Updated process_batch function with validation
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
            
            # Validate documents if not in preview mode
            if not self.preview_mode:
                self.status.emit("Validating documents against API requirements...")
                # Create API helper for validation
                api_helper = SimplifileAPI(self.api_token, self.submitter_id, self.recipient_id)
                
                validation_warnings = []
                for i, package in enumerate(packages):
                    for doc in package["documents"]:
                        instrument_type = doc.get("type", "Deed - Timeshare")
                        is_valid, message = api_helper.validate_document(doc, instrument_type)
                        if not is_valid:
                            warning = f"Document {doc['document_id']} in package {package['package_id']} may not be valid: {message}"
                            self.status.emit(f"Warning: {warning}")
                            validation_warnings.append(warning)
                
                if validation_warnings:
                    self.status.emit(f"Found {len(validation_warnings)} validation warnings. Review before submitting.")
            
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
        """Load and validate Excel data according to the required schema"""
        try:
            self.status.emit(f"Loading Excel data from {os.path.basename(excel_path)}...")
            excel_data = pd.read_excel(excel_path)
            
            # Check for required columns
            required_columns = [
                'KC File No.', 'Account', 'Last Name #1', 'First Name #1', 
                'Deed Book', 'Deed Page', 'Recorded Date',
                'Mortgage Book', 'Mortgage Page', 'Consideration', 
                'Execution Date', 'GRANTOR/GRANTEE', 'LEGAL DESCRIPTION'
            ]
            
            # Check which required columns are missing
            missing_required = [col for col in required_columns if col not in excel_data.columns]
            
            if missing_required:
                self.error.emit(f"Missing required columns in Excel: {', '.join(missing_required)}")
                return None
            
            # Validate data in key columns
            empty_accounts = excel_data[excel_data['Account'].isna()].index.tolist()
            if empty_accounts:
                self.error.emit(f"Empty account numbers in rows: {', '.join(map(str, [i+2 for i in empty_accounts]))}")
                return None
            
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
        """Prepare packages following the exact instructions"""
        try:
            total_rows = len(excel_data)
            total_deeds = len(deed_files)
            total_mortgages = len(mortgage_files)
            
            # Determine how many packages we can create
            total_packages = min(total_rows, max(total_deeds, total_mortgages))
            
            if total_packages == 0:
                self.error.emit("No documents to process")
                return []
            
            packages = []
            
            # Process each row from Excel with corresponding PDFs
            for i in range(total_packages):
                row = excel_data.iloc[i]
                
                # Extract required data from Excel with safer accessor
                def get_cell_value(column, default=""):
                    try:
                        if column in row and pd.notna(row[column]):
                            return str(row[column])
                        return default
                    except:
                        return default
                
                # Get essential data from Excel
                kc_file_no = get_cell_value('KC File No.')
                account_number = get_cell_value('Account')
                
                # Name data with proper formatting
                last_name1 = self.format_name(get_cell_value('Last Name #1'))
                first_name1 = self.format_name(get_cell_value('First Name #1'))
                
                # Check for second owner
                has_second_owner = '&' in get_cell_value('&', '')
                last_name2 = self.format_name(get_cell_value('Last Name #2')) if has_second_owner else ''
                first_name2 = self.format_name(get_cell_value('First Name #2')) if has_second_owner else ''
                
                # Reference data
                deed_book = get_cell_value('Deed Book')
                deed_page = get_cell_value('Deed Page')
                mortgage_book = get_cell_value('Mortgage Book')
                mortgage_page = get_cell_value('Mortgage Page')
                
                # Other fields
                suite = get_cell_value('Suite')
                consideration = get_cell_value('Consideration', '0.00')
                execution_date = get_cell_value('Execution Date', datetime.now().strftime('%Y-%m-%d'))
                grantor_grantee = self.format_name(get_cell_value('GRANTOR/GRANTEE', 'OCEAN CLUB VACATIONS LLC'))
                legal_description = self.format_name(get_cell_value('LEGAL DESCRIPTION', 'ANDERSON OCEAN CLUB HPR'))
                
                # Set package name following convention exactly as in instructions
                package_name = f"{account_number} {last_name1} TD {kc_file_no}"
                
                self.status.emit(f"Preparing package {i+1}/{total_packages}: {package_name}")
                
                # Prepare documents for this package
                package_docs = []
                
                # Prepare grantor list for deed documents
                deed_grantors = []
                
                # Add default organization grantors exactly as specified
                deed_grantors.append({
                    "type": "Organization",
                    "nameUnparsed": "KING CUNNINGHAM LLC TR"
                })
                
                # Add GRANTOR/GRANTEE as specified in instructions
                deed_grantors.append({
                    "type": "Organization",
                    "nameUnparsed": grantor_grantee
                })
                
                # Add person grantors (owners)
                if first_name1 and last_name1:
                    deed_grantors.append({
                        "type": "Individual",
                        "firstName": first_name1,
                        "lastName": last_name1
                    })
                
                if has_second_owner and first_name2 and last_name2:
                    deed_grantors.append({
                        "type": "Individual",
                        "firstName": first_name2,
                        "lastName": last_name2
                    })
                
                # Prepare grantor list for mortgage documents (only the person grantors)
                mortgage_grantors = []
                if first_name1 and last_name1:
                    mortgage_grantors.append({
                        "type": "Individual",
                        "firstName": first_name1,
                        "lastName": last_name1
                    })
                
                if has_second_owner and first_name2 and last_name2:
                    mortgage_grantors.append({
                        "type": "Individual",
                        "firstName": first_name2,
                        "lastName": last_name2
                    })
                
                # Default grantee (from GRANTOR/GRANTEE column) as specified
                grantees = [{
                    "type": "Organization",
                    "nameUnparsed": grantor_grantee
                }]
                
                # Add deed document if available
                if i < len(deed_files):
                    deed = deed_files[i]
                    
                    # Document name following convention exactly
                    deed_doc_name = f"{account_number} {last_name1} TD"
                    
                    # Prepare legal descriptions
                    legal_descriptions = [{
                        "description": legal_description,
                        "parcelId": suite if suite else ""
                    }]
                    
                    # Prepare reference information as specified
                    reference_information = []
                    if deed_book and deed_page:
                        reference_information.append({
                            "documentType": "Deed - Timeshare",
                            "book": deed_book,
                            "page": int(deed_page) if deed_page.isdigit() else 0
                        })
                    
                    deed_doc = {
                        "file_path": deed["path"],
                        "document_id": f"D-{account_number}-TD",
                        "name": deed_doc_name,
                        "type": "Deed - Timeshare",
                        "consideration": float(consideration) if consideration.replace('.', '', 1).isdigit() else 0.0,
                        "execution_date": execution_date,
                        "legal_descriptions": legal_descriptions,
                        "grantors": deed_grantors,
                        "grantees": grantees,
                        "reference_information": reference_information
                    }
                    
                    package_docs.append(deed_doc)
                
                # Add mortgage satisfaction document if available
                if i < len(mortgage_files):
                    mortgage = mortgage_files[i]
                    
                    # Document name following convention exactly
                    mortgage_doc_name = f"{account_number} {last_name1} SAT"
                    
                    # Prepare reference information
                    reference_information = []
                    if mortgage_book and mortgage_page:
                        reference_information.append({
                            "documentType": "Mortgage Satisfaction",
                            "book": mortgage_book,
                            "page": int(mortgage_page) if mortgage_page.isdigit() else 0
                        })
                    
                    # Prepare legal descriptions
                    legal_descriptions = [{
                        "description": legal_description,
                        "parcelId": suite if suite else ""
                    }]
                    
                    mortgage_doc = {
                        "file_path": mortgage["path"],
                        "document_id": f"D-{account_number}-SAT",
                        "name": mortgage_doc_name,
                        "type": "Mortgage Satisfaction",
                        "execution_date": execution_date,
                        "legal_descriptions": legal_descriptions,
                        "grantors": mortgage_grantors,
                        "grantees": grantees,
                        "reference_information": reference_information
                    }
                    
                    package_docs.append(mortgage_doc)
                
                # Create package info with proper settings as specified
                package = {
                    "package_id": f"P-{account_number}",
                    "package_name": package_name,
                    "documents": package_docs,
                    "excel_row": i + 2,  # Excel row (1-based, with header)
                    "draft_on_errors": True,
                    "submit_immediately": False,  # Never auto-submit as per instructions
                    "verify_page_margins": True
                }
                
                packages.append(package)
                
                self.progress.emit(70 + (i * 25 // total_packages))
            
            self.status.emit(f"Prepared {len(packages)} packages")
            return packages
                
        except Exception as e:
            self.error.emit(f"Error preparing packages: {str(e)}")
            return []
            
    def format_name(self, name):
        """Format names according to requirements"""
        if not isinstance(name, str):
            return ""
        # Convert to uppercase
        name = name.upper()
        # Remove hyphens as specified in the guide
        name = name.replace('-', ' ')
        return name
    
    def encode_file(self, file_path):
        """Convert a file to base64 encoding"""
        try:
            with open(file_path, "rb") as file:
                encoded_data = base64.b64encode(file.read()).decode('utf-8')
                return encoded_data
        except Exception as e:
            self.error.emit(f"Error encoding file {os.path.basename(file_path)}: {str(e)}")
            return None
    
    # Updated upload_packages_to_api with improved error handling

    def upload_packages_to_api(self, packages):
        """Upload packages to Simplifile API with improved error handling"""
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
                            error_details = ""
                            
                            # Extract more detailed error information if available
                            if "errors" in response_data:
                                errors_list = []
                                for err in response_data.get("errors", []):
                                    error_path = err.get("path", "")
                                    error_message = err.get("message", "")
                                    errors_list.append(f"{error_path}: {error_message}")
                                error_details = "; ".join(errors_list)
                                
                            # Log the full response for debugging
                            detailed_error = f"API Error: {error_msg}\nDetails: {error_details}\nFull response: {json.dumps(response_data, indent=2)}"
                            self.status.emit(detailed_error)
                                
                            results["packages"].append({
                                "package_id": package_id,
                                "status": "api_error",
                                "message": f"{error_msg} - {error_details}".strip(" -"),
                                "package_name": package_name,
                                "document_count": len(documents),
                                "api_response": response_data
                            })
                            results["summary"]["failed"] += 1
                    else:
                        error_details = ""
                        try:
                            error_data = response.json()
                            error_message = error_data.get("message", "")
                            error_details = f"API Error: {error_message}"
                            
                            # Log the full response for debugging
                            detailed_error = f"HTTP Error {response.status_code}: {error_message}\nFull response: {json.dumps(error_data, indent=2)}"
                            self.status.emit(detailed_error)
                        except:
                            error_details = response.text[:200] + "..." if len(response.text) > 200 else response.text
                            self.status.emit(f"HTTP Error {response.status_code}: {error_details}")
                                
                        results["packages"].append({
                            "package_id": package_id,
                            "status": "http_error",
                            "message": f"HTTP error {response.status_code}: {error_details}",
                            "package_name": package_name,
                            "document_count": len(documents),
                            "response_text": response.text
                        })
                        results["summary"]["failed"] += 1
                    
                except Exception as e:
                    # Get more detailed error information if available
                    error_info = str(e)
                    self.status.emit(f"Exception during API call: {error_info}")
                    
                    results["packages"].append({
                        "package_id": package_id,
                        "status": "exception",
                        "message": f"Exception: {error_info}",
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
    
    # Updated create_api_payload function
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
                "draftOnErrors": package.get("draft_on_errors", True),
                "submitImmediately": package.get("submit_immediately", False),
                "verifyPageMargins": package.get("verify_page_margins", True)
            }
        }
        
        # Process each document
        for doc in documents:
            # Encode document file
            encoded_file = self.encode_file(doc["file_path"])
            if not encoded_file:
                continue
            
            # Create document entry with enhanced structure
            document = {
                "submitterDocumentID": doc["document_id"],
                "name": doc["name"].upper(),
                "kindOfInstrument": [doc["type"]],
                "indexingData": {
                    "grantors": doc.get("grantors", []),
                    "grantees": doc.get("grantees", []),
                    "legalDescriptions": []
                },
                "fileBytes": [encoded_file]
            }
            
            # Format execution date in YYYY-MM-DD format
            if "execution_date" in doc:
                try:
                    date_str = doc.get("execution_date")
                    if isinstance(date_str, str):
                        try:
                            date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                            formatted_date = date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            formatted_date = date_str
                    else:
                        formatted_date = datetime.now().strftime('%Y-%m-%d')
                    
                    document["indexingData"]["executionDate"] = formatted_date
                except:
                    document["indexingData"]["executionDate"] = datetime.now().strftime('%Y-%m-%d')
            else:
                document["indexingData"]["executionDate"] = datetime.now().strftime('%Y-%m-%d')
            
            # Add consideration if provided (ensure it's a float)
            if "consideration" in doc:
                try:
                    document["indexingData"]["consideration"] = float(doc.get("consideration", 0.0))
                except:
                    document["indexingData"]["consideration"] = 0.0
            
            # Format legal descriptions
            if "legal_descriptions" in doc and doc["legal_descriptions"]:
                for desc in doc["legal_descriptions"]:
                    legal_desc = {
                        "description": desc.get("description", "").upper(),
                        "parcelId": desc.get("parcelId", "").upper()
                    }
                    # Only add unitNumber if provided
                    if "unitNumber" in desc and desc["unitNumber"] is not None:
                        legal_desc["unitNumber"] = desc["unitNumber"]
                    document["indexingData"]["legalDescriptions"].append(legal_desc)
            else:
                # Add default legal description
                document["indexingData"]["legalDescriptions"].append({
                    "description": doc.get("legal_description", "").upper(),
                    "parcelId": doc.get("parcel_id", "").upper()
                })
            
            # Format reference information
            if "reference_information" in doc and doc["reference_information"]:
                reference_information = []
                for ref in doc["reference_information"]:
                    try:
                        page_val = int(ref.get("page", 0))
                    except:
                        page_val = 0
                        
                    reference_information.append({
                        "documentType": ref.get("documentType", ""),
                        "book": ref.get("book", ""),
                        "page": page_val
                    })
                document["indexingData"]["referenceInformation"] = reference_information
            
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