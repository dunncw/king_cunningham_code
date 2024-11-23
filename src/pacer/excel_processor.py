# File: pacer/excel_processor.py
import pandas as pd
import re
from typing import Dict, List, Tuple, Union
import openpyxl
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

class PACERExcelProcessor:
    VALID_RESULTS = ["No Bankruptcy", "Closed Bankruptcy", "OPEN Bankruptcy Found"]
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = None
        self.cells_to_highlight = []

    def validate_ssn(self, ssn) -> bool:
        """Validate SSN format and length"""
        if pd.isna(ssn):
            return False

        # Convert to string and remove decimal point and trailing zeros
        ssn_str = str(ssn).split('.')[0]
        
        # Remove any non-digit characters
        ssn_clean = re.sub(r'\D', '', ssn_str)
        
        # Check if it's exactly 9 digits
        return len(ssn_clean) == 9

    def format_ssn(self, ssn) -> str:
        """Format SSN to standard format"""
        # Convert to string and remove decimal point and trailing zeros
        ssn_str = str(ssn).split('.')[0]
        
        # Remove any non-digit characters
        ssn_clean = re.sub(r'\D', '', ssn_str)
        
        # Return formatted SSN
        return ssn_clean  # Return just the numbers for API use

    def needs_processing(self, result: str) -> bool:
        """Check if a result needs processing"""
        if pd.isna(result) or not result:
            return True
            
        # Check if the result is not one of our valid results
        if result not in self.VALID_RESULTS:
            return True
            
        return False

    def process_excel(self) -> Tuple[bool, Union[List[Dict], str]]:
        """Process Excel file and return data for processing"""
        try:
            # Read Excel file with string dtype for specific columns
            self.df = pd.read_excel(
                self.excel_path,
                dtype={
                    'Person_1_Results': str,
                    'Person_2_Results': str
                }
            )
            
            # Add result columns if they don't exist
            if 'Person_1_Results' not in self.df.columns:
                self.df['Person_1_Results'] = pd.Series(dtype=str)
            if 'Person_2_Results' not in self.df.columns:
                self.df['Person_2_Results'] = pd.Series(dtype=str)
            
            # Ensure columns are string type even if they existed
            self.df['Person_1_Results'] = self.df['Person_1_Results'].astype(str)
            self.df['Person_2_Results'] = self.df['Person_2_Results'].astype(str)
            
            # Replace 'nan' strings with empty strings
            self.df['Person_1_Results'] = self.df['Person_1_Results'].replace('nan', '')
            self.df['Person_2_Results'] = self.df['Person_2_Results'].replace('nan', '')
            
            # Initialize list to store processed data
            processed_data = []
            
            # Process each row
            for index, row in self.df.iterrows():
                row_data = {
                    "excel_row_index": index,
                    "account_number": row["Account #"] if pd.notna(row["Account #"]) else None,
                    "people": []
                }
                
                # Process person 1
                if (pd.notna(row.get("Last Name 1")) and 
                    self.validate_ssn(row.get("SSN 1")) and 
                    self.needs_processing(row.get('Person_1_Results'))):
                    person1 = {
                        "person_number": 1,
                        "last_name": row["Last Name 1"],
                        "ssn": self.format_ssn(row["SSN 1"])
                    }
                    row_data["people"].append(person1)
                
                # Process person 2
                if (pd.notna(row.get("Last Name 2")) and 
                    self.validate_ssn(row.get("SSN 2")) and 
                    self.needs_processing(row.get('Person_2_Results'))):
                    person2 = {
                        "person_number": 2,
                        "last_name": row["Last Name 2"],
                        "ssn": self.format_ssn(row["SSN 2"])
                    }
                    row_data["people"].append(person2)
                
                # Only add rows that have at least one person to process and an account number
                if row_data["account_number"] and row_data["people"]:
                    processed_data.append(row_data)
            
            # Save the modified Excel file with new columns
            self.save_excel()
            
            return True, processed_data
        except Exception as e:
            return False, f"Error processing Excel file: {str(e)}"

    def update_results(self, row_index: int, person_number: int, result: str) -> Tuple[bool, str]:
        """Update results for a specific person in the Excel file"""
        try:
            # Update DataFrame
            result_column = f'Person_{person_number}_Results'
            self.df.at[row_index, result_column] = result
            
            # If it's an open bankruptcy, store the cell location for later highlighting
            if "OPEN Bankruptcy Found" in result:
                col_idx = self.df.columns.get_loc(result_column) + 1
                row_idx = row_index + 2
                self.cells_to_highlight.append((col_idx, row_idx))
                print(f"DEBUG: Marked cell at column {col_idx}, row {row_idx} for highlighting")
            
            # Save the DataFrame (without formatting)
            self.save_excel()
            
            return True, "Results updated successfully"
            
        except Exception as e:
            print(f"ERROR in update_results: {str(e)}")
            return False, f"Error updating results: {str(e)}"

    def apply_highlighting(self):
        """Apply highlighting to all marked cells at once"""
        if not self.cells_to_highlight:
            return
            
        try:
            print(f"DEBUG: Applying highlighting to {len(self.cells_to_highlight)} cells")
            
            # Load the workbook
            wb = openpyxl.load_workbook(self.excel_path)
            ws = wb.active
            
            # Create the styles
            red_fill = PatternFill(start_color="FF0000", 
                                 end_color="FF0000",
                                 fill_type="solid")
            white_font = Font(color="FFFFFF")
            
            # Apply highlighting to all marked cells
            for col_idx, row_idx in self.cells_to_highlight:
                col_letter = get_column_letter(col_idx)
                cell = ws[f"{col_letter}{row_idx}"]
                
                print(f"DEBUG: Highlighting cell {col_letter}{row_idx}")
                cell.fill = red_fill
                cell.font = white_font
            
            # Save the workbook once with all formatting
            wb.save(self.excel_path)
            print("DEBUG: Successfully applied all highlighting")
            
            # Clear the list of cells to highlight
            self.cells_to_highlight = []
            
        except Exception as e:
            print(f"ERROR applying highlighting: {str(e)}")

    def save_excel(self) -> bool:
        """Save the Excel file with updates"""
        try:
            self.df.to_excel(self.excel_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving Excel file: {str(e)}")
            return False