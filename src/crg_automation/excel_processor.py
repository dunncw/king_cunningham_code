import pandas as pd
import os

class ExcelProcessor:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_excel_file(self):
        _, file_extension = os.path.splitext(self.file_path)
        if file_extension.lower() not in ['.xlsx', '.xls', '.xlsm']:
            raise ValueError(f"Unsupported file format: {file_extension}. Please use .xlsx, .xls, or .xlsm files.")

        if file_extension.lower() == '.xlsm':
            return pd.ExcelFile(self.file_path, engine='openpyxl')
        else:
            return pd.ExcelFile(self.file_path)

    def process_excel(self, sheet_name='Contracts'):
        try:
            excel_file = self.read_excel_file()
            
            if sheet_name not in excel_file.sheet_names:
                raise ValueError(f"Sheet '{sheet_name}' not found in the Excel file.")

            df = excel_file.parse(sheet_name)

            # Update these column names based on the actual headers in your file
            sales_site_column = 'Sales Site'
            account_number_column = 'Account Number'

            if sales_site_column not in df.columns or account_number_column not in df.columns:
                raise ValueError(f"Required columns '{sales_site_column}' and/or '{account_number_column}' not found in the Excel file.")

            # Filter the dataframe to only include rows where 'Project' is 'Myrtle Beach'
            filtered_df = df[df[sales_site_column] == 'Myrtle Beach']

            # Extract the account numbers into a list, converting to integers
            account_numbers = filtered_df[account_number_column].astype(int).tolist()

            return account_numbers
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")

if __name__ == "__main__":
    # This block allows you to test the function independently
    test_excel_path = r"data\raw\capital_ventures\Closing Worksheet SBO-CP-216.xlsm"
    
    print(f"Processing Excel file: {test_excel_path}")
    
    try:
        processor = ExcelProcessor(test_excel_path)
        account_numbers = processor.process_excel()
        print(f"Number of account numbers found for Myrtle Beach: {len(account_numbers)}")
        print("Account numbers:")
        print(account_numbers)
    except Exception as e:
        print(f"Error: {str(e)}")