from typing import Dict, Any

from ...base.workflow import BasePayloadBuilder


class FultonFCLPayloadBuilder(BasePayloadBuilder):
    """Payload builder for Fulton FCL workflow"""

    def build_package(self, workflow_data: Dict[str, Any], pdf_documents: Dict[str, str]) -> Dict[str, Any]:
        """Build complete FCL package for API submission"""
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
        # Build grantors
        grantors = []

        # Add first grantor
        grantor_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }

        if workflow_data["grantor_1_middle_name"]:
            grantor_1["middleName"] = workflow_data["grantor_1_middle_name"]

        grantors.append(grantor_1)

        # Add second grantor if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }

            if workflow_data["grantor_2_middle_name"]:
                grantor_2["middleName"] = workflow_data["grantor_2_middle_name"]

            if workflow_data["grantor_2_last_name"]:
                grantor_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                grantor_2["lastName"] = ""

            grantors.append(grantor_2)

        # Build grantees
        grantees = [{
            "nameUnparsed": workflow_data["deed_grantee_name"],
            "type": workflow_data["deed_grantee_type"]
        }]

        # Build legal descriptions
        legal_descriptions = [{
            "description": "",
            "parcelId": workflow_data["parcel_id"]
        }]

        # Build helper documents
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
        # Build grantors (individuals)
        grantors = []

        # Add first grantor
        grantor_1 = {
            "firstName": workflow_data["grantor_1_first_name"],
            "lastName": workflow_data["grantor_1_last_name"],
            "type": "Individual"
        }

        if workflow_data["grantor_1_middle_name"]:
            grantor_1["middleName"] = workflow_data["grantor_1_middle_name"]

        grantors.append(grantor_1)

        # Add second grantor if exists
        if workflow_data["has_second_owner"] and workflow_data["grantor_2_first_name"]:
            grantor_2 = {
                "firstName": workflow_data["grantor_2_first_name"],
                "type": "Individual"
            }

            if workflow_data["grantor_2_middle_name"]:
                grantor_2["middleName"] = workflow_data["grantor_2_middle_name"]

            if workflow_data["grantor_2_last_name"]:
                grantor_2["lastName"] = workflow_data["grantor_2_last_name"]
            else:
                grantor_2["lastName"] = ""

            grantors.append(grantor_2)

        # For satisfaction documents, grantee is from county config
        grantees = [{
            "nameUnparsed": workflow_data["sat_grantee_name"],
            "type": workflow_data["sat_grantee_type"]
        }]

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