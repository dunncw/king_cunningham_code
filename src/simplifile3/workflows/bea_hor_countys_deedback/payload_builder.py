# simplifile3/workflows/bea_hor_countys_deedback/payload_builder.py - Payload builder for multi-county deedback
from typing import Dict, List, Any
from ...workflows.base import BasePayloadBuilder
from ...core.county_config import get_county_config


class BeaHorCountysDeedbackPayloadBuilder(BasePayloadBuilder):
    """Payload builder for BEA-HOR-COUNTYS-DEEDBACK workflow"""

    def __init__(self, logger=None):
        super().__init__(logger)

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete package for API submission to appropriate county"""
        
        # Determine target county from workflow data
        target_county = self._determine_target_county(workflow_data)
        county_config = get_county_config(target_county)
        
        # Build document based on target county
        if target_county == "SCCP49":  # Horry County
            document = self._build_horry_document(workflow_data, pdf_documents, county_config)
        elif target_county == "SCCY4G":  # Beaufort County
            document = self._build_beaufort_document(workflow_data, pdf_documents, county_config)
        else:
            raise ValueError(f"Unsupported target county: {target_county}")
        
        # Build complete package
        package = {
            "documents": [document],
            "recipient": county_config.COUNTY_ID,
            "submitterPackageID": workflow_data["package_id"],
            "name": workflow_data["package_name"],
            "operations": {
                "draftOnErrors": True,
                "submitImmediately": False,
                "verifyPageMargins": True
            }
        }
        
        return package

    def _determine_target_county(self, workflow_data: Dict[str, Any]) -> str:
        """Determine target county from workflow data"""
        project = workflow_data.get("project_number", 0)
        
        if project in [93, 94, 96]:
            return "SCCP49"  # Horry County
        elif project == 95:
            return "SCCY4G"  # Beaufort County
        else:
            raise ValueError(f"Cannot determine county for project: {project}")

    def _build_horry_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str], county_config) -> Dict[str, Any]:
        """Build document for Horry County submission"""
        
        # Build grantors (individual type only)
        grantors = []
        
        # Primary grantor
        grantors.append({
            "firstName": workflow_data["lead_1_first"],
            "lastName": workflow_data["lead_1_last"],
            "type": "Individual"
        })
        
        # Secondary grantor if exists
        if workflow_data.get("has_second_lead", False):
            grantors.append({
                "firstName": workflow_data["lead_2_first"],
                "lastName": workflow_data["lead_2_last"],
                "type": "Individual"
            })
        
        # Build grantees (organization type)
        grantees = [{
            "nameUnparsed": workflow_data["grantee_organization"],
            "type": "Organization"
        }]
        
        # Build legal descriptions with TMS as parcel ID
        legal_descriptions = [{
            "description": workflow_data["legal_description"],
            "parcelId": workflow_data["tms_number"]
        }]
        
        # Build reference information
        reference_information = [{
            "documentType": workflow_data["document_type"]
        }]
        
        # Build complete Horry document
        document = {
            "submitterDocumentID": workflow_data["document_id"],
            "name": workflow_data["package_name"],
            "kindOfInstrument": [workflow_data["document_type"]],
            "indexingData": {
                "executionDate": workflow_data["execution_date_formatted"],
                "consideration": workflow_data["consideration_amount"],
                "grantors": grantors,
                "grantees": grantees,
                "legalDescriptions": legal_descriptions,
            },
            "fileBytes": [pdf_documents["deed_pdf"]]
        }
        
        return document

    def _build_beaufort_document(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str], county_config) -> Dict[str, Any]:
        """Build document for Beaufort County submission (simplified requirements)"""
        
        # Build grantors (individual type only)
        grantors = []
        
        # Primary grantor
        grantors.append({
            "firstName": workflow_data["lead_1_first"],
            "lastName": workflow_data["lead_1_last"],
            "type": "Individual"
        })
        
        # Secondary grantor if exists
        if workflow_data.get("has_second_lead", False):
            grantors.append({
                "firstName": workflow_data["lead_2_first"],
                "lastName": workflow_data["lead_2_last"],
                "type": "Individual"
            })
        
        # Build grantees (organization type)
        grantees = [{
            "nameUnparsed": workflow_data["grantee_organization"],
            "type": "Organization"
        }]
        
        # Build complete Beaufort document (simplified - no execution date, legal descriptions, or reference info)
        document = {
            "submitterDocumentID": workflow_data["document_id"],
            "name": workflow_data["package_name"],
            "kindOfInstrument": [workflow_data["document_type"]],
            "indexingData": {
                "consideration": workflow_data["consideration_amount"],
                "grantors": grantors,
                "grantees": grantees
            },
            "fileBytes": [pdf_documents["deed_pdf"]]
        }
        
        return document

    def validate_package(self, package: Dict[str, Any]) -> List[str]:
        """Validate package against county requirements"""
        errors = super().validate_package(package)
        
        if "documents" in package and len(package["documents"]) > 0:
            document = package["documents"][0]
            doc_errors = self._validate_deedback_document(document, package.get("recipient", ""))
            errors.extend(doc_errors)
        
        return errors

    def _validate_deedback_document(self, document: Dict[str, Any], recipient: str) -> List[str]:
        """Validate deedback document"""
        errors = []
        indexing_data = document.get("indexingData", {})
        
        # Validate common requirements
        if "grantors" not in indexing_data or not indexing_data["grantors"]:
            errors.append("Document missing grantors")
        
        if "grantees" not in indexing_data or not indexing_data["grantees"]:
            errors.append("Document missing grantees")
        
        if "consideration" not in indexing_data:
            errors.append("Document missing consideration")
        elif not isinstance(indexing_data["consideration"], (int, float)):
            errors.append("Document consideration must be numeric")
        
        # County-specific validation
        if recipient == "SCCP49":  # Horry County
            if "executionDate" not in indexing_data or not indexing_data["executionDate"]:
                errors.append("Horry document missing execution date")
            
            if "legalDescriptions" not in indexing_data or not indexing_data["legalDescriptions"]:
                errors.append("Horry document missing legal descriptions")
        
        # Beaufort County requires only grantors, grantees, and consideration (already validated above)
        
        return errors

    def get_package_summary(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary information about a deedback package"""
        summary = {
            "package_id": package.get("submitterPackageID", "Unknown"),
            "package_name": package.get("name", "Unknown"),
            "recipient": package.get("recipient", "Unknown"),
            "document_count": len(package.get("documents", [])),
            "package_type": "Multi-County Deedback",
            "workflow": "BEA-HOR-COUNTYS-DEEDBACK"
        }
        
        if package.get("documents"):
            document = package["documents"][0]
            indexing_data = document.get("indexingData", {})
            
            summary.update({
                "document_id": document.get("submitterDocumentID", "Unknown"),
                "document_type": document.get("kindOfInstrument", ["Unknown"])[0],
                "grantor_count": len(indexing_data.get("grantors", [])),
                "grantee_count": len(indexing_data.get("grantees", [])),
                "has_execution_date": "executionDate" in indexing_data,
                "has_legal_descriptions": "legalDescriptions" in indexing_data
            })
        
        return summary