"""Base workflow class with common functionality."""

import os
import base64
from io import BytesIO
from typing import Dict, List, Any, Optional
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter


class BaseWorkflow:
    """Base class for all workflows with common functionality."""
    
    # Override these in subclasses
    name = ""
    display_name = ""
    required_columns = []
    field_mappings = {}
    county = ""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.current_doc_index = 0
    
    def validate_excel(self, df: pd.DataFrame) -> List[str]:
        """Validate Excel has required columns."""
        errors = []
        for col in self.required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
        return errors
    
    def is_row_valid(self, row: Dict[str, Any]) -> bool:
        """Check if row should be processed."""
        for col in self.required_columns:
            if pd.isna(row.get(col)) or str(row.get(col)).strip() == "":
                return False
        return True
    
    def transform_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Excel row to package data. Override for custom logic."""
        data = {}
        
        # Apply field mappings
        for excel_col, api_field in self.field_mappings.items():
            value = row.get(excel_col, "")
            if not pd.isna(value):
                data[api_field] = str(value).strip()
        
        data["county"] = self.county
        return data
    
    def extract_pdfs(self, row_data: Dict[str, Any], pdf_paths: Dict[str, str]) -> Dict[str, bytes]:
        """Extract PDFs for this row. Override for custom logic."""
        return {}
    
    def build_payload(self, package_data: Dict[str, Any], pdfs: Dict[str, bytes]) -> Dict[str, Any]:
        """Build API payload. Override for custom logic."""
        return {
            "documents": [],
            "recipient": self.county,
            "submitterPackageID": package_data.get("package_id", ""),
            "name": package_data.get("package_name", ""),
            "operations": {
                "draftOnErrors": True,
                "submitImmediately": False,
                "verifyPageMargins": True
            }
        }
    
    # Utility methods for PDF handling
    def extract_fixed_pages(self, pdf_path: str, pages_per_doc: int, index: int) -> bytes:
        """Extract document at index from fixed-page PDF."""
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        start = index * pages_per_doc
        end = start + pages_per_doc
        
        for i in range(start, min(end, len(reader.pages))):
            writer.add_page(reader.pages[i])
        
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()
    
    def extract_variable_pages(self, pdf_path: str, page_count: int) -> bytes:
        """Extract variable pages from current position."""
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        for i in range(self.current_doc_index, min(self.current_doc_index + page_count, len(reader.pages))):
            writer.add_page(reader.pages[i])
        
        self.current_doc_index += page_count
        
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()


    def extract_pages_at_position(self, pdf_path: str, start_position: int, page_count: int) -> bytes:
        """Extract pages from PDF starting at specific position."""
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        end_position = start_position + page_count
        
        for i in range(start_position, min(end_position, len(reader.pages))):
            writer.add_page(reader.pages[i])
        
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()


    def merge_pdfs(self, *pdfs: bytes) -> bytes:
        """Merge multiple PDFs."""
        writer = PdfWriter()
        
        for pdf_bytes in pdfs:
            reader = PdfReader(BytesIO(pdf_bytes))
            for page in reader.pages:
                writer.add_page(page)
        
        buffer = BytesIO()
        writer.write(buffer)
        return buffer.getvalue()
    
    def to_base64(self, pdf_bytes: bytes) -> str:
        """Convert PDF bytes to base64."""
        return base64.b64encode(pdf_bytes).decode('utf-8')
    
    def clean_money(self, value: str) -> str:
        """Clean monetary value by removing leading $ and keeping as string."""
        if not value:
            return "0"
        
        # Convert to string and strip whitespace
        cleaned = str(value).strip()
        
        # Remove leading $ if present
        if cleaned.startswith("$"):
            cleaned = cleaned[1:]
        
        # Return as string (don't convert to float)
        return cleaned if cleaned else "0"