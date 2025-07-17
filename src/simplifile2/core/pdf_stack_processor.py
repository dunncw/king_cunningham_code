# simplifile2/pdf_stack_processor.py - Generic PDF stack processing
import base64
import io
from typing import List, Dict, Any, Optional
from PyPDF2 import PdfReader, PdfWriter


class PDFStackProcessor:
    """Generic processor for PDF document stacks"""
    
    def __init__(self):
        self.pdf_cache = {}  # Cache loaded PDFs to avoid re-reading
    
    def load_pdf_stack(self, pdf_path: str) -> PdfReader:
        """Load and cache a PDF file"""
        if pdf_path not in self.pdf_cache:
            try:
                self.pdf_cache[pdf_path] = PdfReader(pdf_path)
            except Exception as e:
                raise Exception(f"Failed to load PDF: {pdf_path} - {str(e)}")
        
        return self.pdf_cache[pdf_path]
    
    def get_document_from_stack(self, pdf_path: str, document_index: int, pages_per_document: int) -> str:
        """
        Extract a specific document from a PDF stack and return as base64
        
        Args:
            pdf_path: Path to the PDF stack file
            document_index: 0-based index of the document to extract
            pages_per_document: Number of pages per document in the stack
            
        Returns:
            Base64 encoded PDF data for the extracted document
        """
        try:
            # Load the PDF stack
            pdf_reader = self.load_pdf_stack(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            # Calculate page range for this document
            start_page = document_index * pages_per_document
            end_page = start_page + pages_per_document
            
            # Validate page range
            if start_page >= total_pages:
                raise Exception(f"Document index {document_index} exceeds available pages in {pdf_path}")
            
            if end_page > total_pages:
                # Adjust end page if we're at the end of the stack
                end_page = total_pages
                actual_pages = end_page - start_page
                if actual_pages < pages_per_document:
                    print(f"Warning: Document {document_index} has only {actual_pages} pages instead of expected {pages_per_document}")
            
            # Create new PDF with extracted pages
            pdf_writer = PdfWriter()
            
            for page_num in range(start_page, end_page):
                pdf_writer.add_page(pdf_reader.pages[page_num])
            
            # Convert to base64
            return self._pdf_writer_to_base64(pdf_writer)
            
        except Exception as e:
            raise Exception(f"Error extracting document {document_index} from {pdf_path}: {str(e)}")
    
    def get_stack_info(self, pdf_path: str, pages_per_document: int) -> Dict[str, Any]:
        """
        Get information about a PDF stack
        
        Args:
            pdf_path: Path to the PDF stack file
            pages_per_document: Expected pages per document
            
        Returns:
            Dictionary with stack information
        """
        try:
            pdf_reader = self.load_pdf_stack(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            # Calculate number of complete documents
            complete_documents = total_pages // pages_per_document
            remaining_pages = total_pages % pages_per_document
            
            return {
                "pdf_path": pdf_path,
                "total_pages": total_pages,
                "pages_per_document": pages_per_document,
                "complete_documents": complete_documents,
                "remaining_pages": remaining_pages,
                "has_incomplete_document": remaining_pages > 0
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing PDF stack {pdf_path}: {str(e)}")
    
    def validate_stacks_alignment(self, stack_configs: List[Dict[str, Any]]) -> List[str]:
        """
        Validate that all PDF stacks have the same number of documents
        
        Args:
            stack_configs: List of stack configuration dictionaries
                          Each should have 'pdf_path' and 'pages_per_document'
        
        Returns:
            List of validation error messages
        """
        errors = []
        stack_info = []
        
        # Get info for each stack
        for config in stack_configs:
            try:
                info = self.get_stack_info(config["pdf_path"], config["pages_per_document"])
                info["stack_name"] = config.get("stack_name", "Unknown")
                stack_info.append(info)
            except Exception as e:
                errors.append(f"Failed to analyze {config.get('stack_name', 'stack')}: {str(e)}")
                return errors  # Can't continue validation if we can't read stacks
        
        # Check alignment
        if len(stack_info) > 1:
            first_stack = stack_info[0]
            expected_documents = first_stack["complete_documents"]
            
            for info in stack_info[1:]:
                if info["complete_documents"] != expected_documents:
                    errors.append(
                        f"Stack alignment error: {first_stack['stack_name']} has {expected_documents} documents, "
                        f"but {info['stack_name']} has {info['complete_documents']} documents"
                    )
        
        # Check for incomplete documents
        for info in stack_info:
            if info["has_incomplete_document"]:
                errors.append(
                    f"Incomplete document in {info['stack_name']}: {info['remaining_pages']} extra pages "
                    f"(expected {info['pages_per_document']} pages per document)"
                )
        
        return errors
    
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


class FultonFCLPDFProcessor:
    """Specialized processor for Fulton FCL workflow PDF stacks"""
    
    def __init__(self):
        self.stack_processor = PDFStackProcessor()
    
    def validate_fcl_stacks(self, deed_path: str, pt61_path: str, mortgage_path: str) -> List[str]:
        """Validate all three FCL PDF stacks"""
        stack_configs = [
            {
                "pdf_path": deed_path,
                "pages_per_document": 3,
                "stack_name": "Deed Stack"
            },
            {
                "pdf_path": pt61_path,
                "pages_per_document": 1,
                "stack_name": "PT-61 Stack"
            },
            {
                "pdf_path": mortgage_path,
                "pages_per_document": 1,
                "stack_name": "Mortgage Satisfaction Stack"
            }
        ]
        
        return self.stack_processor.validate_stacks_alignment(stack_configs)
    
    def get_fcl_documents(self, document_index: int, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, str]:
        """
        Get all documents for a specific FCL package
        
        Args:
            document_index: 0-based index of the document set to extract
            deed_path: Path to deed stack PDF
            pt61_path: Path to PT-61 stack PDF
            mortgage_path: Path to mortgage satisfaction stack PDF
        
        Returns:
            Dictionary with base64 encoded documents:
            {
                "deed_pdf": "base64_data",
                "pt61_pdf": "base64_data", 
                "mortgage_pdf": "base64_data"
            }
        """
        try:
            documents = {}
            
            # Extract deed document (3 pages)
            documents["deed_pdf"] = self.stack_processor.get_document_from_stack(
                deed_path, document_index, 3
            )
            
            # Extract PT-61 document (1 page)
            documents["pt61_pdf"] = self.stack_processor.get_document_from_stack(
                pt61_path, document_index, 1
            )
            
            # Extract mortgage satisfaction document (1 page)
            documents["mortgage_pdf"] = self.stack_processor.get_document_from_stack(
                mortgage_path, document_index, 1
            )
            
            return documents
            
        except Exception as e:
            raise Exception(f"Error extracting FCL documents for index {document_index}: {str(e)}")
    
    def get_fcl_stack_summary(self, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, Any]:
        """Get summary information about all FCL stacks"""
        try:
            deed_info = self.stack_processor.get_stack_info(deed_path, 3)
            pt61_info = self.stack_processor.get_stack_info(pt61_path, 1)
            mortgage_info = self.stack_processor.get_stack_info(mortgage_path, 1)
            
            # Determine how many complete packages we can create
            max_packages = min(
                deed_info["complete_documents"],
                pt61_info["complete_documents"],
                mortgage_info["complete_documents"]
            )
            
            return {
                "deed_stack": deed_info,
                "pt61_stack": pt61_info,
                "mortgage_stack": mortgage_info,
                "max_packages": max_packages,
                "all_stacks_aligned": (
                    deed_info["complete_documents"] == pt61_info["complete_documents"] == 
                    mortgage_info["complete_documents"]
                )
            }
            
        except Exception as e:
            raise Exception(f"Error getting FCL stack summary: {str(e)}")
    
    def cleanup(self):
        """Clean up resources"""
        self.stack_processor.clear_cache()