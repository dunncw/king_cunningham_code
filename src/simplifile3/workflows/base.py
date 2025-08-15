# simplifile3/workflows/base.py - Base classes for workflow implementations
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from ..utils.logging import Logger
from ..core.county_config import CountyConfig, get_county_config


class BaseWorkflow(ABC):
    """Abstract base for workflow-specific processing logic"""
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger()
        self.supported_counties = self.get_supported_counties()
        self.county_configs = {
            county_id: get_county_config(county_id) 
            for county_id in self.supported_counties
        }
    
    @abstractmethod
    def get_workflow_id(self) -> str:
        """Return unique workflow identifier"""
        pass
    
    @abstractmethod
    def get_supported_counties(self) -> List[str]:
        """Return list of supported county IDs"""
        pass
    
    @abstractmethod
    def get_required_excel_columns(self) -> List[str]:
        """Return list of required Excel column names"""
        pass
    
    @abstractmethod
    def get_excel_mapping(self) -> Dict[str, str]:
        """Map Excel column headers to internal field names"""
        pass
    
    @abstractmethod
    def route_to_county(self, excel_row: Dict[str, Any]) -> str:
        """Determine which county this row should be processed for"""
        pass
    
    @abstractmethod
    def transform_row_data(self, excel_row: Dict[str, Any], target_county: str) -> Dict[str, Any]:
        """Apply workflow-specific business logic to a single row for target county"""
        pass
    
    def get_county_config(self, county_id: str) -> CountyConfig:
        """Get county configuration for supported county"""
        if county_id not in self.county_configs:
            raise ValueError(f"County {county_id} not supported by workflow {self.get_workflow_id()}")
        return self.county_configs[county_id]
    
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
    
    def is_row_valid(self, excel_row: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if a row has all required data and should be processed"""
        # Default implementation - can be overridden by specific workflows
        required_fields = self.get_required_excel_columns()
        
        for field_name in required_fields:
            value = excel_row.get(field_name)
            if pd.isna(value) or str(value).strip() == "":
                return False, f"Missing required field: {field_name}"
        
        # Check if row can be routed to a valid county
        try:
            target_county = self.route_to_county(excel_row)
            if not target_county or target_county not in self.supported_counties:
                return False, f"Cannot route to valid county (got: {target_county})"
        except Exception as e:
            return False, f"County routing failed: {str(e)}"
        
        return True, ""


class BasePDFProcessor(ABC):
    """Abstract base for PDF processing specific to workflows"""
    
    def __init__(self, logger: Optional[Logger] = None):
        self.logger = logger or Logger()
    
    @abstractmethod
    def validate_pdfs(self, file_paths: Dict[str, str], excel_data: List[Dict[str, Any]]) -> List[str]:
        """Validate PDF files against Excel data"""
        pass
    
    @abstractmethod
    def get_documents_for_row(self, row_data: Dict[str, Any], file_paths: Dict[str, str]) -> Dict[str, str]:
        """Get all PDF documents for a specific row as base64 strings"""
        pass
    
    @abstractmethod
    def get_pdf_summary(self, file_paths: Dict[str, str], excel_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary information about PDF files"""
        pass
    
    def cleanup(self):
        """Clean up resources - default implementation"""
        pass


class BasePayloadBuilder(ABC):
    """Abstract base for building API payloads"""
    
    def __init__(self, logger: Optional[Logger] = None):
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