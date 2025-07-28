import re
from typing import Dict, List, Any

from ...base.workflow import BasePayloadBuilder

class HorryMTGFCLPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Horry MTG-FCL workflow"""

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete Horry MTG-FCL package for API submission"""
        # Build the documents array
        documents = []

        # Add DEED document (merged deed+affidavit, 4 pages total)
        deed_document = self._build_deed_document(workflow_data, pdf_documents)
        documents.append(deed_document)

        # Add MORTGAGE SATISFACTION document
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
        """Build DEED document according to Horry County requirements"""
        # Build grantors according to Horry spec
        grantors = []

        # 1. KING CUNNINGHAM LLC TR (Organization) - REQUIRED for deed documents
        grantors.append({
            "nameUnparsed": "KING CUNNINGHAM LLC TR",
            "type": "Organization"
        })

        # 2. Entity from GRANTOR/GRANTEE column (Organization)
        grantors.append({
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        })

        # 3. Individual owners from Excel
        # First owner
        grantor_1 = {
            "firstName": workflow_data["owner_1_first_name"],
            "lastName": workflow_data["owner_1_last_name"],
            "type": "Individual"
        }
        
        # Handle organization prefix (ORG:)
        if workflow_data["owner_1_last_name"].startswith("ORG:"):
            # This is actually an organization
            grantors.append({
                "nameUnparsed": workflow_data["owner_1_first_name"],
                "type": "Organization"
            })
        else:
            grantors.append(grantor_1)

        # Second owner (if exists)
        if workflow_data["has_second_owner"] and workflow_data["owner_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["owner_2_first_name"],
                "lastName": workflow_data["owner_2_last_name"],
                "type": "Individual"
            }
            
            # Handle organization prefix for second owner
            if workflow_data["owner_2_last_name"].startswith("ORG:"):
                grantors.append({
                    "nameUnparsed": workflow_data["owner_2_first_name"],
                    "type": "Organization"
                })
            else:
                grantors.append(grantor_2)

        # Build grantees - Entity from GRANTOR/GRANTEE column (Horry County approach)
        grantees = [{
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": workflow_data["combined_legal_description"],
            "parcelId": ""  # Leave parcelId blank as per old code spec
        }]

        # Build reference information for deed
        reference_information = [{
            "documentType": self.county.DEED_DOCUMENT_TYPE,
            "book": workflow_data["deed_book"],
            "page": int(workflow_data["deed_page"]) if workflow_data["deed_page"].isdigit() else 0
        }]

        # Build complete DEED document
        deed_document = {
            "submitterDocumentID": workflow_data["deed_document_id"],
            "name": workflow_data["deed_document_name"],
            "kindOfInstrument": [self.county.DEED_DOCUMENT_TYPE],
            "indexingData": {
                "executionDate": workflow_data["execution_date"],
                "consideration": float(workflow_data["consideration_amount"]),
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions,
                "referenceInformation": reference_information
            },
            "fileBytes": [pdf_documents["deed_pdf"]]
        }

        return deed_document

    def _build_satisfaction_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build MORTGAGE SATISFACTION document according to Horry County requirements"""
        # Build grantors - Individual owners only (NOT KING CUNNINGHAM LLC TR)
        grantors = []

        # First owner
        grantor_1 = {
            "firstName": workflow_data["owner_1_first_name"],
            "lastName": workflow_data["owner_1_last_name"],
            "type": "Individual"
        }
        
        # Handle organization prefix (ORG:)
        if workflow_data["owner_1_last_name"].startswith("ORG:"):
            # This is actually an organization
            grantors.append({
                "nameUnparsed": workflow_data["owner_1_first_name"],
                "type": "Organization"
            })
        else:
            grantors.append(grantor_1)

        # Second owner (if exists)
        if workflow_data["has_second_owner"] and workflow_data["owner_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["owner_2_first_name"],
                "lastName": workflow_data["owner_2_last_name"],
                "type": "Individual"
            }
            
            # Handle organization prefix for second owner
            if workflow_data["owner_2_last_name"].startswith("ORG:"):
                grantors.append({
                    "nameUnparsed": workflow_data["owner_2_first_name"],
                    "type": "Organization"
                })
            else:
                grantors.append(grantor_2)

        # Build grantees - Entity from GRANTOR/GRANTEE column
        grantees = [{
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": workflow_data["combined_legal_description"],
            "parcelId": ""  # Leave parcelId blank as per old code spec
        }]

        # Build reference information for mortgage satisfaction
        reference_information = [{
            "documentType": self.county.MORTGAGE_DOCUMENT_TYPE,
            "book": workflow_data["mortgage_book"],
            "page": int(workflow_data["mortgage_page"]) if workflow_data["mortgage_page"].isdigit() else 0
        }]

        # Build complete SATISFACTION document
        satisfaction_document = {
            "submitterDocumentID": workflow_data["satisfaction_document_id"],
            "name": workflow_data["satisfaction_document_name"],
            "kindOfInstrument": [self.county.MORTGAGE_DOCUMENT_TYPE],
            "indexingData": {
                "executionDate": workflow_data["execution_date"],
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions,
                "referenceInformation": reference_information
            },
            "fileBytes": [pdf_documents["mortgage_pdf"]]
        }

        return satisfaction_document

    def validate_package(self, package: Dict[str, Any]) -> List[str]:
        """Validate package against Horry County requirements"""
        errors = super().validate_package(package)

        # Additional Horry-specific validation
        if "documents" in package:
            for i, document in enumerate(package["documents"]):
                doc_errors = self._validate_horry_document(document, i)
                errors.extend(doc_errors)

        return errors

    def _validate_horry_document(self, document: Dict[str, Any], doc_index: int) -> List[str]:
        """Validate individual Horry document"""
        errors = []
        doc_prefix = f"Document {doc_index + 1}"

        # Check document type
        kind = document.get("kindOfInstrument", [])
        if not kind:
            errors.append(f"{doc_prefix}: Missing kindOfInstrument")
            return errors

        doc_type = kind[0]
        indexing_data = document.get("indexingData", {})

        if doc_type == self.county.DEED_DOCUMENT_TYPE:
            # Validate DEED document specific requirements
            
            # Check for consideration - allow 0.00 for Horry workflow
            if "consideration" not in indexing_data:
                errors.append(f"{doc_prefix}: DEED missing consideration")
            elif not isinstance(indexing_data["consideration"], (int, float)):
                errors.append(f"{doc_prefix}: DEED consideration must be numeric")
            elif indexing_data["consideration"] < 0:  # Allow 0.00, just not negative
                errors.append(f"{doc_prefix}: DEED consideration cannot be negative")

            # Check for execution date
            if "executionDate" not in indexing_data or not indexing_data["executionDate"]:
                errors.append(f"{doc_prefix}: DEED missing execution date")

            # Check for legal descriptions
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append(f"{doc_prefix}: DEED missing legal descriptions")

            # Check for reference information
            if "referenceInformation" not in indexing_data or not indexing_data["referenceInformation"]:
                errors.append(f"{doc_prefix}: DEED missing reference information")

            # Check for KING CUNNINGHAM LLC TR in grantors
            grantors = indexing_data.get("grantors", [])
            has_king_cunningham = False
            for grantor in grantors:
                if (grantor.get("type") == "Organization" and 
                    "KING CUNNINGHAM LLC TR" in grantor.get("nameUnparsed", "")):
                    has_king_cunningham = True
                    break
            
            if not has_king_cunningham:
                errors.append(f"{doc_prefix}: DEED missing required grantor 'KING CUNNINGHAM LLC TR'")

        elif doc_type == self.county.MORTGAGE_DOCUMENT_TYPE:
            # Validate SATISFACTION document requirements
            
            # Check for execution date
            if "executionDate" not in indexing_data or not indexing_data["executionDate"]:
                errors.append(f"{doc_prefix}: SATISFACTION missing execution date")

            # Check for legal descriptions
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append(f"{doc_prefix}: SATISFACTION missing legal descriptions")

            # Check for reference information
            if "referenceInformation" not in indexing_data or not indexing_data["referenceInformation"]:
                errors.append(f"{doc_prefix}: SATISFACTION missing reference information")

            # Check that KING CUNNINGHAM LLC TR is NOT a grantor for satisfaction
            grantors = indexing_data.get("grantors", [])
            for grantor in grantors:
                if (grantor.get("type") == "Organization" and 
                    "KING CUNNINGHAM LLC TR" in grantor.get("nameUnparsed", "")):
                    errors.append(f"{doc_prefix}: SATISFACTION should not have 'KING CUNNINGHAM LLC TR' as grantor")
                    break

        return errors

    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a Horry MTG-FCL package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "package_type": "Horry Timeshare Deed + Mortgage Satisfaction",
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

            # Add specific info for each document type
            if doc_summary["type"] == self.county.DEED_DOCUMENT_TYPE:
                doc_summary["has_consideration"] = "consideration" in indexing_data
                doc_summary["merged_document"] = True  # Always merged deed+affidavit
            elif doc_summary["type"] == self.county.MORTGAGE_DOCUMENT_TYPE:
                doc_summary["satisfaction_type"] = "Mortgage Satisfaction"

            summary["documents"].append(doc_summary)

        return summary