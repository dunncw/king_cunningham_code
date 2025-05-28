# File: scra_automation/scra_multi_request_formatter.py
import pandas as pd
from datetime import datetime
import os
import re

class SCRAMultiRequestFormatter:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.validation_errors = []  # Track validation errors
        self.dropped_records = []    # Track specifically dropped records
        self.cleaned_records = []    # Track records that had characters scrubbed
        
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

    def clean_name(self, name, row_index, person_num):
        """Clean and validate name according to SCRA requirements."""
        if pd.isna(name):
            self.validation_errors.append(
                f"Row {row_index + 2}: Last Name {person_num} is empty"
            )
            return None, False

        # Convert to string
        name_str = str(name).strip()

        # Check if empty after stripping
        if not name_str:
            self.validation_errors.append(
                f"Row {row_index + 2}: Last Name {person_num} is empty"
            )
            return None, False

        # Check if name contains invalid characters
        allowed_pattern = r'^[A-Za-z\s\-\']+$'
        if not bool(re.match(allowed_pattern, name_str)):
            original_name = name_str
            # Remove any character that's not a letter, space, dash, or apostrophe
            cleaned_name = re.sub(r'[^A-Za-z\s\-\']', '', name_str)
            
            # Track this cleaning operation
            self.cleaned_records.append({
                'row': row_index + 2,
                'original': original_name,
                'cleaned': cleaned_name,
                'person': person_num
            })
            
            self.validation_errors.append(
                f"Row {row_index + 2}: Last Name {person_num} '{original_name}' contained invalid characters and was automatically cleaned to '{cleaned_name}'"
            )
            
            name_str = cleaned_name

        # Check if name exceeds 26 characters
        if len(name_str) > 26:
            error_msg = f"Row {row_index + 2}: Last Name {person_num} '{name_str}' exceeds maximum length of 26 characters (current length: {len(name_str)})"
            self.validation_errors.append(error_msg)
            self.dropped_records.append({
                'row': row_index + 2,
                'name': name_str,
                'reason': f"Last name exceeds 26 characters (length: {len(name_str)})",
                'person': person_num
            })
            return None, False

        return name_str, True

    def validate_ssn_with_reporting(self, ssn, row_index, person_num):
        """Validate SSN with error reporting"""
        if pd.isna(ssn):
            self.validation_errors.append(
                f"Row {row_index + 2}: SSN {person_num} is empty"
            )
            return False

        ssn_str = str(ssn).split('.')[0]
        ssn_clean = re.sub(r'\D', '', ssn_str)

        if len(ssn_clean) != 9:
            self.validation_errors.append(
                f"Row {row_index + 2}: SSN {person_num} '{ssn_str}' must be exactly 9 digits (current length: {len(ssn_clean)})"
            )
            return False

        return True

    def format_name(self, name, field_length):
        """Format name to fixed width field."""
        name_str = str(name).strip()
        
        # If name is longer than field_length, return None to indicate it should be dropped
        if len(name_str) > field_length:
            return None
            
        # Left justify and pad with spaces
        return name_str.ljust(field_length)

    def format_account_number(self, account_number, suffix):
        """Format account number to exactly 28 characters including suffix"""
        # Convert account number to string and remove any whitespace
        acct_str = str(account_number).strip()
        
        # Remove any non-alphanumeric characters except hyphen
        acct_clean = re.sub(r'[^A-Za-z0-9\-]', '', acct_str)
        
        # Add the suffix (1 or 2)
        acct_with_suffix = f"{acct_clean}{suffix}"
        
        # Pad with spaces to exactly 28 characters
        return acct_with_suffix.ljust(28)

    def process_excel(self):
        """Process the Excel file and create formatted text file."""
        try:
            # Clear previous validation errors and dropped records
            self.validation_errors = []
            self.dropped_records = []
            self.cleaned_records = []
            
            # Read Excel file
            df = pd.read_excel(self.input_file)
            
            # Get current date for active duty status date
            current_date = datetime.now().strftime('%Y%m%d')
            
            # Track processed and dropped records
            processed_count = 0
            
            # Open output file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # Process each row
                for index, row in df.iterrows():
                    # Process person 1
                    if self.validate_ssn(row['SSN 1']):
                        cleaned_name, is_valid = self.clean_name(row['Last Name 1'], index, 1)
                        if is_valid:
                            formatted_last_name = self.format_name(cleaned_name, 26)
                            if formatted_last_name is not None:
                                line = (
                                    f"{self.format_ssn(row['SSN 1'])}"        # SSN (9)
                                    f"{''.ljust(8)}"                          # Date of Birth (8) - blank
                                    f"{formatted_last_name}"                  # Last Name (26)
                                    f"{''.ljust(20)}"                         # First Name (20) - blank
                                    f"{self.format_account_number(row['Account #'], '1')}"  # Customer Record ID (28)
                                    f"{current_date}"                         # Active Duty Status Date (8)
                                    f"{''.ljust(20)}\n"                      # Middle Name (20) - blank
                                )
                                f.write(line)
                                processed_count += 1
                    
                    # Process person 2
                    if pd.notna(row.get('SSN 2')) and pd.notna(row.get('Last Name 2')):  # Only process if person 2 exists
                        if self.validate_ssn(row['SSN 2']):
                            cleaned_name, is_valid = self.clean_name(row['Last Name 2'], index, 2)
                            if is_valid:
                                formatted_last_name = self.format_name(cleaned_name, 26)
                                if formatted_last_name is not None:
                                    line = (
                                        f"{self.format_ssn(row['SSN 2'])}"        # SSN (9)
                                        f"{''.ljust(8)}"                          # Date of Birth (8) - blank
                                        f"{formatted_last_name}"                  # Last Name (26)
                                        f"{''.ljust(20)}"                         # First Name (20) - blank
                                        f"{self.format_account_number(row['Account #'], '2')}"  # Customer Record ID (28)
                                        f"{current_date}"                         # Active Duty Status Date (8)
                                        f"{''.ljust(20)}\n"                      # Middle Name (20) - blank
                                    )
                                    f.write(line)
                                    processed_count += 1

            # Prepare summary message
            summary = []
            summary.append("SCRA Batch Processing Summary:")
            summary.append(f"Total records processed successfully: {processed_count}")
            
            if self.cleaned_records:
                summary.append("\n⚠️ MODIFIED RECORDS (These were automatically cleaned and included in the batch):")
                for record in self.cleaned_records:
                    summary.append(f"⚠️ MODIFIED - Row {record['row']}: '{record['original']}' → '{record['cleaned']}' (Person {record['person']})")
            
            if self.dropped_records:
                summary.append("\n⚠️ DROPPED RECORDS (These will not be included in the SCRA batch):")
                for record in self.dropped_records:
                    summary.append(f"⚠️ DROPPED - Row {record['row']}: {record['name']} (Person {record['person']}) - {record['reason']}")
            
            if self.validation_errors:
                other_errors = [err for err in self.validation_errors if "exceeds maximum length" not in err and "contained invalid characters" not in err]
                if other_errors:
                    summary.append("\nOther Validation Warnings (records will still be processed):")
                    for error in other_errors:
                        summary.append(f"⚠️ {error}")
            
            return True, "\n".join(summary)
            
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
        print("\n" + message)  # Print validation summary
        print(f"\nOutput file created at: {output_file}")
    else:
        print("Error:", message)

if __name__ == "__main__":
    main()