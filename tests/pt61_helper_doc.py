import requests
import base64
import json
import os
from datetime import datetime

# API Configuration
api_url = "https://api.simplifile.com/sf/rest/api/erecord/submitters/SCTP3G/packages/create"
api_token = "4FFHQQNYENLNVUNL3XPDZIGG3<*>wWmUac/DY3vcJKvrfmUlzPivb3HBpoA7PzfHf4kUfLk="  # Replace with your actual token

# Test Data
contract_number = "FCLTST001"
package_name = f"FCL Helper Test - {datetime.now().strftime('%Y%m%d%H%M%S')}"

# Read and encode PDF files
def get_base64_encoded_file(file_path):
    """Encode a PDF file to base64"""
    with open(file_path, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())
        return encoded_string.decode('utf-8')

# File paths (update these to your test files)
deed_pdf_path = r"D:\repositorys\KC_appp\task\pt61\saves\52200720_JAKEWAY_PT61.pdf"  # 3-page deed
pt61_pdf_path = r"D:\repositorys\KC_appp\task\pt61\saves\392300029_KING_PT61.pdf"  # 1-page PT-61

# Check if files exist
if not os.path.exists(deed_pdf_path):
    print(f"Error: Deed PDF not found at {deed_pdf_path}")
    exit(1)
    
if not os.path.exists(pt61_pdf_path):
    print(f"Error: PT-61 PDF not found at {pt61_pdf_path}")
    exit(1)

# Encode the documents
print("Encoding deed document...")
encoded_deed = get_base64_encoded_file(deed_pdf_path)

print("Encoding PT-61 helper document...")
encoded_pt61 = get_base64_encoded_file(pt61_pdf_path)

# Clean sales price (remove $ and commas)
def clean_sales_price(price_str):
    """Clean sales price string to decimal format"""
    if isinstance(price_str, str):
        return price_str.replace('$', '').replace(',', '')
    return str(price_str)

# Test payload for Fulton County FCL workflow
payload = {
    "documents": [
        {
            "submitterDocumentID": f"D-{contract_number}-DEED",
            "name": f"DOE {contract_number} DEED",
            "kindOfInstrument": ["DEED"],  # Fulton County deed type
            "indexingData": {
                "consideration": clean_sales_price("$21,369.55"),  # Test with formatted price
                "exempt": True,  # Tax exempt always true for foreclosures
                "grantors": [
                    {
                        "firstName": "JOHN",
                        "middleName": "M",
                        "lastName": "DOE", 
                        "type": "Individual"
                    },
                    {
                        "firstName": "JANE",
                        "middleName": "",
                        "lastName": "DOE",
                        "type": "Individual"
                    }
                ],
                "grantees": [
                    {
                        "nameUnparsed": "CENTENNIAL PARK DEVELOPMENT LLC",
                        "type": "Organization"
                    }
                ],
                "legalDescriptions": [
                    {
                        "description": "",  # Empty description as specified
                        "parcelId": "14-0078-0007-096-9"  # Fixed parcel ID for Fulton foreclosures
                    }
                ]
            },
            "fileBytes": [encoded_deed],
            "helperDocuments": [
                {
                    "fileBytes": [encoded_pt61],
                    "helperKindOfInstrument": "PT-61",
                    "isElectronicallyOriginated": False
                }
            ]
        },
        {
            "submitterDocumentID": f"D-{contract_number}-SAT",
            "name": f"DOE {contract_number} SAT", 
            "kindOfInstrument": ["SATISFACTION"],  # Fulton County mortgage satisfaction type
            "indexingData": {
                "grantors": [
                    {
                        "firstName": "JOHN",
                        "middleName": "M", 
                        "lastName": "DOE",
                        "type": "Individual"
                    },
                    {
                        "firstName": "JANE",
                        "middleName": "",
                        "lastName": "DOE", 
                        "type": "Individual"
                    }
                ],
                "grantees": [
                    {
                        "firstName": "JOHN",
                        "middleName": "M",
                        "lastName": "DOE",
                        "type": "Individual" 
                    },
                    {
                        "firstName": "JANE",
                        "middleName": "",
                        "lastName": "DOE",
                        "type": "Individual"
                    }
                ]
            },
            "fileBytes": [encoded_deed]  # Will be mortgage satisfaction PDF in real usage
        }
    ],
    "recipient": "GAC3TH",  # Fulton County recipient ID
    "submitterPackageID": f"P-{contract_number}",
    "name": package_name,
    "operations": {
        "draftOnErrors": True,
        "submitImmediately": False, 
        "verifyPageMargins": True
    }
}

# Set up headers
headers = {
    "Content-Type": "application/json",
    "api_token": api_token
}

# Make the API request
print(f"\nSending test package to Fulton County (GAC3TH)...")
print(f"Package: {package_name}")
print(f"Contract: {contract_number}")

try:
    response = requests.post(api_url, headers=headers, data=json.dumps(payload, indent=2))
    
    print(f"\nStatus Code: {response.status_code}")
    
    # Pretty print the response
    response_data = response.json()
    print("\nAPI Response:")
    print(json.dumps(response_data, indent=2))
    
    # Check result
    if response.status_code == 200:
        result_code = response_data.get("resultCode")
        if result_code == "SUCCESS":
            print("\n✅ SUCCESS: PT-61 helper document test passed!")
            
            # Show package details if available
            if "packages" in response_data:
                for pkg in response_data["packages"]:
                    print(f"Package ID: {pkg.get('packageId')}")
                    print(f"Status: {pkg.get('status')}")
                    
        elif result_code == "DRAFT":
            print("\n📝 DRAFT: Package created as draft (check for validation issues)")
            
        else:
            print(f"\n❌ API ERROR: {result_code}")
            if "message" in response_data:
                print(f"Message: {response_data['message']}")
                
    else:
        print(f"\n❌ HTTP ERROR: {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ REQUEST ERROR: {str(e)}")
    
except json.JSONDecodeError as e:
    print(f"\n❌ JSON DECODE ERROR: {str(e)}")
    print(f"Raw response: {response.text}")
    
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {str(e)}")

print("\n" + "="*50)
print("HELPER DOCUMENT STRUCTURE TESTED:")
print("- Main document: DEED with 3-page PDF")
print("- Helper document: PT-61 with 1-page PDF") 
print("- Structure: helperDocuments array within deed")
print("- Helper fields: fileBytes, helperKindOfInstrument, isElectronicallyOriginated")
print("="*50)