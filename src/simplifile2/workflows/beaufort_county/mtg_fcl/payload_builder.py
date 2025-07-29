# workflows/beaufort_county/mtg_fcl/payload_builder.py - Beaufort County MTG-FCL payload builder
from typing import Dict, List, Any

from ...base.workflow import BasePayloadBuilder


class BeaufortMTGFCLPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Beaufort MTG-FCL workflow - simplified requirements per spec"""

    def __init__(self, county_config, workflow_config=None, logger=None):
        super().__init__(county_config, logger)
        # Handle backward compatibility - workflow_config is optional
        if workflow_config is None:
            # Use legacy document types from county config
            self.document_types = {
                "DEED_DOCUMENT_TYPE": county_config.DEED_DOCUMENT_TYPE,
                "MORTGAGE_DOCUMENT_TYPE": county_config.MORTGAGE_DOCUMENT_TYPE
            }
        else:
            # Use workflow-specific document types
            self.document_types = workflow_config.get("document_types", {
                "DEED_DOCUMENT_TYPE": county_config.DEED_DOCUMENT_TYPE,
                "MORTGAGE_DOCUMENT_TYPE": county_config.MORTGAGE_DOCUMENT_TYPE
            })

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete Beaufort MTG-FCL package for API submission - simplified"""
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
        """Build DEED document according to Beaufort County simplified requirements"""
        # Build grantors according to Beaufort spec
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

        # Build grantees - Entity from GRANTOR/GRANTEE column
        grantees = [{
            "nameUnparsed": workflow_data["grantor_grantee_entity"],
            "type": "Organization"
        }]

        # Build complete DEED document - SIMPLIFIED for Beaufort
        # No execution date, consideration, legal descriptions, or reference information required
        deed_document = {
            "submitterDocumentID": workflow_data["deed_document_id"],
            "name": workflow_data["deed_document_name"],
            "kindOfInstrument": [self.county.DEED_DOCUMENT_TYPE],
            "indexingData": {
                "grantors": grantors,
                "grantees": grantees
            },
            "fileBytes": [pdf_documents["deed_pdf"]]
        }

        return deed_document

    def _build_satisfaction_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build MORTGAGE SATISFACTION document according to Beaufort County simplified requirements"""
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

        # Build complete SATISFACTION document - SIMPLIFIED for Beaufort
        # No execution date, legal descriptions, or reference information required
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
        """Validate package against Beaufort County requirements - simplified validation"""
        errors = super().validate_package(package)

        # Additional Beaufort-specific validation (much simpler than Horry)
        if "documents" in package:
            for i, document in enumerate(package["documents"]):
                doc_errors = self._validate_beaufort_document(document, i)
                errors.extend(doc_errors)

        return errors

    def _validate_beaufort_document(self, document: Dict[str, Any], doc_index: int) -> List[str]:
        """Validate individual Beaufort document - simplified requirements"""
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
            # Validate DEED document - simplified for Beaufort
            
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

            # Note: Beaufort does NOT require consideration, execution date, 
            # legal descriptions, or reference information per spec

        elif doc_type == self.county.MORTGAGE_DOCUMENT_TYPE:
            # Validate SATISFACTION document - simplified for Beaufort
            
            # Check that KING CUNNINGHAM LLC TR is NOT a grantor for satisfaction
            grantors = indexing_data.get("grantors", [])
            for grantor in grantors:
                if (grantor.get("type") == "Organization" and 
                    "KING CUNNINGHAM LLC TR" in grantor.get("nameUnparsed", "")):
                    errors.append(f"{doc_prefix}: SATISFACTION should not have 'KING CUNNINGHAM LLC TR' as grantor")
                    break

            # Note: Beaufort does NOT require execution date, legal descriptions, 
            # or reference information per spec

        return errors

    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a Beaufort MTG-FCL package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "package_type": "Beaufort Hilton Head Timeshare Deed + Mortgage Satisfaction (Simplified)",
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
                doc_summary["simplified_requirements"] = True  # Beaufort simplification
                doc_summary["merged_document"] = True  # Always merged deed+affidavit
            elif doc_summary["type"] == self.county.MORTGAGE_DOCUMENT_TYPE:
                doc_summary["satisfaction_type"] = "Mortgage Satisfaction"
                doc_summary["simplified_requirements"] = True  # Beaufort simplification

            summary["documents"].append(doc_summary)

        return summary