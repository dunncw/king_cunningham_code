# File: scra_automation/scra_results_interp.py
from datetime import datetime
import pandas as pd
import os

class SCRAResultsInterpreter:
    def __init__(self, results_file):
        self.results_file = results_file

        # Define field positions based on the fixed-width format
        self.fields = {
            'ssn': (0, 9),
            'dob': (9, 17),
            'last_name': (17, 43),
            'first_name': (43, 63),
            'customer_record_id': (63, 83),
            'active_duty_status_date': (83, 91),
            'on_active_duty': (91, 92),
            'left_active_duty': (92, 93),
            'future_call_up': (93, 94),
            'active_duty_end_date': (94, 102),
            'match_result_code': (102, 103),
            'error_code': (103, 104),
            'date_of_match': (104, 112),
            'active_duty_begin_date': (112, 120),
            'eid_begin_date': (120, 128),
            'eid_end_date': (128, 136),
            'service_component': (136, 138),
            'eid_service_component': (138, 140),
            'middle_name': (140, 160),
            'certificate_id': (160, 185)
        }
        
        # Define interpretation mappings
        self.active_duty_status = {
            'Y': 'Yes, was on active duty and that period has ended',
            'X': 'Yes, currently on active duty',
            'N': 'No, not on active duty',
            'Z': 'Data input issue'
        }
        
        self.left_active_duty_status = {
            'Y': 'Yes, left active duty within 367 days prior',
            'N': 'No, did not leave active duty within 367 days prior',
            'Z': 'Not applicable or error'
        }
        
        self.future_call_up_status = {
            'Y': 'Yes, date falls within future call-up period',
            'N': 'No future call-up notification',
            'Z': 'Not applicable or error'
        }
        
        self.error_codes = {
            '1': 'Missing required field',
            '2': 'Invalid SSN',
            '3': 'Invalid date',
            '4': 'Multiple Records',
            '9': 'No Errors',
            'B': 'Invalid date of birth',
            'D': 'Invalid first name',
            'E': 'Invalid customer ID',
            'G': 'Invalid middle name'
        }
        
        self.service_components = {
            'AG': 'Army National Guard',
            'AJ': 'Army Cadet',
            'AR': 'Army Active Duty',
            'AV': 'Army Reserve',
            'AZ': 'Army affiliate',
            'CJ': 'Coast Guard Cadet',
            'CR': 'Coast Guard Active Duty',
            'CV': 'Coast Guard Reserve',
            'CZ': 'Coast Guard affiliate',
            'FG': 'Air National Guard',
            'FJ': 'Air Force Cadet',
            'FR': 'Air Force Active Duty',
            'FV': 'Air Force Reserve',
            'HR': 'Public Health Services',
            'MR': 'Marines Corps Active Duty',
            'MV': 'Marine Corps Reserve',
            'MZ': 'Marine Corps affiliate',
            'NJ': 'Navy Cadet',
            'NR': 'Navy Active Duty',
            'NV': 'Navy Reserve',
            'OR': 'National Oceanic & Atmospheric Administration Active',
            'SR': 'Space Force Active Duty',
            'SV': 'Space Force Reserve',
            'ZZ': 'Other'
        }

    def format_date(self, date_str):
        """Format date string if it's valid, otherwise return 'N/A'."""
        if date_str and date_str.strip() != '00000000':
            try:
                return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            except ValueError:
                return 'N/A'
        return 'N/A'

    def extract_field(self, line, field):
        """Extract a field from the fixed-width line with raw debug output."""
        start, end = self.fields[field]
        value = line[start:end]  # Removed .strip() to show raw output
        print(f"Field: {field:<25} | Position: {start:>3}-{end:<3} | Raw Value: '{value}'")
        return value.strip()  # Still return stripped value for processing

    def interpret_record(self, line):
        """Interpret a single record from the results file."""
        print("\n" + "="*80)
        print(f"Processing line of length: {len(line)}")
        print(f"Raw line: '{line}'")  # Added to see the complete raw line
        print("="*80)
        
        # Extract basic information
        ssn = self.extract_field(line, 'ssn')
        customer_id = self.extract_field(line, 'customer_record_id')
        last_name = self.extract_field(line, 'last_name')
        first_name = self.extract_field(line, 'first_name')
        middle_name = self.extract_field(line, 'middle_name')
        
        # Extract dates
        dob = self.extract_field(line, 'dob')
        active_duty_status_date = self.extract_field(line, 'active_duty_status_date')
        active_duty_end_date = self.extract_field(line, 'active_duty_end_date')
        active_duty_begin_date = self.extract_field(line, 'active_duty_begin_date')
        date_of_match = self.extract_field(line, 'date_of_match')
        eid_begin_date = self.extract_field(line, 'eid_begin_date')
        eid_end_date = self.extract_field(line, 'eid_end_date')
        
        # Extract status codes
        active_duty = self.extract_field(line, 'on_active_duty')
        left_active = self.extract_field(line, 'left_active_duty')
        future_call = self.extract_field(line, 'future_call_up')
        error_code = self.extract_field(line, 'error_code')
        
        # Get service information
        service_comp = self.extract_field(line, 'service_component')
        eid_service_comp = self.extract_field(line, 'eid_service_component')
        certificate_id = self.extract_field(line, 'certificate_id')
        
        print("="*80)

        # Create interpretation summary
        summary = {
            'SSN': ssn,
            'Customer ID': customer_id,
            'Last Name': last_name,
            'Status': self.active_duty_status.get(active_duty, 'Unknown'),
            'Left Active Duty Status': self.left_active_duty_status.get(left_active, 'Unknown'),
            'Future Call-up': self.future_call_up_status.get(future_call, 'Unknown'),
            'Error Status': self.error_codes.get(error_code, 'Unknown Error'),
            'Service Component': self.service_components.get(service_comp, 'Unknown'),
            'Active Duty Begin': self.format_date(active_duty_begin_date),
            'Active Duty End': self.format_date(active_duty_end_date),
            'Match Date': self.format_date(date_of_match),
            'Raw Status Code': active_duty
        }
        
        return summary

        # Create interpretation summary
        summary = {
            'SSN': ssn,
            'Customer ID': customer_id,
            'Last Name': last_name,
            'Status': self.active_duty_status.get(active_duty, 'Unknown'),
            'Left Active Duty Status': self.left_active_duty_status.get(left_active, 'Unknown'),
            'Future Call-up': self.future_call_up_status.get(future_call, 'Unknown'),
            'Error Status': self.error_codes.get(error_code, 'Unknown Error'),
            'Service Component': self.service_components.get(service_comp, 'Unknown'),
            'Active Duty Begin': self.format_date(active_duty_begin_date),
            'Active Duty End': self.format_date(active_duty_end_date),
            'Match Date': self.format_date(date_of_match),
            'Raw Status Code': active_duty
        }
        
        return summary

    def process_results(self):
        """Process the entire results file and return interpretations."""
        try:
            results = []
            with open(self.results_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(line.strip()) >= 180:  # Ensure line meets minimum length
                        results.append(self.interpret_record(line))
            return True, results
        except Exception as e:
            return False, f"Error processing results file: {str(e)}"

    def print_summary(self, results):
        """Print formatted summary of results to console."""
        for record in results:
            # Check if it's a match (X or Y for active duty, or Y for left active duty)
            is_match = (record['Raw Status Code'] in ['X', 'Y'] or 
                       (record['Raw Status Code'] == 'N' and 
                        record['Left Active Duty Status'].startswith('Yes')))

            # For non-matches, print single line
            if not is_match:
                print(f"Account: {record['Customer ID']} | SSN: {record['SSN']} | Status: No military match found")
                continue

            # For matches, print detailed information
            print(f"\n=== MILITARY MATCH FOUND ===")
            print(f"Account: {record['Customer ID']}")
            print(f"SSN: {record['SSN']}")
            print(f"Last Name: {record['Last Name']}")
            print(f"Status: {record['Status']}")
            
            if record['Error Status'] != 'No Errors':
                print(f"⚠️ Error: {record['Error Status']}")
            
            if record['Raw Status Code'] in ['X', 'Y']:
                print(f"Service: {record['Service Component']}")
                print(f"Active Duty Begin Date: {record['Active Duty Begin']}")
                if record['Raw Status Code'] == 'Y':
                    print(f"Active Duty End Date: {record['Active Duty End']}")
            
            if record['Future Call-up'].startswith('Yes'):
                print("⚠️ Notice: Individual has received future call-up orders")
            
            print(f"Match Date: {record['Match Date']}")
            print("=" * 30)

def main():
    # Test the interpreter with a hardcoded path
    results_file = r"D:\repositorys\KC_appp\task\pacer_scra\data\in\srca_batch_results.txt"
    
    print(f"Processing SCRA results file: {results_file}")
    
    interpreter = SCRAResultsInterpreter(results_file)
    success, results = interpreter.process_results()
    
    if success:
        interpreter.print_summary(results)
    else:
        print("Error:", results)

if __name__ == "__main__":
    main()