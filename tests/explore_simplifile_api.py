import requests
import json
import os
from datetime import datetime

def get_recipient_requirements(recipient_code):
    """
    Queries the Simplifile API for recipient requirements and saves the response to a JSON file.
    
    Parameters:
    - recipient_code: The code of the recipient (e.g., 'SCCP49')
    
    Returns:
    - True if successful, False otherwise
    """
    # Your Simplifile API token
    api_token = "4FFHQQNYENLNVUNL3XPDZIGG3<*>wWmUac/DY3vcJKvrfmUlzPivb3HBpoA7PzfHf4kUfLk="
    
    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "api_token": api_token
    }
    
    # Construct the URL
    base_url = "https://api.simplifile.com/sf/rest/api"
    url = f"{base_url}/erecord/recipients/{recipient_code}/requirements"
    
    try:
        print(f"Querying requirements for recipient {recipient_code}...")
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code < 400:
            try:
                data = response.json()
                
                # Create filename with timestamp for uniqueness
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"simplifile_{recipient_code}_requirements_{timestamp}.json"
                
                # Save to JSON file with pretty formatting
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
                
                print(f"Successfully saved requirements to {filename}")
                return True
                
            except json.JSONDecodeError:
                print("Error: Response is not valid JSON")
                print(f"Response content: {response.text[:500]}...")
                return False
        else:
            print(f"Error: Request failed with status code {response.status_code}")
            print(f"Response content: {response.text[:500]}...")
            return False
            
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False

if __name__ == "__main__":
    # You can change this to query different recipients
    recipient_code = "SCCP49"
    
    result = get_recipient_requirements(recipient_code)
    
    if result:
        print("Operation completed successfully")
    else:
        print("Operation failed")