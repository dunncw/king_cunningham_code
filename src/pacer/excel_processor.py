# File: pacer/excel_processor.py
import pandas as pd
import re

class PACERExcelProcessor:
    def __init__(self, excel_path):
        self.excel_path = excel_path

    def validate_ssn(self, ssn):
        """Validate SSN format and length"""
        if pd.isna(ssn):
            return False
        
        # Remove any non-digit characters
        ssn_clean = re.sub(r'\D', '', str(ssn))
        
        # Check if it's exactly 9 digits
        return len(ssn_clean) == 9

    def format_ssn(self, ssn):
        """Format SSN to standard format"""
        ssn_clean = re.sub(r'\D', '', str(ssn))
        return f"{ssn_clean[:3]}-{ssn_clean[3:5]}-{ssn_clean[5:]}"

    def process_excel(self):
        try:
            # Read Excel file
            df = pd.read_excel(self.excel_path)
            
            # Initialize list to store processed data
            processed_data = []
            
            # Process each row
            for index, row in df.iterrows():
                row_data = {
                    "account_number": row["Account #"] if pd.notna(row["Account #"]) else None,
                    "people": []
                }
                
                # Process person 1
                if pd.notna(row.get("Last Name 1")) and self.validate_ssn(row.get("SSN 1")):
                    person1 = {
                        "last_name": row["Last Name 1"],
                        "ssn": self.format_ssn(row["SSN 1"])
                    }
                    row_data["people"].append(person1)
                
                # Process person 2
                if pd.notna(row.get("Last Name 2")) and self.validate_ssn(row.get("SSN 2")):
                    person2 = {
                        "last_name": row["Last Name 2"],
                        "ssn": self.format_ssn(row["SSN 2"])
                    }
                    row_data["people"].append(person2)
                
                # Only add rows that have at least one valid person and an account number
                if row_data["account_number"] and row_data["people"]:
                    processed_data.append(row_data)
            
            return True, processed_data
        except Exception as e:
            return False, f"Error processing Excel file: {str(e)}"

def main():
    # Test the processor with a sample file
    excel_path = r"D:\repositorys\KC_appp\task\pacer_scra\data\in\z SSN Example.xlsx"
    processor = PACERExcelProcessor(excel_path)
    success, result = processor.process_excel()
    
    if success:
        print("Successfully processed Excel file")
        print("\nProcessed data:")
        for row in result:
            print(f"\nAccount #: {row['account_number']}")
            for person in row['people']:
                print(f"Person: {person['last_name']}, SSN: {person['ssn']}")
    else:
        print(f"Error: {result}")

if __name__ == "__main__":
    main()