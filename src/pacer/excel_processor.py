# File: pacer/excel_processor.py
import pandas as pd
import re
from typing import Dict, List, Tuple, Union

class PACERExcelProcessor:
    VALID_RESULTS = ["No Bankruptcy", "Closed Bankruptcy", "OPEN Bankruptcy Found"]
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.df = None

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
            # Read Excel file
            self.df = pd.read_excel(self.excel_path)
            
            # Add result columns if they don't exist
            if 'Person_1_Results' not in self.df.columns:
                self.df['Person_1_Results'] = ''
            if 'Person_2_Results' not in self.df.columns:
                self.df['Person_2_Results'] = ''
            
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

    def update_results(self, row_index: int, person_number: int, result: str, is_open_bankruptcy: bool = False) -> Tuple[bool, str]:
        """Update results for a specific person in the Excel file"""
        try:
            # Update the DataFrame
            result_column = f'Person_{person_number}_Results'
            
            # If it's an open bankruptcy, add highlighting in Excel
            if is_open_bankruptcy:
                # Apply red background and white text in Excel
                self.df.at[row_index, result_column] = result
                try:
                    # Try to apply style if openpyxl is available
                    import openpyxl
                    from openpyxl.styles import PatternFill, Font
                    
                    # We'll need to save and reload the file to apply styles
                    self.save_excel()
                    wb = openpyxl.load_workbook(self.excel_path)
                    ws = wb.active
                    
                    # Find the cell (add 2 because Excel is 1-based and we have headers)
                    cell = ws.cell(row=row_index + 2, column=self.df.columns.get_loc(result_column) + 1)
                    
                    # Apply red background with white text
                    cell.fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                    cell.font = Font(color="FFFFFF")
                    
                    wb.save(self.excel_path)
                except ImportError:
                    # If openpyxl isn't available, just save the regular way
                    self.save_excel()
            else:
                self.df.at[row_index, result_column] = result
                self.save_excel()
                
            return True, "Results updated successfully"
        except Exception as e:
            return False, f"Error updating results: {str(e)}"

    def save_excel(self) -> bool:
        """Save the Excel file with updates"""
        try:
            self.df.to_excel(self.excel_path, index=False)
            return True
        except Exception as e:
            print(f"Error saving Excel file: {str(e)}")
            return False