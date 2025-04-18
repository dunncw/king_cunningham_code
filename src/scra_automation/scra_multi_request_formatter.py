# File: scra_automation/scra_multi_request_formatter.py
import pandas as pd
from datetime import datetime
import os
import re

class SCRAMultiRequestFormatter:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        
    def validate_ssn(self, ssn):
        """Validate SSN format and length"""
        if pd.isna(ssn):
            return False

        # Convert to string and remove decimal point and trailing zeros
        ssn_str = str(ssn).split('.')[0]

        # Remove any non-digit characters
        ssn_clean = re.sub(r'\D', '', ssn_str)

        # Check if it's exactly 9 digits
        return len(ssn_clean) == 9

    def format_ssn(self, ssn):
        """Format SSN to standard format"""
        # Convert to string and remove decimal point and trailing zeros
        ssn_str = str(ssn).split('.')[0]
        
        # Remove any non-digit characters
        ssn_clean = re.sub(r'\D', '', ssn_str)
        
        return ssn_clean.zfill(9)

    def validate_name(self, name):
        """Validate name according to SCRA requirements."""
        if pd.isna(name):
            return False

        # Convert to string
        name_str = str(name).strip()

        # Check if empty after stripping
        if not name_str:
            return False

        # Check if name contains only allowed characters (letters, spaces, dashes, apostrophes)
        allowed_pattern = r'^[A-Za-z\s\-\']+$'
        return bool(re.match(allowed_pattern, name_str))

    def format_name(self, name, field_length):
        """Format name to fixed width field."""
        name_str = str(name).strip()
        # Left justify and pad with spaces
        return name_str.ljust(field_length)

    def format_account_number(self, account_number, suffix):
        """Format account number to exactly 20 characters including suffix"""
        # Convert account number to string and remove any whitespace
        acct_str = str(account_number).strip()
        
        # Remove any non-alphanumeric characters except hyphen
        acct_clean = re.sub(r'[^A-Za-z0-9\-]', '', acct_str)
        
        # Add the suffix (1 or 2)
        acct_with_suffix = f"{acct_clean}{suffix}"
        
        # Pad with spaces to exactly 20 characters
        return acct_with_suffix.ljust(28)

    def process_excel(self):
        """Process the Excel file and create formatted text file."""
        try:
            # Read Excel file
            df = pd.read_excel(self.input_file)
            
            # Get current date for active duty status date
            current_date = datetime.now().strftime('%Y%m%d')
            
            # Open output file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Process each row
                for index, row in df.iterrows():
                    # Process person 1
                    if self.validate_ssn(row['SSN 1']) and self.validate_name(row['Last Name 1']):
                        line = (
                            f"{self.format_ssn(row['SSN 1'])}"        # SSN (9)
                            f"{''.ljust(8)}"                          # Date of Birth (8) - blank
                            f"{self.format_name(row['Last Name 1'], 26)}"  # Last Name (26)
                            f"{''.ljust(20)}"                         # First Name (20) - blank
                            f"{self.format_account_number(row['Account #'], '1')}"  # Customer Record ID (20)
                            f"{current_date}"                         # Active Duty Status Date (8)
                            f"{''.ljust(20)}\n"                      # Middle Name (20) - blank
                        )
                        f.write(line)
                    
                    # Process person 2
                    if self.validate_ssn(row['SSN 2']) and self.validate_name(row['Last Name 2']):
                        line = (
                            f"{self.format_ssn(row['SSN 2'])}"        # SSN (9)
                            f"{''.ljust(8)}"                          # Date of Birth (8) - blank
                            f"{self.format_name(row['Last Name 2'], 26)}"  # Last Name (26)
                            f"{''.ljust(20)}"                         # First Name (20) - blank
                            f"{self.format_account_number(row['Account #'], '2')}"  # Customer Record ID (20)
                            f"{current_date}"                         # Active Duty Status Date (8)
                            f"{''.ljust(20)}\n"                      # Middle Name (20) - blank
                        )
                        f.write(line)

            return True, "Processing completed successfully"
            
        except Exception as e:
            return False, f"Error processing file: {str(e)}"

def main():
    # Test the processor with hardcoded paths
    input_file = r"D:\repositorys\KC_appp\task\pacer_scra\data\in\zSSN_long.xlsx"
    output_file = r"D:\repositorys\KC_appp\task\pacer_scra\data\out\output.txt"

    print(f"Processing Excel file: {input_file}")
    print(f"Output will be saved to: {output_file}")

    processor = SCRAMultiRequestFormatter(input_file, output_file)
    success, message = processor.process_excel()

    if success:
        print("Success:", message)
        print(f"Output file created at: {output_file}")
    else:
        print("Error:", message)

if __name__ == "__main__":
    main()