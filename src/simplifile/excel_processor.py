# excel_processor.py - Centralized Excel processing for Simplifile
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
import os
from .models import SimplifilePackage, SimplifileDocument, Party, LegalDescription, ReferenceInformation

class SimplifileExcelProcessor:
    """Handles all Excel data processing for Simplifile"""
    
    def __init__(self):
        self.missing_required_columns = []
        self.missing_recommended_columns = []
        self.validation_warnings = []
    
    def load_excel_file(self, excel_path: str) -> Optional[pd.DataFrame]:
        """Load and validate Excel file for Simplifile processing"""
        try:
            if not os.path.exists(excel_path):
                raise FileNotFoundError(f"Excel file not found: {excel_path}")
                
            # Load Excel file
            data = pd.read_excel(excel_path)
            
            # Validate required columns
            required_columns = [
                'KC File No.', 'Account', 'Last Name #1', 'First Name #1'
            ]
            
            recommended_columns = [
                'Deed Book', 'Deed Page', 'Mortgage Book', 'Mortgage Page', 
                'Execution Date', 'GRANTOR/GRANTEE', 'LEGAL DESCRIPTION',
                'Suite', 'Consideration', '&', 'Last Name #2', 'First Name #2'
            ]
            
            # Check for missing columns
            self.missing_required_columns = [col for col in required_columns if col not in data.columns]
            self.missing_recommended_columns = [col for col in recommended_columns if col not in data.columns]
            
            if self.missing_required_columns:
                raise ValueError(f"Missing required columns: {', '.join(self.missing_required_columns)}")
            
            # Basic validation of data format
            self.validation_warnings = []
            
            # Check if names are in ALL CAPS as required
            if 'Last Name #1' in data.columns:
                for idx, value in data['Last Name #1'].items():
                    if isinstance(value, str) and value != value.upper():
                        self.validation_warnings.append(f"Row {idx+2}: Last name '{value}' is not in ALL CAPS")
            
            if 'First Name #1' in data.columns:
                for idx, value in data['First Name #1'].items():
                    if isinstance(value, str) and value != value.upper():
                        self.validation_warnings.append(f"Row {idx+2}: First name '{value}' is not in ALL CAPS")
            
            # Check for empty cells in required columns
            empty_accounts = data[data['Account'].isna()].index.tolist()
            if empty_accounts:
                self.validation_warnings.append(
                    f"Empty account numbers in rows: {', '.join(map(str, [i+2 for i in empty_accounts]))}"
                )
            
            return data
            
        except Exception as e:
            raise Exception(f"Error loading Excel file: {str(e)}")
    
    def get_cell_value(self, row: pd.Series, column: str, default: str = "") -> str:
        """Safely extract cell value from Excel row"""
        try:
            if column in row and pd.notna(row[column]):
                return str(row[column])
            return default
        except:
            return default
    
    def create_package_from_row(self, row: pd.Series, row_index: int) -> SimplifilePackage:
        """Create a SimplifilePackage from an Excel row"""
        # First create the package with basic information
        package = SimplifilePackage.from_excel_row({
            'Account': self.get_cell_value(row, 'Account'),
            'KC File No.': self.get_cell_value(row, 'KC File No.'),
            'Last Name #1': self.get_cell_value(row, 'Last Name #1'),
            'First Name #1': self.get_cell_value(row, 'First Name #1'),
            'GRANTOR/GRANTEE': self.get_cell_value(row, 'GRANTOR/GRANTEE')
        }, row_index)
        
        # Get more data for creating documents
        last_name1 = SimplifilePackage.format_name(self.get_cell_value(row, 'Last Name #1'))
        first_name1 = SimplifilePackage.format_name(self.get_cell_value(row, 'First Name #1'))
        
        # Check for second owner
        has_second_owner = '&' in self.get_cell_value(row, '&', '')
        last_name2 = SimplifilePackage.format_name(self.get_cell_value(row, 'Last Name #2')) if has_second_owner else ''
        first_name2 = SimplifilePackage.format_name(self.get_cell_value(row, 'First Name #2')) if has_second_owner else ''
        
        # Get common document data
        execution_date = self.get_cell_value(row, 'Execution Date', '')
        legal_description = SimplifilePackage.format_name(self.get_cell_value(row, 'LEGAL DESCRIPTION', ''))
        suite = self.get_cell_value(row, 'Suite', '')
        consideration = self.get_cell_value(row, 'Consideration', '0.00')
        grantor_grantee = SimplifilePackage.format_name(self.get_cell_value(row, 'GRANTOR/GRANTEE', ''))
        
        # Create legal description object
        legal_desc = LegalDescription(legal_description, suite)
        
        # Create deed document
        deed_document = SimplifileDocument()
        deed_document.document_id = f"D-{package.account_number}-TD"
        
        # Document name based on convention
        if last_name1.startswith("ORG:"):
            deed_document.name = f"{package.account_number} {first_name1} TD"
        else:
            deed_document.name = f"{package.account_number} {last_name1} TD"
        
        deed_document.type = "Deed - Timeshare"
        deed_document.execution_date = execution_date
        deed_document.consideration = consideration
        deed_document.legal_descriptions.append(legal_desc)
        
        # Add reference information for deed
        deed_book = self.get_cell_value(row, 'Deed Book', '')
        deed_page = self.get_cell_value(row, 'Deed Page', '')
        
        if deed_book or deed_page:
            deed_ref = ReferenceInformation("Deed - Timeshare", deed_book, deed_page)
            deed_document.reference_information.append(deed_ref)
        
        # Add grantors for deed document (following the rules)
        # First, always add KING CUNNINGHAM LLC TR
        deed_document.grantors.append(Party(name="KING CUNNINGHAM LLC TR", is_organization=True))
        
        # Add grantor/grantee entity
        if grantor_grantee:
            deed_document.grantors.append(Party(name=grantor_grantee, is_organization=True))
        
        # Add individual owners as grantors
        if first_name1 and last_name1:
            deed_document.grantors.append(Party.from_excel_data(first_name1, last_name1))
            
        if has_second_owner and first_name2 and last_name2:
            deed_document.grantors.append(Party.from_excel_data(first_name2, last_name2))
        
        # Add grantee (from GRANTOR/GRANTEE)
        if grantor_grantee:
            deed_document.grantees.append(Party(name=grantor_grantee, is_organization=True))
        
        # Create mortgage satisfaction document
        mortgage_document = SimplifileDocument()
        mortgage_document.document_id = f"D-{package.account_number}-SAT"
        
        # Document name based on convention
        if last_name1.startswith("ORG:"):
            mortgage_document.name = f"{package.account_number} {first_name1} SAT"
        else:
            mortgage_document.name = f"{package.account_number} {last_name1} SAT"
        
        mortgage_document.type = "Mortgage Satisfaction"
        mortgage_document.execution_date = execution_date
        mortgage_document.legal_descriptions.append(legal_desc)
        
        # Add reference information for mortgage satisfaction
        mortgage_book = self.get_cell_value(row, 'Mortgage Book', '')
        mortgage_page = self.get_cell_value(row, 'Mortgage Page', '')
        
        if mortgage_book or mortgage_page:
            mortgage_ref = ReferenceInformation("Mortgage Satisfaction", mortgage_book, mortgage_page)
            mortgage_document.reference_information.append(mortgage_ref)
        
        # Add grantors for mortgage document (only individuals, NOT KING CUNNINGHAM LLC TR)
        # First, add individual owners
        if first_name1 and last_name1:
            mortgage_document.grantors.append(Party.from_excel_data(first_name1, last_name1))
            
        if has_second_owner and first_name2 and last_name2:
            mortgage_document.grantors.append(Party.from_excel_data(first_name2, last_name2))
        
        # Add grantee (from GRANTOR/GRANTEE)
        if grantor_grantee:
            mortgage_document.grantees.append(Party(name=grantor_grantee, is_organization=True))
        
        # Add documents to package
        package.add_document(deed_document)
        package.add_document(mortgage_document)
        
        # Validate package
        self.validate_package(package)
        
        return package
    
    def process_excel_data(self, excel_data: pd.DataFrame) -> List[SimplifilePackage]:
        """Process Excel data into SimplifilePackage objects"""
        packages = []
        
        for i, row in excel_data.iterrows():
            try:
                package = self.create_package_from_row(row, i)
                packages.append(package)
            except Exception as e:
                # Log error but continue processing other rows
                print(f"Error processing row {i+2}: {str(e)}")
        
        return packages
    
    def validate_package(self, package: SimplifilePackage) -> None:
        """Validate a package and set validation status"""
        package.is_valid = True
        package.validation_issues = []
        
        # Validate basic package info
        if not package.account_number:
            package.is_valid = False
            package.validation_issues.append("Missing account number")
        
        if not package.kc_file_no:
            package.is_valid = False
            package.validation_issues.append("Missing KC File No.")
        
        # Validate documents
        for doc in package.documents:
            doc.is_valid = True
            doc.validation_issues = []
            
            # Check required fields based on document type
            if doc.type == "Deed - Timeshare":
                if not doc.reference_information or not doc.reference_information[0].book or not doc.reference_information[0].page:
                    doc.is_valid = False
                    doc.validation_issues.append("Missing deed book/page reference")
                    package.is_valid = False
            
            elif doc.type == "Mortgage Satisfaction":
                if not doc.reference_information or not doc.reference_information[0].book or not doc.reference_information[0].page:
                    doc.is_valid = False
                    doc.validation_issues.append("Missing mortgage book/page reference")
                    package.is_valid = False
            
            # Check required parties
            if not doc.grantors:
                doc.is_valid = False
                doc.validation_issues.append("Missing grantors")
                package.is_valid = False
            
            if not doc.grantees:
                doc.is_valid = False
                doc.validation_issues.append("Missing grantees")
                package.is_valid = False