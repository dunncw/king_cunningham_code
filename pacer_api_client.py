import requests
import json
from typing import Optional, Dict, Any
from datetime import datetime

class PacerApiClient:
    def __init__(self, environment: str = "qa"):
        """
        Initialize the PACER API client
        
        Args:
            environment (str): Either 'qa' or 'prod' to determine which PACER environment to use
        """
        self.environment = environment
        self.auth_token = None
        self.base_urls = {
            "qa": {
                "auth": "https://qa-login.uscourts.gov",
                "api": "https://qa-pcl.uscourts.gov/pcl-public-api/rest"
            },
            "prod": {
                "auth": "https://pacer.login.uscourts.gov",
                "api": "https://pcl.uscourts.gov/pcl-public-api/rest"
            }
        }

    def authenticate(self, username: str, password: str, client_code: Optional[str] = None) -> bool:
        """
        Authenticate with PACER and get an authentication token
        
        Args:
            username (str): PACER username
            password (str): PACER password
            client_code (str, optional): Client code if required for searching
            
        Returns:
            bool: True if authentication successful, False otherwise
        """
        auth_url = f"{self.base_urls[self.environment]['auth']}/services/cso-auth"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        auth_data = {
            "loginId": username,
            "password": password,
            "redactFlag": "1"  # Required for filers
        }
        
        if client_code:
            auth_data["clientCode"] = client_code
            
        try:
            response = requests.post(auth_url, headers=headers, json=auth_data)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("loginResult") == "0":
                self.auth_token = response_data.get("nextGenCSO")
                return True
            else:
                print(f"Authentication failed: {response_data.get('errorDescription')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"Authentication request failed: {e}")
            return False

    def make_api_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make an authenticated request to the PACER API
        
        Args:
            endpoint (str): API endpoint (starting with /)
            data (dict): Request payload
            
        Returns:
            dict: API response data if successful, None otherwise
        """
        if not self.auth_token:
            print("Not authenticated. Call authenticate() first.")
            return None
            
        url = f"{self.base_urls[self.environment]['api']}{endpoint}"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-NEXT-GEN-CSO": self.auth_token
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def search_bankruptcy_by_ssn(self, ssn: str, date_from: Optional[str] = None, 
                               date_to: Optional[str] = None, 
                               chapters: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """
        Search for bankruptcy cases by SSN
        
        Args:
            ssn (str): Social Security Number
            date_from (str, optional): Start date in YYYY-MM-DD format
            date_to (str, optional): End date in YYYY-MM-DD format
            chapters (list, optional): List of bankruptcy chapters to search (e.g., ["7", "13"])
            
        Returns:
            dict: Search results if successful, None otherwise
        """
        search_data = {
            "ssn": ssn,
            "jurisdictionType": "bk"
        }
        
        if any([date_from, date_to, chapters]):
            search_data["courtCase"] = {}
            
            if date_from:
                search_data["courtCase"]["dateFiledFrom"] = date_from
            if date_to:
                search_data["courtCase"]["dateFiledTo"] = date_to
            if chapters:
                search_data["courtCase"]["federalBankruptcyChapter"] = chapters
        
        return self.make_api_request("/parties/find", search_data)

# Example usage:
def main():
    # Initialize client
    client = PacerApiClient(environment="prod")  # Use "prod" for production
    
    # Authenticate
    authenticated = client.authenticate(
        username="KingC123",
        password=""
    )
    
    if authenticated:
        # Example bankruptcy search
        results = client.search_bankruptcy_by_ssn(
            ssn="172382589"
        )
        
        if results:
            print("Search Results:")
            print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()