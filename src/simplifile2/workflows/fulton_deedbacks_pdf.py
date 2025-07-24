# workflows/fulton_deedbacks_pdf.py - PDF processing for Deedbacks workflow
import os
import base64
from typing import Dict, List, Any, Optional
from PyPDF2 import PdfReader

from .base import BasePDFProcessor
from ..utils.logging import Logger


class FultonDeedbacksPDFProcessor(BasePDFProcessor):
    """PDF processor for Fulton Deedbacks workflow - handles individual PDF files from directory"""

    def __init__(self, logger: Optional[Logger] = None):
        super().__init__(logger)
        self.pdf_cache = {}  # Cache loaded PDFs to avoid re-reading

    def validate_stacks(self, *args) -> List[str]:
        """Deedbacks doesn't use stacks - this is handled by the document processor"""
        return []

    def get_documents(self, document_index: int, *args) -> Dict[str, str]:
        """Not used for Deedbacks - documents are retrieved by contract number"""
        raise NotImplementedError("Use get_documents_by_contract_number for Deedbacks workflow")

    def get_stack_summary(self, *args) -> Dict[str, Any]:
        """Not used for Deedbacks - summary is provided by document processor"""
        return {}

    def get_documents_by_contract_number(self, contract_num: str, document_paths: Dict[str, str]) -> Dict[str, str]:
        """
        Get base64 encoded documents for a specific contract number
        
        Args:
            contract_num: Contract number (for logging)
            document_paths: Dictionary with 'deed_path', 'pt61_path', and optionally 'sat_path'
        
        Returns:
            Dictionary with base64 encoded documents:
            {
                "deed_pdf": "base64_data",
                "pt61_pdf": "base64_data", 
                "mortgage_pdf": "base64_data"  # only if SAT document exists
            }
        """
        try:
            documents = {}
            
            # Process deed document (required)
            if 'deed_path' not in document_paths:
                raise Exception(f"Missing deed document path for contract {contract_num}")
            
            documents["deed_pdf"] = self._pdf_file_to_base64(
                document_paths['deed_path'], f"deed for contract {contract_num}"
            )
            
            # Process PT-61 document (required)
            if 'pt61_path' not in document_paths:
                raise Exception(f"Missing PT-61 document path for contract {contract_num}")
            
            documents["pt61_pdf"] = self._pdf_file_to_base64(
                document_paths['pt61_path'], f"PT-61 for contract {contract_num}"
            )
            
            # Process SAT document (optional)
            if 'sat_path' in document_paths:
                documents["mortgage_pdf"] = self._pdf_file_to_base64(
                    document_paths['sat_path'], f"SAT for contract {contract_num}"
                )
                self.logger.info(f"  Loaded SAT document for contract {contract_num}")
            else:
                self.logger.info(f"  No SAT document for contract {contract_num} (optional)")
            
            return documents
            
        except Exception as e:
            raise Exception(f"Error loading documents for contract {contract_num}: {str(e)}")

    def _pdf_file_to_base64(self, file_path: str, description: str) -> str:
        """
        Convert a PDF file to base64 string with validation
        
        Args:
            file_path: Path to PDF file
            description: Description for error messages
            
        Returns:
            Base64 encoded PDF data
        """
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise Exception(f"File does not exist: {file_path}")
            
            if not os.path.isfile(file_path):
                raise Exception(f"Path is not a file: {file_path}")
            
            # Check file size (reasonable limits)
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise Exception(f"File is empty: {file_path}")
            elif file_size > 50 * 1024 * 1024:  # 50MB limit
                raise Exception(f"File too large (>50MB): {file_path}")
            
            # Validate it's a PDF by reading header
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    raise Exception(f"File is not a valid PDF: {file_path}")
                
                # Reset to beginning and read entire file
                f.seek(0)
                pdf_bytes = f.read()
            
            # Additional PDF validation using PyPDF2
            try:
                # Try to load with PyPDF2 to ensure it's readable
                import io
                pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                page_count = len(pdf_reader.pages)
                
                if page_count == 0:
                    raise Exception(f"PDF has no pages: {file_path}")
                
                self.logger.info(f"  Validated PDF: {os.path.basename(file_path)} ({page_count} pages, {file_size:,} bytes)")
                
            except Exception as pdf_error:
                raise Exception(f"PDF validation failed for {file_path}: {str(pdf_error)}")
            
            # Convert to base64
            base64_data = base64.b64encode(pdf_bytes).decode('utf-8')
            
            return base64_data
            
        except Exception as e:
            raise Exception(f"Error processing {description} at {file_path}: {str(e)}")

    def validate_documents_for_package(self, contract_num: str, document_paths: Dict[str, str]) -> List[str]:
        """
        Validate all documents for a specific package without loading them
        
        Args:
            contract_num: Contract number for error messages
            document_paths: Dictionary with document paths
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required documents
        required_docs = ['deed_path', 'pt61_path']
        for doc_key in required_docs:
            if doc_key not in document_paths:
                errors.append(f"Missing {doc_key} for contract {contract_num}")
                continue
            
            file_path = document_paths[doc_key]
            doc_type = doc_key.replace('_path', '')
            
            # Validate file existence and basic properties
            file_errors = self._validate_single_file(file_path, f"{doc_type} for contract {contract_num}")
            errors.extend(file_errors)
        
        # Check optional SAT document if present
        if 'sat_path' in document_paths:
            file_errors = self._validate_single_file(
                document_paths['sat_path'], 
                f"SAT for contract {contract_num}"
            )
            errors.extend(file_errors)
        
        return errors

    def _validate_single_file(self, file_path: str, description: str) -> List[str]:
        """Validate a single PDF file without loading it fully"""
        errors = []
        
        try:
            # Basic file checks
            if not os.path.exists(file_path):
                errors.append(f"{description}: File does not exist - {file_path}")
                return errors
            
            if not os.path.isfile(file_path):
                errors.append(f"{description}: Path is not a file - {file_path}")
                return errors
            
            # Size checks
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                errors.append(f"{description}: File is empty - {file_path}")
                return errors
            elif file_size > 50 * 1024 * 1024:
                errors.append(f"{description}: File too large (>50MB) - {file_path}")
                return errors
            
            # PDF header check
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    errors.append(f"{description}: Not a valid PDF file - {file_path}")
                    return errors
            
        except Exception as e:
            errors.append(f"{description}: Error accessing file - {str(e)}")
        
        return errors

    def get_package_document_summary(self, contract_num: str, document_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        Get summary info about documents for a package without fully loading them
        
        Returns:
            Dictionary with summary information
        """
        summary = {
            "contract_num": contract_num,
            "has_deed": 'deed_path' in document_paths,
            "has_pt61": 'pt61_path' in document_paths,
            "has_sat": 'sat_path' in document_paths,
            "document_count": 1,  # Always 1 package for Deedbacks (deed + optional sat)
            "files": {}
        }
        
        # Get file info for each document
        for doc_key, file_path in document_paths.items():
            doc_type = doc_key.replace('_path', '')
            
            try:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    summary["files"][doc_type] = {
                        "path": file_path,
                        "filename": os.path.basename(file_path),
                        "size_bytes": file_size,
                        "exists": True
                    }
                else:
                    summary["files"][doc_type] = {
                        "path": file_path,
                        "filename": os.path.basename(file_path),
                        "exists": False
                    }
            except Exception as e:
                summary["files"][doc_type] = {
                    "path": file_path,
                    "error": str(e),
                    "exists": False
                }
        
        # Determine package type
        if summary["has_sat"]:
            summary["package_type"] = "Deed + Satisfaction"
            summary["api_document_count"] = 2
        else:
            summary["package_type"] = "Deed Only"
            summary["api_document_count"] = 1
        
        return summary

    def cleanup(self):
        """Clean up resources"""
        self.pdf_cache.clear()