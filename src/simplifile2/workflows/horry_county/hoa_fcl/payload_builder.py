# workflows/horry_county/hoa_fcl/payload_builder.py - Horry County HOA-FCL payload builder
from typing import Dict, List, Any

from ...base.workflow import BasePayloadBuilder


class HorryHOAFCLPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Horry HOA-FCL workflow"""

    def __init__(self, county_config, workflow_config: Dict[str, Any], logger=None):
        super().__init__(county_config, logger)
        self.workflow_config = workflow_config
        self.document_types = workflow_config.get("document_types", {})

    def get_deed_document_type(self) -> str:
        """Get deed document type for this workflow"""
        return self.document_types.get("DEED_DOCUMENT_TYPE", "Deed - Timeshare")

    def get_satisfaction_document_type(self) -> str:
        """Get satisfaction document type for this workflow"""
        return self.document_types.get("SATISFACTION_DOCUMENT_TYPE", "Condo Lien Satisfaction")

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete Horry HOA-FCL package for API submission"""
        # Build the documents array
        documents = []

        # Add DEED document (merged deed+affidavit, 4 pages total)
        deed_document = self._build_deed_document(workflow_data, pdf_documents)
        documents.append(deed_document)

        # Add CONDO LIEN SATISFACTION document
        satisfaction_document = self._build_condo_lien_satisfaction_document(workflow_data, pdf_documents)
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
        """Build DEED document according to Horry HOA-FCL requirements"""
        # Build grantors according to HOA-FCL spec
        grantors = []

        # 1. KING CUNNINGHAM LLC TR (Organization) - REQUIRED for deed documents
        grantors.append({
            "nameUnparsed": "KING CUNNINGHAM LLC TR",
            "type": "Organization"
        })

        # 2. Entity from GRANTOR column (Organization) - SEPARATE from grantee
        grantors.append({
            "nameUnparsed": workflow_data["grantor_entity"],
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

        # Build grantees - Entity from GRANTEE column (separate from grantor)
        grantees = [{
            "nameUnparsed": workflow_data["grantee_entity"],
            "type": "Organization"
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": workflow_data["combined_legal_description"],
            "parcelId": ""  # Leave parcelId blank as per spec
        }]

        # Build reference information for deed
        reference_information = [{
            "documentType": self.get_deed_document_type(),
            "book": workflow_data["deed_book"],
            "page": int(workflow_data["deed_page"]) if workflow_data["deed_page"].isdigit() else 0
        }]

        # Build complete DEED document
        deed_document = {
            "submitterDocumentID": workflow_data["deed_document_id"],
            "name": workflow_data["deed_document_name"],
            "kindOfInstrument": [self.get_deed_document_type()],
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

    def _build_condo_lien_satisfaction_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build CONDO LIEN SATISFACTION document according to Horry HOA-FCL requirements"""
        # Build grantors - INCLUDES KING CUNNINGHAM LLC TR for condo lien satisfaction (per spec)
        grantors = []

        # 1. KING CUNNINGHAM LLC TR (Organization) - INCLUDED for condo lien satisfaction
        grantors.append({
            "nameUnparsed": "KING CUNNINGHAM LLC TR",
            "type": "Organization"
        })

        # 2. Entity from GRANTOR column (Organization)
        grantors.append({
            "nameUnparsed": workflow_data["grantor_entity"],
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

        # Build grantees - Entity from GRANTEE column
        grantees = [{
            "nameUnparsed": workflow_data["grantee_entity"],
            "type": "Organization"
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": workflow_data["combined_legal_description"],
            "parcelId": ""  # Leave parcelId blank as per spec
        }]

        # Build reference information for condo lien satisfaction
        reference_information = [{
            "documentType": self.get_satisfaction_document_type(),
            "book": workflow_data["condo_lien_book"],
            "page": int(workflow_data["condo_lien_page"]) if workflow_data["condo_lien_page"].isdigit() else 0
        }]

        # Build complete CONDO LIEN SATISFACTION document
        satisfaction_document = {
            "submitterDocumentID": workflow_data["satisfaction_document_id"],
            "name": workflow_data["satisfaction_document_name"],
            "kindOfInstrument": [self.get_satisfaction_document_type()],
            "indexingData": {
                "executionDate": workflow_data["execution_date"],
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions,
                "referenceInformation": reference_information
            },
            "fileBytes": [pdf_documents["condo_lien_pdf"]]
        }

        return satisfaction_document

    def validate_package(self, package: Dict[str, Any]) -> List[str]:
        """Validate package against Horry HOA-FCL requirements"""
        errors = super().validate_package(package)

        # Additional HOA-FCL-specific validation
        if "documents" in package:
            for i, document in enumerate(package["documents"]):
                doc_errors = self._validate_hoa_fcl_document(document, i)
                errors.extend(doc_errors)

        return errors

    def _validate_hoa_fcl_document(self, document: Dict[str, Any], doc_index: int) -> List[str]:
        """Validate individual HOA-FCL document"""
        errors = []
        doc_prefix = f"Document {doc_index + 1}"

        # Check document type
        kind = document.get("kindOfInstrument", [])
        if not kind:
            errors.append(f"{doc_prefix}: Missing kindOfInstrument")
            return errors

        doc_type = kind[0]
        indexing_data = document.get("indexingData", {})

        if doc_type == self.get_deed_document_type():
            # Validate DEED document specific requirements
            
            # Check for consideration - STRICT validation for HOA-FCL (must be > 0)
            if "consideration" not in indexing_data:
                errors.append(f"{doc_prefix}: DEED missing consideration")
            elif not isinstance(indexing_data["consideration"], (int, float)):
                errors.append(f"{doc_prefix}: DEED consideration must be numeric")
            elif indexing_data["consideration"] <= 0:
                errors.append(f"{doc_prefix}: DEED consideration must be greater than 0 for HOA-FCL workflow")

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

        elif doc_type == self.get_satisfaction_document_type():
            # Validate CONDO LIEN SATISFACTION document requirements
            
            # Check for execution date
            if "executionDate" not in indexing_data or not indexing_data["executionDate"]:
                errors.append(f"{doc_prefix}: CONDO LIEN SATISFACTION missing execution date")

            # Check for legal descriptions
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append(f"{doc_prefix}: CONDO LIEN SATISFACTION missing legal descriptions")

            # Check for reference information
            if "referenceInformation" not in indexing_data or not indexing_data["referenceInformation"]:
                errors.append(f"{doc_prefix}: CONDO LIEN SATISFACTION missing reference information")

            # Check that KING CUNNINGHAM LLC TR IS a grantor for condo lien satisfaction (differs from MTG-FCL)
            grantors = indexing_data.get("grantors", [])
            has_king_cunningham = False
            for grantor in grantors:
                if (grantor.get("type") == "Organization" and 
                    "KING CUNNINGHAM LLC TR" in grantor.get("nameUnparsed", "")):
                    has_king_cunningham = True
                    break
            
            if not has_king_cunningham:
                errors.append(f"{doc_prefix}: CONDO LIEN SATISFACTION missing required grantor 'KING CUNNINGHAM LLC TR'")

        return errors

    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a Horry HOA-FCL package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "package_type": "Horry HOA Foreclosure (Deed + Condo Lien Satisfaction)",
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
            if doc_summary["type"] == self.get_deed_document_type():
                doc_summary["has_consideration"] = "consideration" in indexing_data
                doc_summary["merged_document"] = True  # Always merged deed+affidavit
            elif doc_summary["type"] == self.get_satisfaction_document_type():
                doc_summary["satisfaction_type"] = "Condo Lien Satisfaction"

            summary["documents"].append(doc_summary)

        return summary