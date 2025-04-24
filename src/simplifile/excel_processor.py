# excel_processor.py - Updated Excel processing for Simplifile with county support
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
import os
from .models import SimplifilePackage, SimplifileDocument, Party, LegalDescription, ReferenceInformation
from .county_config import get_county_config

class SimplifileExcelProcessor:
    """Handles all Excel data processing for Simplifile"""

    def __init__(self, county_id: str = "SCCP49"):
        self.missing_required_columns = []
        self.missing_recommended_columns = []
        self.validation_warnings = []
        self.county_id = county_id
        self.county_config = get_county_config(county_id)

    def set_county(self, county_id: str):
        """Set the county configuration to use for processing"""
        self.county_id = county_id
        self.county_config = get_county_config(county_id)

    def load_excel_file(self, excel_path: str) -> Optional[pd.DataFrame]:
        """Load and validate Excel file for Simplifile processing with enhanced validation"""
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
            
            # Check for empty cells in required fields
            for col in required_columns:
                if col in data.columns:
                    empty_cells = data[data[col].isna()].index.tolist()
                    if empty_cells:
                        self.validation_warnings.append(
                            f"Empty {col} in rows: {', '.join(map(str, [i+2 for i in empty_cells]))}"
                        )
            
            # Check for empty cells in important recommended columns based on county configuration
            important_fields = []
            if self.county_config.DEED_REQUIRES_REFERENCE_INFO:
                important_fields.extend(['Deed Book', 'Deed Page'])
                
            if self.county_config.MORTGAGE_REQUIRES_REFERENCE_INFO:
                important_fields.extend(['Mortgage Book', 'Mortgage Page'])
                
            if self.county_config.DEED_REQUIRES_LEGAL_DESCRIPTION:
                important_fields.append('LEGAL DESCRIPTION')
                
            if self.county_config.DEED_GRANTEES_USE_GRANTOR_GRANTEE:
                important_fields.append('GRANTOR/GRANTEE')
                
            for col in important_fields:
                if col in data.columns:
                    empty_cells = data[data[col].isna()].index.tolist()
                    if empty_cells:
                        self.validation_warnings.append(
                            f"Empty {col} in rows: {', '.join(map(str, [i+2 for i in empty_cells]))}"
                        )
            
            # Special check for '&' indicator and matching Last Name #2/First Name #2
            if '&' in data.columns and 'Last Name #2' in data.columns and 'First Name #2' in data.columns:
                for idx, row in data.iterrows():
                    # Check if & field indicates a second owner but Last Name #2 is missing
                    if pd.notna(row['&']) and row['&'] == '&' and (pd.isna(row['Last Name #2']) or pd.isna(row['First Name #2'])):
                        self.validation_warnings.append(
                            f"Row {idx+2}: Has '&' indicator but missing second owner information"
                        )
                    # Check if Last Name #2 is provided but & indicator is missing
                    elif (pd.notna(row['Last Name #2']) or pd.notna(row['First Name #2'])) and (pd.isna(row['&']) or row['&'] != '&'):
                        self.validation_warnings.append(
                            f"Row {idx+2}: Has second owner information but missing '&' indicator"
                        )
            
            # Check for malformed organization entries (should use ORG: prefix)
            if 'Last Name #1' in data.columns and 'First Name #1' in data.columns:
                for idx, row in data.iterrows():
                    name = str(row['Last Name #1']).strip() if pd.notna(row['Last Name #1']) else ""
                    
                    # Check for organizations that might not be correctly formatted
                    if len(name.split()) > 2 and not name.startswith('ORG:'):
                        if pd.isna(row['First Name #1']) or str(row['First Name #1']).strip() == "":
                            # This is likely an organization name that should use the ORG: prefix
                            self.validation_warnings.append(
                                f"Row {idx+2}: '{name}' appears to be an organization but doesn't use 'ORG:' prefix"
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
        """Create a SimplifilePackage from an Excel row with county-specific processing"""
        # First create the package with basic information
        package = SimplifilePackage.from_excel_row({
            'Account': self.get_cell_value(row, 'Account'),
            'KC File No.': self.get_cell_value(row, 'KC File No.'),
            'Last Name #1': self.get_cell_value(row, 'Last Name #1'),
            'First Name #1': self.get_cell_value(row, 'First Name #1'),
            'GRANTOR/GRANTEE': self.get_cell_value(row, 'GRANTOR/GRANTEE')
        }, row_index, self.county_id)
        
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
        
        # Get county configuration
        county_config = self.county_config
        
        # Create deed document with county-specific type
        deed_document = SimplifileDocument()
        deed_document.set_county_config(self.county_id)
        deed_document.document_id = f"D-{package.account_number}-TD"
        
        # Document name based on convention
        if last_name1.startswith("ORG:"):
            deed_document.name = f"{package.account_number} {first_name1} TD"
        else:
            deed_document.name = f"{package.account_number} {last_name1} TD"
        
        # Set document type based on county
        deed_document.type = county_config.DEED_DOCUMENT_TYPE
        
        # Add execution date if required by county
        if county_config.DEED_REQUIRES_EXECUTION_DATE:
            deed_document.execution_date = execution_date
        
        # Add consideration
        deed_document.consideration = consideration
        
        # Add legal description if required by county
        if county_config.DEED_REQUIRES_LEGAL_DESCRIPTION:
            deed_document.legal_descriptions.append(legal_desc)
        
        # Add reference information for deed if required by county
        if county_config.DEED_REQUIRES_REFERENCE_INFO:
            deed_book = self.get_cell_value(row, 'Deed Book', '')
            deed_page = self.get_cell_value(row, 'Deed Page', '')
            
            if deed_book or deed_page:
                deed_ref = ReferenceInformation(county_config.DEED_DOCUMENT_TYPE, deed_book, deed_page)
                deed_document.reference_information.append(deed_ref)
        
        # Add grantors for deed document (following the rules)
        # First, check if King Cunningham is required by county configuration
        if county_config.KING_CUNNINGHAM_REQUIRED_FOR_DEED:
            deed_document.grantors.append(Party(name="KING CUNNINGHAM LLC TR", is_organization=True))
        
        # Add grantor/grantee entity
        if grantor_grantee:
            deed_document.grantors.append(Party(name=grantor_grantee, is_organization=True))
        
        # Add individual owners as grantors
        if first_name1 and last_name1:
            deed_document.grantors.append(Party.from_excel_data(first_name1, last_name1))
            
        if has_second_owner and first_name2 and last_name2:
            deed_document.grantors.append(Party.from_excel_data(first_name2, last_name2))
        
        # Add grantees based on county configuration
        if county_config.DEED_GRANTEES_USE_GRANTOR_GRANTEE and grantor_grantee:
            # Use GRANTOR/GRANTEE entity as grantee (Horry County approach)
            deed_document.grantees.append(Party(name=grantor_grantee, is_organization=True))
        elif county_config.DEED_GRANTEES_USE_OWNERS:
            # Use owners as grantees (Beaufort County approach)
            if first_name1 and last_name1:
                deed_document.grantees.append(Party.from_excel_data(first_name1, last_name1))
                
            if has_second_owner and first_name2 and last_name2:
                deed_document.grantees.append(Party.from_excel_data(first_name2, last_name2))
        
        # Create mortgage satisfaction document
        mortgage_document = SimplifileDocument()
        mortgage_document.set_county_config(self.county_id)
        mortgage_document.document_id = f"D-{package.account_number}-SAT"
        
        # Document name based on convention
        if last_name1.startswith("ORG:"):
            mortgage_document.name = f"{package.account_number} {first_name1} SAT"
        else:
            mortgage_document.name = f"{package.account_number} {last_name1} SAT"
        
        # Set mortgage document type based on county
        mortgage_document.type = county_config.MORTGAGE_DOCUMENT_TYPE
        
        # Add execution date if required by county
        if county_config.MORTGAGE_REQUIRES_EXECUTION_DATE:
            mortgage_document.execution_date = execution_date
        
        # Add legal description if required by county
        if county_config.MORTGAGE_REQUIRES_LEGAL_DESCRIPTION:
            mortgage_document.legal_descriptions.append(legal_desc)
        
        # Add reference information for mortgage satisfaction if required by county
        if county_config.MORTGAGE_REQUIRES_REFERENCE_INFO:
            mortgage_book = self.get_cell_value(row, 'Mortgage Book', '')
            mortgage_page = self.get_cell_value(row, 'Mortgage Page', '')
            
            if mortgage_book or mortgage_page:
                mortgage_ref = ReferenceInformation(county_config.MORTGAGE_DOCUMENT_TYPE, mortgage_book, mortgage_page)
                mortgage_document.reference_information.append(mortgage_ref)
        
        # Add grantors for mortgage document (only individuals, NOT KING CUNNINGHAM LLC TR)
        # First, add individual owners
        if first_name1 and last_name1:
            mortgage_document.grantors.append(Party.from_excel_data(first_name1, last_name1))
            
        if has_second_owner and first_name2 and last_name2:
            mortgage_document.grantors.append(Party.from_excel_data(first_name2, last_name2))
        
        # Add grantee (always from GRANTOR/GRANTEE for mortgages)
        if grantor_grantee:
            mortgage_document.grantees.append(Party(name=grantor_grantee, is_organization=True))
        
        # Add documents to package - use the add_document method to ensure county config is applied
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
        """Validate a package with enhanced checks and set validation status based on county requirements"""
        package.is_valid = True
        package.validation_issues = []
        
        # Validate basic package info
        if not package.account_number:
            package.is_valid = False
            package.validation_issues.append("Missing account number")
        
        if not package.kc_file_no:
            package.is_valid = False
            package.validation_issues.append("Missing KC File No.")
        
        # Check for organization name formatting issues
        if package.grantor_grantee and not package.grantor_grantee.strip().isupper():
            package.validation_issues.append(f"GRANTOR/GRANTEE '{package.grantor_grantee}' should be in ALL CAPS")
            package.is_valid = False
        
        # Get county configuration for validation
        county_config = package.county_config
        
        # Validate documents
        for doc in package.documents:
            doc.is_valid = True
            doc.validation_issues = []
            
            # Check document name is in UPPERCASE
            if doc.name and not doc.name.strip().isupper():
                doc.is_valid = False
                doc.validation_issues.append("Document name should be in ALL CAPS")
                package.is_valid = False
            
            # Check required fields based on document type and county configuration
            if doc.type == county_config.DEED_DOCUMENT_TYPE:
                # Check reference information if required
                if county_config.DEED_REQUIRES_REFERENCE_INFO:
                    if not doc.reference_information or not doc.reference_information[0].book or not doc.reference_information[0].page:
                        doc.is_valid = False
                        doc.validation_issues.append("Missing deed book/page reference")
                        package.is_valid = False
                
                # Check for KING CUNNINGHAM LLC TR as grantor if required
                if county_config.KING_CUNNINGHAM_REQUIRED_FOR_DEED:
                    has_king_cunningham = False
                    for grantor in doc.grantors:
                        if grantor.is_organization and "KING CUNNINGHAM LLC TR" in grantor.name:
                            has_king_cunningham = True
                            break
                            
                    if not has_king_cunningham:
                        doc.is_valid = False
                        doc.validation_issues.append("Missing required grantor: KING CUNNINGHAM LLC TR")
                        package.is_valid = False
                
                # Check legal description if required
                if county_config.DEED_REQUIRES_LEGAL_DESCRIPTION:
                    if not doc.legal_descriptions or not doc.legal_descriptions[0].description.strip():
                        doc.is_valid = False
                        doc.validation_issues.append("Missing legal description")
                        package.is_valid = False
            
            elif doc.type == county_config.MORTGAGE_DOCUMENT_TYPE:
                # Check reference information if required
                if county_config.MORTGAGE_REQUIRES_REFERENCE_INFO:
                    if not doc.reference_information or not doc.reference_information[0].book or not doc.reference_information[0].page:
                        doc.is_valid = False
                        doc.validation_issues.append("Missing mortgage book/page reference")
                        package.is_valid = False
                
                # Check that KING CUNNINGHAM LLC TR is NOT a grantor for mortgage satisfaction
                for grantor in doc.grantors:
                    if grantor.is_organization and "KING CUNNINGHAM LLC TR" in grantor.name:
                        doc.is_valid = False
                        doc.validation_issues.append("KING CUNNINGHAM LLC TR should not be a grantor for Mortgage Satisfaction")
                        package.is_valid = False
                        break
                
                # Check legal description if required
                if county_config.MORTGAGE_REQUIRES_LEGAL_DESCRIPTION:
                    if not doc.legal_descriptions or not doc.legal_descriptions[0].description.strip():
                        doc.is_valid = False
                        doc.validation_issues.append("Missing legal description")
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