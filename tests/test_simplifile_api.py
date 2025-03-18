import requests
import base64
import json
import os
from datetime import datetime

# API Configuration
api_url = "https://api.simplifile.com/sf/rest/api/erecord/submitters/SCTP3G/packages/create"
api_token = "4FFHQQNYENLNVUNL3XPDZIGG3<*>wWmUac/DY3vcJKvrfmUlzPivb3HBpoA7PzfHf4kUfLk="  # Replace with your actual token

# Document Data
contract_number = "TEST123"
document_number = "001"
package_name = f"Test Package - {datetime.now().strftime('%Y%m%d%H%M%S')}"

# Read and encode a PDF file
def get_base64_encoded_file(file_path):
    with open(file_path, "rb") as pdf_file:
        encoded_string = base64.b64encode(pdf_file.read())
        return encoded_string.decode('utf-8')

# Replace with path to your test PDF
pdf_file_path = r"D:\repositorys\KC_appp\tests\93-21 TD.pdf"
encoded_document = get_base64_encoded_file(pdf_file_path)

# Prepare the request payload
payload = {
    "documents": [
        {
            "submitterDocumentID": f"D-{contract_number}-{document_number}",
            "name": f"{contract_number}-{document_number}",
            "kindOfInstrument": [
                "Deed-Timeshare"
            ],
            "indexingData": {
                "consideration": "100000.00",
                "executionDate": datetime.now().strftime('%m/%d/%Y'),
                "grantors": [
                    {
                        "nameUnparsed": "TEST DEVELOPMENT LLC",
                        "type": "ORGANIZATION"
                    }
                ],
                "grantees": [
                    {
                        "firstName": "John",
                        "middleName": "",
                        "lastName": "Doe",
                        "type": "PERSON"
                    },
                    {
                        "firstName": "Jane",
                        "lastName": "Doe",
                        "type": "PERSON"
                    }
                ],
                "legalDescriptions": [
                    {
                        "description": "TEST PROPERTY UNIT 123 WEEK 45",
                        "parcelId": "1810418003"  # Use appropriate parcel ID for your county
                    }
                ]
            },
            "fileBytes": [
                encoded_document
            ]
        }
    ],
    "recipient": "SCCP49",  # County code
    "submitterPackageID": f"P-{contract_number}-{document_number}",
    "name": package_name,
    "operations": {
        "draftOnErrors": True,
        "submitImmediately": False,
        "verifyPageMargins": True
    }
}

# Set up the headers
headers = {
    "Content-Type": "application/json",
    "api_token": api_token
}

# Make the API request
try:
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    
    # Print the response
    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
    
    # Check if successful
    if response.status_code == 200 and response.json().get("resultCode") == "SUCCESS":
        print("Document submitted successfully!")
    else:
        print("Document submission failed.")
        
except Exception as e:
    print(f"Error occurred: {str(e)}")