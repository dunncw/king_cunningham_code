# simplifile2/document_builder.py - Build Simplifile API payloads
from typing import Dict, List, Any, Optional
from .county_config import CountyConfig


class DocumentBuilder:
    """Builds Simplifile API payloads from workflow data and PDF documents"""
    
    def __init__(self, county_config: CountyConfig):
        self.county = county_config
    
    def build_fcl_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """
        Build complete FCL package for API submission
        
        Args:
            workflow_data: Processed data from FultonFCLWorkflow
            pdf_documents: Base64 encoded PDFs from FultonFCLPDFProcessor
                          {"deed_pdf": "base64...", "pt61_pdf": "base64...", "mortgage_pdf": "base64..."}
        
        Returns:
            Complete API payload dictionary
        """
        # Build the documents array
        documents = []
        
        # Add DEED document with PT-61 helper
        deed_document = self._build_deed_document(workflow_data, pdf_documents)
        documents.append(deed_document)
        
        # Add SATISFACTION document
        satisfaction_document = self._build_satisfaction_document(workflow_data, pdf_documents)
        documents.append(satisfaction_document)
        
        # Build complete package
        package = {
            "documents": documents,
            "recipient": self.county.COUNTY_ID,
            "submitterPackageID": workflow_data["package_id"],
            "name": workflow_data["package_name"],
            "operations": {
                "draftOnErrors": True,
                "submitImmediately": False,
                "verifyPageMargins": True
            }
        }
        
        return package
    
    def _build_deed_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build DEED document with PT-61 helper document"""
        # Build grantors (individuals who are selling)
        grantors = []
        
        # Add first grantor
        grantor_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }
        
        # Add middle name if provided
        if workflow_data["grantor_1_middle_name"]:
            grantor_1["middleName"] = workflow_data["grantor_1_middle_name"]
        
        grantors.append(grantor_1)
        
        # Add second grantor if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }
            
            # Add middle name if provided
            if workflow_data["grantor_2_middle_name"]:
                grantor_2["middleName"] = workflow_data["grantor_2_middle_name"]
            
            # Add last name if provided (might be empty if full name is in first name field)
            if workflow_data["grantor_2_last_name"]:
                grantor_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                # If no last name, treat first name as full name
                grantor_2["lastName"] = ""
            
            grantors.append(grantor_2)
        
        # Build grantees (organization buying)
        grantees = [{
            "nameUnparsed": workflow_data["deed_grantee_name"],
            "type": workflow_data["deed_grantee_type"]
        }]
        
        # Build legal descriptions
        legal_descriptions = [{
            "description": "",
            "parcelId": workflow_data["parcel_id"]
        }]
        
        # Build helper documents (PT-61)
        helper_documents = [{
            "fileBytes": [pdf_documents["pt61_pdf"]],
            "helperKindOfInstrument": "PT-61",
            "isElectronicallyOriginated": False
        }]
        
        # Build complete DEED document
        deed_document = {
            "submitterDocumentID": workflow_data["deed_document_id"],
            "name": workflow_data["deed_document_name"],
            "kindOfInstrument": [self.county.DEED_DOCUMENT_TYPE],
            "indexingData": {
                "consideration": float(workflow_data["consideration_amount"]),
                "exempt": workflow_data["tax_exempt"],
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions
            },
            "fileBytes": [pdf_documents["deed_pdf"]],
            "helperDocuments": helper_documents
        }
        
        return deed_document
    
    def _build_satisfaction_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build SATISFACTION document"""
        # Build grantors and grantees (same individuals for satisfaction)
        parties = []
        
        # Add first party
        party_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }
        
        # Add middle name if provided
        if workflow_data["grantor_1_middle_name"]:
            party_1["middleName"] = workflow_data["grantor_1_middle_name"]
        
        parties.append(party_1)
        
        # Add second party if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            party_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }
            
            # Add middle name if provided
            if workflow_data["grantor_2_middle_name"]:
                party_2["middleName"] = workflow_data["grantor_2_middle_name"]
            
            # Add last name if provided
            if workflow_data["grantor_2_last_name"]:
                party_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                party_2["lastName"] = ""
            
            parties.append(party_2)
        
        # For satisfaction documents, grantors and grantees are the same people
        grantors = parties.copy()
        grantees = parties.copy()
        
        # Build complete SATISFACTION document
        satisfaction_document = {
            "submitterDocumentID": workflow_data["satisfaction_document_id"],
            "name": workflow_data["satisfaction_document_name"],
            "kindOfInstrument": [self.county.MORTGAGE_DOCUMENT_TYPE],
            "indexingData": {
                "grantors": grantors,
                "grantees": grantees
            },
            "fileBytes": [pdf_documents["mortgage_pdf"]]
        }
        
        return satisfaction_document
    
    def validate_package(self, package: Dict[str, Any]) -> List[str]:
        """
        Validate package against known API requirements
        
        Args:
            package: Complete API package dictionary
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate package structure
        if "documents" not in package:
            errors.append("Package missing 'documents' array")
            return errors
        
        if not isinstance(package["documents"], list) or len(package["documents"]) == 0:
            errors.append("Package must contain at least one document")
            return errors
        
        # Validate each document
        for i, document in enumerate(package["documents"]):
            doc_errors = self._validate_document(document, i)
            errors.extend(doc_errors)
        
        # Validate package-level fields
        required_package_fields = ["recipient", "submitterPackageID", "name", "operations"]
        for field in required_package_fields:
            if field not in package:
                errors.append(f"Package missing required field: {field}")
        
        return errors
    
    def _validate_document(self, document: Dict[str, Any], doc_index: int) -> List[str]:
        """Validate individual document"""
        errors = []
        doc_prefix = f"Document {doc_index + 1}"
        
        # Required document fields
        required_fields = ["submitterDocumentID", "name", "kindOfInstrument", "indexingData", "fileBytes"]
        for field in required_fields:
            if field not in document:
                errors.append(f"{doc_prefix}: Missing required field '{field}'")
        
        # Validate indexingData
        if "indexingData" in document:
            indexing_data = document["indexingData"]
            
            # Check for required parties
            if "grantors" not in indexing_data or not indexing_data["grantors"]:
                errors.append(f"{doc_prefix}: Missing grantors")
            
            if "grantees" not in indexing_data or not indexing_data["grantees"]:
                errors.append(f"{doc_prefix}: Missing grantees")
            
            # Validate party structure
            for party_type in ["grantors", "grantees"]:
                if party_type in indexing_data:
                    for j, party in enumerate(indexing_data[party_type]):
                        party_errors = self._validate_party(party, f"{doc_prefix} {party_type}[{j}]")
                        errors.extend(party_errors)
        
        # Validate fileBytes
        if "fileBytes" in document:
            if not isinstance(document["fileBytes"], list) or len(document["fileBytes"]) == 0:
                errors.append(f"{doc_prefix}: fileBytes must be a non-empty array")
        
        return errors
    
    def _validate_party(self, party: Dict[str, Any], party_prefix: str) -> List[str]:
        """Validate party (grantor/grantee) structure"""
        errors = []
        
        if "type" not in party:
            errors.append(f"{party_prefix}: Missing 'type' field")
            return errors
        
        party_type = party["type"]
        
        if party_type == "Individual":
            # Individual must have firstName and lastName (or at least one name field)
            if "firstName" not in party or not party["firstName"]:
                errors.append(f"{party_prefix}: Individual missing 'firstName'")
            
            # lastName is technically required but we handle cases where full name is in firstName
            if "lastName" not in party:
                errors.append(f"{party_prefix}: Individual missing 'lastName' field")
        
        elif party_type == "Organization":
            # Organization must have nameUnparsed
            if "nameUnparsed" not in party or not party["nameUnparsed"]:
                errors.append(f"{party_prefix}: Organization missing 'nameUnparsed'")
        
        else:
            errors.append(f"{party_prefix}: Invalid party type '{party_type}' (must be 'Individual' or 'Organization')")
        
        return errors
    
    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "documents": []
        }
        
        for document in package.get("documents", []):
            doc_summary = {
                "document_id": document.get("submitterDocumentID", "Unknown"),
                "name": document.get("name", "Unknown"),
                "type": document.get("kindOfInstrument", ["Unknown"])[0],
                "has_file": len(document.get("fileBytes", [])) > 0,
                "has_helper_documents": len(document.get("helperDocuments", [])) > 0
            }
            
            # Count parties
            indexing_data = document.get("indexingData", {})
            doc_summary["grantor_count"] = len(indexing_data.get("grantors", []))
            doc_summary["grantee_count"] = len(indexing_data.get("grantees", []))
            
            summary["documents"].append(doc_summary)
        
        return summary