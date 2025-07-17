# workflows/base.py - Base workflow and PDF processor classes
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from ..core.county_config import CountyConfig
from ..utils.logging import Logger


class BaseWorkflow(ABC):
    """Abstract base for workflow-specific processing logic"""
    
    def __init__(self, county_config: CountyConfig, logger: Optional[Logger] = None):
        self.county = county_config
        self.logger = logger or Logger()
    
    @abstractmethod
    def get_required_excel_columns(self) -> List[str]:
        """Return list of required Excel column names"""
        pass
    
    @abstractmethod
    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel column headers to internal field names"""
        pass
    
    @abstractmethod
    def get_document_types(self) -> List[str]:
        """Return document types this workflow creates"""
        pass
    
    @abstractmethod
    def transform_row_data(self, excel_row: Dict[str, Any]) -> Dict[str, Any]:
        """Apply workflow-specific business logic to a single row"""
        pass
    
    def validate_excel_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate Excel file structure"""
        errors = []
        required_columns = self.get_required_excel_columns()
        
        for column in required_columns:
            if column not in df.columns:
                errors.append(f"Missing required Excel column: '{column}'")
        
        return errors
    
    def validate_excel_data(self, df: pd.DataFrame) -> List[str]:
        """Validate Excel data content"""
        errors = []
        required_columns = self.get_required_excel_columns()
        
        for column in required_columns:
            if column in df.columns:
                # Check for empty required fields
                empty_rows = df[df[column].isna() | (df[column] == "")].index.tolist()
                if empty_rows:
                    row_numbers = [str(row + 2) for row in empty_rows]  # +2 for 1-based and header
                    errors.append(f"Empty values in required column '{column}' at rows: {', '.join(row_numbers)}")
        
        return errors
    
    def is_row_valid(self, excel_row: Dict[str, Any]) -> tuple[bool, str]:
        """Check if a row has all required data and should be processed"""
        # Default implementation - can be overridden by specific workflows
        required_fields = self.get_required_excel_columns()
        
        for field_name in required_fields:
            value = excel_row.get(field_name)
            if pd.isna(value) or str(value).strip() == "":
                return False, f"Missing required field: {field_name}"
        
        return True, ""


class BasePDFProcessor(ABC):
    """Abstract base for PDF processing specific to workflows"""
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger()
    
    @abstractmethod
    def validate_stacks(self, *stack_paths: str) -> List[str]:
        """Validate PDF stack alignment and structure"""
        pass
    
    @abstractmethod
    def get_documents(self, document_index: int, *stack_paths: str) -> Dict[str, str]:
        """Get all documents for a specific package"""
        pass
    
    @abstractmethod
    def get_stack_summary(self, *stack_paths: str) -> Dict[str, Any]:
        """Get summary information about stacks"""
        pass
    
    def cleanup(self):
        """Clean up resources - default implementation"""
        pass


class BasePayloadBuilder(ABC):
    """Abstract base for building API payloads"""
    
    def __init__(self, county_config: CountyConfig, logger: Optional[Logger] = None):
        self.county = county_config
        self.logger = logger or Logger()
    
    @abstractmethod
    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete package for API submission"""
        pass
    
    def validate_package(self, package: Dict[str, Any]) -> List[str]:
        """Validate package against known API requirements - base implementation"""
        errors = []
        
        # Basic package structure validation
        if "documents" not in package:
            errors.append("Package missing 'documents' array")
            return errors
        
        if not isinstance(package["documents"], list) or len(package["documents"]) == 0:
            errors.append("Package must contain at least one document")
            return errors
        
        # Validate package-level fields
        required_package_fields = ["recipient", "submitterPackageID", "name", "operations"]
        for field in required_package_fields:
            if field not in package:
                errors.append(f"Package missing required field: {field}")
        
        return errors