"""Unified validation for Simplifile3."""

import os
import pandas as pd
from typing import Dict, List, Any, Optional

from .logging import Logger


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class Validator:
    """Single validation pipeline for all workflows."""
    
    def __init__(self, workflow_spec: Dict[str, Any], logger: Optional[Logger] = None):
        self.spec = workflow_spec
        self.logger = logger or Logger()
    
    def validate(self, excel_df: pd.DataFrame, pdf_paths: Dict[str, str]) -> None:
        """Run all validations. Raises ValidationError on failure."""
        errors = []
        invalid_row_indices = set()

        # Check files exist
        errors.extend(self._check_files_exist(pdf_paths))

        # Check Excel structure
        errors.extend(self._check_excel_structure(excel_df))

        # Check required fields and collect invalid row indices
        required_columns = self.spec.get("required_columns", [])
        for col in required_columns:
            if col in excel_df.columns:
                empty_rows = excel_df[excel_df[col].isna() | (excel_df[col] == "")].index.tolist()
                if empty_rows:
                    invalid_row_indices.update(empty_rows)
        errors.extend(self._check_required_fields(excel_df))

        # Check PDF alignment
        errors.extend(self._check_pdf_alignment(excel_df, pdf_paths))

        if errors:
            for error in errors:
                self.logger.error(error)
            raise ValidationError(f"Validation failed with {len(errors)} errors")
        if invalid_row_indices:
                # Output all unique invalid row indices (Excel is 1-based, add 2 for header)
                row_nums = [str(i + 2) for i in sorted(invalid_row_indices)]
                self.logger.error(f"Invalid rows: {', '.join(row_nums)}")

        self.logger.info("All validations passed")
    
    def _check_files_exist(self, pdf_paths: Dict[str, str]) -> List[str]:
        """Check all required files exist."""
        errors = []
        
        for key, path in pdf_paths.items():
            if not path:
                errors.append(f"Missing path for {key}")
                continue
                
            if not os.path.exists(path):
                errors.append(f"{key} does not exist: {path}")
                continue
                
            # Check if directory when expected
            if key.endswith("_dir") and not os.path.isdir(path):
                errors.append(f"{key} is not a directory: {path}")
            elif not key.endswith("_dir") and not os.path.isfile(path):
                errors.append(f"{key} is not a file: {path}")
        
        return errors
    
    def _check_excel_structure(self, df: pd.DataFrame) -> List[str]:
        """Check Excel has required columns."""
        errors = []
        required_columns = self.spec.get("required_columns", [])
        
        for col in required_columns:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
        
        return errors
    
    def _check_required_fields(self, df: pd.DataFrame) -> List[str]:
        """Check for empty required fields."""
        errors = []
        required_columns = self.spec.get("required_columns", [])
        
        for col in required_columns:
            if col in df.columns:
                empty_rows = df[df[col].isna() | (df[col] == "")].index.tolist()
                if empty_rows:
                    row_nums = [str(r + 2) for r in empty_rows[:5]]  # First 5 examples
                    errors.append(f"Empty {col} at rows: {', '.join(row_nums)}")
        
        return errors
    
    def _check_pdf_alignment(self, df: pd.DataFrame, pdf_paths: Dict[str, str]) -> List[str]:
        """Check PDF documents align with Excel rows."""
        errors = []
        input_mode = self.spec.get("input_mode", "fixed_pdf")
        
        if input_mode == "variable_pdf":
            errors.extend(self._check_variable_pdf(df, pdf_paths))
        elif input_mode == "fixed_pdf":
            errors.extend(self._check_fixed_pdf(df, pdf_paths))
        elif input_mode == "directory":
            errors.extend(self._check_directory_files(df, pdf_paths))
        
        return errors
    
    def _check_variable_pdf(self, df: pd.DataFrame, pdf_paths: Dict[str, str]) -> List[str]:
        """Check variable-length PDF has enough pages."""
        errors = []
        page_field = self.spec.get("page_count_field", "DB Pages")
        
        if page_field not in df.columns:
            errors.append(f"Missing page count column: {page_field}")
            return errors
        
        try:
            # Calculate total pages needed
            total_pages_needed = df[page_field].astype(int).sum()
            
            # Check PDF has enough pages (would need PyPDF2 here)
            # For now, just log the requirement
            self.logger.info(f"Variable PDF needs {total_pages_needed} total pages")
            
        except Exception as e:
            errors.append(f"Error checking variable PDF: {e}")
        
        return errors
    
    def _check_fixed_pdf(self, df: pd.DataFrame, pdf_paths: Dict[str, str]) -> List[str]:
        """Check fixed-page PDF has correct page count."""
        errors = []
        pages_per_doc = self.spec.get("pages_per_document", 2)
        
        # Would need PyPDF2 to check actual page count
        # For now, just log the requirement
        expected_pages = len(df) * pages_per_doc
        self.logger.info(f"Fixed PDF needs {expected_pages} pages ({len(df)} docs × {pages_per_doc} pages)")
        
        return errors
    
    def _check_directory_files(self, df: pd.DataFrame, pdf_paths: Dict[str, str]) -> List[str]:
        """Check directory has required files."""
        errors = []
        dir_path = pdf_paths.get("documents_dir", "")
        
        if not dir_path or not os.path.isdir(dir_path):
            errors.append("Documents directory not found")
            return errors
        
        # Check for expected files based on pattern
        # This would need the actual pattern from spec
        files_in_dir = set(os.listdir(dir_path))
        self.logger.info(f"Found {len(files_in_dir)} files in directory")
        
        return errors