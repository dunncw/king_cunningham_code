# workflows/fulton_deedbacks_payload.py - API payload builder for Deedbacks workflow
from typing import Dict, List, Any
from .base import BasePayloadBuilder
from ..core.county_config import CountyConfig
from ..utils.logging import Logger


class FultonDeedbacksPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Fulton Deedbacks workflow"""

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """
        Build complete Deedbacks package for API submission
        
        Args:
            workflow_data: Processed data from FultonDeedbacksWorkflow
            pdf_documents: Base64 encoded PDFs from FultonDeedbacksPDFProcessor
                          {"deed_pdf": "base64...", "pt61_pdf": "base64...", "mortgage_pdf": "base64..."} (mortgage_pdf optional)
        
        Returns:
            Complete API payload dictionary
        """
        # Build the documents array
        documents = []
        
        # Add DEED document with PT-61 helper (always present)
        deed_document = self._build_deed_document(workflow_data, pdf_documents)
        documents.append(deed_document)
        
        # Add SATISFACTION document (only if present)
        if "mortgage_pdf" in pdf_documents:
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
                # If no last name, treat first name as full name or use Last 1
                grantor_2["lastName"] = workflow_data["grantor_1_last_name"]  # Default to same last name
            
            grantors.append(grantor_2)
        
        # Build grantees (organization buying - from DB To column)
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
        # For satisfaction documents in Deedbacks:
        # - Grantors: Organization (from DB To column) 
        # - Grantees: Same individuals as deed grantors
        
        # Build grantors (organization releasing the mortgage)
        grantors = [{
            "nameUnparsed": workflow_data["sat_grantee_name"],  # From DB To column
            "type": workflow_data["sat_grantee_type"]
        }]
        
        # Build grantees (individuals receiving the satisfaction)
        grantees = []
        
        # Add first grantee
        grantee_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }
        
        # Add middle name if provided
        if workflow_data["grantor_1_middle_name"]:
            grantee_1["middleName"] = workflow_data["grantor_1_middle_name"]
        
        grantees.append(grantee_1)
        
        # Add second grantee if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            grantee_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }
            
            # Add middle name if provided
            if workflow_data["grantor_2_middle_name"]:
                grantee_2["middleName"] = workflow_data["grantor_2_middle_name"]
            
            # Add last name if provided
            if workflow_data["grantor_2_last_name"]:
                grantee_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                # Default to same last name as first grantee
                grantee_2["lastName"] = workflow_data["grantor_1_last_name"]
            
            grantees.append(grantee_2)
        
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
        errors = super().validate_package(package)
        
        # Additional Deedbacks-specific validation
        if "documents" in package:
            for i, document in enumerate(package["documents"]):
                doc_errors = self._validate_deedbacks_document(document, i)
                errors.extend(doc_errors)
        
        return errors
    
    def _validate_deedbacks_document(self, document: Dict[str, Any], doc_index: int) -> List[str]:
        """Validate individual Deedbacks document"""
        errors = []
        doc_prefix = f"Document {doc_index + 1}"
        
        # Check document type
        kind = document.get("kindOfInstrument", [])
        if not kind:
            errors.append(f"{doc_prefix}: Missing kindOfInstrument")
            return errors
        
        doc_type = kind[0]
        
        if doc_type == self.county.DEED_DOCUMENT_TYPE:
            # Validate DEED document specific requirements
            indexing_data = document.get("indexingData", {})
            
            # Check for consideration
            if "consideration" not in indexing_data:
                errors.append(f"{doc_prefix}: DEED missing consideration")
            elif not isinstance(indexing_data["consideration"], (int, float)):
                errors.append(f"{doc_prefix}: DEED consideration must be numeric")
            elif indexing_data["consideration"] <= 0:
                errors.append(f"{doc_prefix}: DEED consideration must be greater than 0")
            
            # Check for exempt status
            if "exempt" not in indexing_data:
                errors.append(f"{doc_prefix}: DEED missing exempt status")
            
            # Check for legal descriptions
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append(f"{doc_prefix}: DEED missing legal descriptions")
            else:
                legal_desc = indexing_data["legalDescriptions"][0]
                if "parcelId" not in legal_desc or not legal_desc["parcelId"]:
                    errors.append(f"{doc_prefix}: DEED missing parcel ID")
            
            # Check for helper documents (PT-61)
            if "helperDocuments" not in document or not document["helperDocuments"]:
                errors.append(f"{doc_prefix}: DEED missing PT-61 helper document")
            else:
                helper = document["helperDocuments"][0]
                if helper.get("helperKindOfInstrument") != "PT-61":
                    errors.append(f"{doc_prefix}: DEED helper document must be PT-61")
        
        elif doc_type == self.county.MORTGAGE_DOCUMENT_TYPE:
            # Validate SATISFACTION document - minimal requirements
            indexing_data = document.get("indexingData", {})
            
            # Just ensure grantors and grantees exist
            if not indexing_data.get("grantors"):
                errors.append(f"{doc_prefix}: SATISFACTION missing grantors")
            
            if not indexing_data.get("grantees"):
                errors.append(f"{doc_prefix}: SATISFACTION missing grantees")
        
        return errors
    
    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a Deedbacks package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "package_type": "Unknown",
            "documents": []
        }
        
        deed_count = 0
        sat_count = 0
        
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
            
            # Count document types
            if doc_summary["type"] == self.county.DEED_DOCUMENT_TYPE:
                deed_count += 1
            elif doc_summary["type"] == self.county.MORTGAGE_DOCUMENT_TYPE:
                sat_count += 1
            
            summary["documents"].append(doc_summary)
        
        # Determine package type
        if deed_count == 1 and sat_count == 1:
            summary["package_type"] = "Deed + Satisfaction"
        elif deed_count == 1 and sat_count == 0:
            summary["package_type"] = "Deed Only"
        else:
            summary["package_type"] = f"Custom ({deed_count} deed, {sat_count} satisfaction)"
        
        return summary