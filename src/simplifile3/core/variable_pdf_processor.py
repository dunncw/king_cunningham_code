# simplifile3/core/variable_pdf_processor.py - Variable-length PDF document processor
import base64
import io
from typing import List, Dict, Any, Optional
from PyPDF2 import PdfReader, PdfWriter


class VariablePDFProcessor:
    """Processor for PDF stacks with variable-length documents using page count data"""
    
    def __init__(self):
        self.pdf_cache = {}  # Cache loaded PDFs to avoid re-reading
        self.current_position = 1  # Track current page position (1-based)
    
    def load_pdf_stack(self, pdf_path: str) -> PdfReader:
        """Load and cache a PDF file"""
        if pdf_path not in self.pdf_cache:
            try:
                self.pdf_cache[pdf_path] = PdfReader(pdf_path)
            except Exception as e:
                raise Exception(f"Failed to load PDF: {pdf_path} - {str(e)}")
        
        return self.pdf_cache[pdf_path]
    
    def reset_position(self):
        """Reset current position to beginning of stack"""
        self.current_position = 1
    
    def get_next_document(self, pdf_path: str, page_count: int) -> str:
        """
        Extract next document from PDF stack and return as base64
        
        Args:
            pdf_path: Path to the PDF stack file
            page_count: Number of pages for this document
            
        Returns:
            Base64 encoded PDF data for the extracted document
        """
        try:
            # Load the PDF stack
            pdf_reader = self.load_pdf_stack(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            # Calculate page range for this document (1-based to 0-based conversion)
            start_page = self.current_position - 1  # Convert to 0-based
            end_page = start_page + page_count
            
            # Validate page range
            if start_page >= total_pages:
                raise Exception(f"Current position {self.current_position} exceeds available pages ({total_pages}) in {pdf_path}")
            
            if end_page > total_pages:
                # Adjust end page if we're at the end of the stack
                end_page = total_pages
                actual_pages = end_page - start_page
                if actual_pages < page_count:
                    print(f"Warning: Document at position {self.current_position} has only {actual_pages} pages instead of expected {page_count}")
            
            # Create new PDF with extracted pages
            pdf_writer = PdfWriter()
            
            for page_num in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Update position for next document
            self.current_position += page_count
            
            # Convert to base64
            return self._pdf_writer_to_base64(pdf_writer)
            
        except Exception as e:
            raise Exception(f"Error extracting document at position {self.current_position} ({page_count} pages) from {pdf_path}: {str(e)}")
    
    def skip_document(self, page_count: int):
        """
        Skip a document without extracting it (for duplicate contracts)
        
        Args:
            page_count: Number of pages to skip
        """
        self.current_position += page_count
    
    def validate_page_counts(self, pdf_path: str, page_counts: List[int]) -> List[str]:
        """
        Validate that PDF has enough pages for all specified page counts
        
        Args:
            pdf_path: Path to the PDF stack file
            page_counts: List of page counts for each document
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            pdf_reader = self.load_pdf_stack(pdf_path)
            total_pages = len(pdf_reader.pages)
            required_pages = sum(page_counts)
            
            if required_pages > total_pages:
                errors.append(
                    f"PDF stack has {total_pages} pages but {required_pages} pages are required "
                    f"for {len(page_counts)} documents"
                )
            
            # Check for invalid page counts
            for i, count in enumerate(page_counts):
                if count <= 0:
                    errors.append(f"Invalid page count {count} for document {i + 1}")
            
        except Exception as e:
            errors.append(f"Error validating PDF stack {pdf_path}: {str(e)}")
        
        return errors
    
    def get_stack_info(self, pdf_path: str, page_counts: List[int]) -> Dict[str, Any]:
        """
        Get information about a variable PDF stack
        
        Args:
            pdf_path: Path to the PDF stack file
            page_counts: List of page counts for each document
            
        Returns:
            Dictionary with stack information
        """
        try:
            pdf_reader = self.load_pdf_stack(pdf_path)
            total_pages = len(pdf_reader.pages)
            required_pages = sum(page_counts)
            
            return {
                "pdf_path": pdf_path,
                "total_pages": total_pages,
                "required_pages": required_pages,
                "document_count": len(page_counts),
                "page_counts": page_counts,
                "has_sufficient_pages": required_pages <= total_pages,
                "excess_pages": max(0, total_pages - required_pages)
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing variable PDF stack {pdf_path}: {str(e)}")
    
    def _pdf_writer_to_base64(self, pdf_writer: PdfWriter) -> str:
        """Convert PdfWriter to base64 string"""
        try:
            # Write PDF to memory buffer
            pdf_buffer = io.BytesIO()
            pdf_writer.write(pdf_buffer)
            
            # Get bytes and encode to base64
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return base64.b64encode(pdf_bytes).decode('utf-8')
            
        except Exception as e:
            raise Exception(f"Error converting PDF to base64: {str(e)}")
    
    def clear_cache(self):
        """Clear the PDF cache to free memory"""
        self.pdf_cache.clear()
        self.current_position = 1