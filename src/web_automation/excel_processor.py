# File: web_automation/excel_processor.py

import pandas as pd
import json
from datetime import datetime

def extract_data_from_excel(excel_path):
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Extract relevant data and create JSON objects
    people_data = []
    for _, row in df.iterrows():
        person = {
            "individual_name": {
                "first": row['First 1'] if pd.notnull(row['First 1']) else "",
                "middle": row['Middle 1'] if pd.notnull(row['Middle 1']) else "",
                "last": row['Last 1'] if pd.notnull(row['Last 1']) else ""
            },
            "additional_name": {
                "first": row['First 2'] if pd.notnull(row['First 2']) else "",
                "middle": row['Middle 2'] if pd.notnull(row['Middle 2']) else "",
                "last": row['Last 2'] if pd.notnull(row['Last 2']) else ""
            },
            "date_on_deed": row['date on deed'].strftime('%m/%d/%Y') if pd.notnull(row['date on deed']) else "",
            "sales_price": f"{row['Sales Price']:.2f}" if pd.notnull(row['Sales Price']) else "",
            "contract_number": str(row['Contract Num']) if pd.notnull(row['Contract Num']) else ""
        }
        people_data.append(person)
    
    return people_data

def print_extracted_data(people_data):
    for i, person in enumerate(people_data):
        print(f"Person {i + 1}:")
        print(json.dumps(person, indent=2))
        print()  # Add a blank line between people

if __name__ == "__main__":
    # This block allows you to test the function independently
    test_excel_path = r"data\raw\WYN B119 Example PT61.xlsx"
    extracted_data = extract_data_from_excel(test_excel_path)
    print_extracted_data(extracted_data)