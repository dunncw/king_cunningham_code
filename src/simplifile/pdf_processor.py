import os
import tempfile
from PyQt6.QtWidgets import QApplication
from PyPDF2 import PdfReader, PdfWriter
from typing import List, Dict, Any, Optional, Tuple
import shutil

class SimplifilePDFProcessor:
    """Handles all PDF operations for Simplifile"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Error cleaning up temporary files: {str(e)}")
    
    def split_deed_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Split deed document PDF into individual files (every 2 pages)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Deed PDF not found: {pdf_path}")
                
            deed_files = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            pages_per_doc = 2  # Deeds are 2 pages each
            doc_count = (total_pages + pages_per_doc - 1) // pages_per_doc  # Ceiling division
            
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
                    "type": "Deed - Timeshare",
                    "page_range": f"{start_page+1}-{end_page}",
                    "page_count": end_page - start_page
                })

                if i % 5 == 0:
                    QApplication.processEvents()
            
            return deed_files
            
        except Exception as e:
            raise Exception(f"Error splitting deed PDF: {str(e)}")
    
    def split_affidavit_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Split affidavit document PDF into individual files (every 2 pages)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Affidavit PDF not found: {pdf_path}")
                
            affidavit_files = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            pages_per_doc = 2  # Affidavits are 2 pages each
            doc_count = (total_pages + pages_per_doc - 1) // pages_per_doc  # Ceiling division
            
            for i in range(doc_count):
                start_page = i * pages_per_doc
                end_page = min(start_page + pages_per_doc, total_pages)
                
                # Create a new PDF writer for this chunk
                output_pdf = PdfWriter()
                
                # Add pages from the original document
                for page_num in range(start_page, end_page):
                    output_pdf.add_page(pdf.pages[page_num])
                
                # Save the split document
                output_path = os.path.join(self.temp_dir, f"affidavit_{i+1}.pdf")
                with open(output_path, "wb") as output_file:
                    output_pdf.write(output_file)
                
                affidavit_files.append({
                    "index": i,
                    "path": output_path,
                    "type": "Affidavit",
                    "page_range": f"{start_page+1}-{end_page}",
                    "page_count": end_page - start_page
                })
            
            return affidavit_files
            
        except Exception as e:
            raise Exception(f"Error splitting affidavit PDF: {str(e)}")
    
    def split_mortgage_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Split mortgage satisfaction PDF into individual files (1 page per document)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Mortgage PDF not found: {pdf_path}")
                
            mortgage_files = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            
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
                    "type": "Mortgage Satisfaction",
                    "page_range": f"{i+1}",
                    "page_count": 1
                })
            
            return mortgage_files
            
        except Exception as e:
            raise Exception(f"Error splitting mortgage PDF: {str(e)}")
    
    def merge_deeds_and_affidavits(self, deed_files: List[Dict[str, Any]], 
                                   affidavit_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge deed files (2 pages) with affidavit files (2 pages) to create 4-page documents"""
        try:
            merged_files = []
            
            # We need to match each deed with its corresponding affidavit
            doc_count = min(len(deed_files), len(affidavit_files))
            
            for i in range(doc_count):
                deed = deed_files[i]
                affidavit = affidavit_files[i]
                
                # Create a new PDF writer for the merged document
                output_pdf = PdfWriter()
                
                # Read the deed PDF
                deed_pdf = PdfReader(deed["path"])
                
                # Read the affidavit PDF
                affidavit_pdf = PdfReader(affidavit["path"])
                
                # Add pages from deed document
                for page in deed_pdf.pages:
                    output_pdf.add_page(page)
                
                # Add pages from affidavit document
                for page in affidavit_pdf.pages:
                    output_pdf.add_page(page)
                
                # Save the merged document
                output_path = os.path.join(self.temp_dir, f"merged_deed_{i+1}.pdf")
                with open(output_path, "wb") as output_file:
                    output_pdf.write(output_file)
                
                # Create merged document info (copy from deed but update path and page info)
                merged_file = deed.copy()
                merged_file["path"] = output_path
                merged_file["source"] = "merged_deed_and_affidavit"
                merged_file["page_range"] = f"{deed['page_range']},{affidavit['page_range']}"
                merged_file["page_count"] = deed["page_count"] + affidavit["page_count"]
                
                merged_files.append(merged_file)
            
            # Check if we have unmatched deed documents
            if len(deed_files) > len(affidavit_files):
                # Add the remaining deed files without merging
                for i in range(doc_count, len(deed_files)):
                    merged_files.append(deed_files[i])
            
            return merged_files
            
        except Exception as e:
            raise Exception(f"Error merging deed and affidavit documents: {str(e)}")
    
    def analyze_deed_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Analyze deed PDF without creating files (for preview)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Deed PDF not found: {pdf_path}")
                
            analysis = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            pages_per_doc = 2  # Deeds are 2 pages each
            doc_count = (total_pages + pages_per_doc - 1) // pages_per_doc  # Ceiling division
            
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
                
                analysis.append({
                    "index": i,
                    "start_page": start_page + 1,  # 1-based for display
                    "end_page": end_page,
                    "page_count": end_page - start_page,
                    "type": "Deed - Timeshare",
                    "page_range": f"{start_page+1}-{end_page}",
                    "sample_text": sample_text,
                    "estimated_size": "~15-25KB"  # Estimated size after split
                })
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing deed PDF: {str(e)}")
    
    def analyze_affidavit_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Analyze affidavit PDF without creating files (for preview)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Affidavit PDF not found: {pdf_path}")
                
            analysis = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            pages_per_doc = 2  # Affidavits are 2 pages each
            doc_count = (total_pages + pages_per_doc - 1) // pages_per_doc  # Ceiling division
            
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
                
                analysis.append({
                    "index": i,
                    "start_page": start_page + 1,  # 1-based for display
                    "end_page": end_page,
                    "page_count": end_page - start_page,
                    "type": "Affidavit",
                    "page_range": f"{start_page+1}-{end_page}",
                    "sample_text": sample_text,
                    "estimated_size": "~15-25KB"  # Estimated size after split
                })
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing affidavit PDF: {str(e)}")
    
    def analyze_mortgage_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Analyze mortgage PDF without creating files (for preview)"""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Mortgage PDF not found: {pdf_path}")
                
            analysis = []
            
            # Read PDF
            pdf = PdfReader(pdf_path)
            total_pages = len(pdf.pages)
            
            for i in range(total_pages):
                # Try to extract some text from page for identification
                sample_text = ""
                try:
                    page = pdf.pages[i]
                    sample_text = page.extract_text()[:100] if hasattr(page, 'extract_text') else ""
                    sample_text = sample_text.replace('\n', ' ').strip()
                except:
                    sample_text = "Text extraction failed"
                
                analysis.append({
                    "index": i,
                    "start_page": i + 1,  # 1-based for display
                    "end_page": i + 1,
                    "page_count": 1,
                    "type": "Mortgage Satisfaction",
                    "page_range": f"{i+1}",
                    "sample_text": sample_text,
                    "estimated_size": "~10-15KB"  # Estimated size
                })
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing mortgage PDF: {str(e)}")