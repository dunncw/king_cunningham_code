from typing import Dict, List, Any

from ...base.workflow import BasePDFProcessor


class FultonFCLPDFProcessor(BasePDFProcessor):
    """PDF processor for Fulton FCL workflow"""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.pdf_cache = {}

    def validate_stacks(self, deed_path: str, pt61_path: str, mortgage_path: str) -> List[str]:
        """Validate all three FCL PDF stacks"""
        from ....core.pdf_stack_processor import PDFStackProcessor

        stack_processor = PDFStackProcessor()

        stack_configs = [
            {
                "pdf_path": deed_path,
                "pages_per_document": 3,
                "stack_name": "Deed Stack"
            },
            {
                "pdf_path": pt61_path,
                "pages_per_document": 1,
                "stack_name": "PT-61 Stack"
            },
            {
                "pdf_path": mortgage_path,
                "pages_per_document": 1,
                "stack_name": "Mortgage Satisfaction Stack"
            }
        ]

        return stack_processor.validate_stacks_alignment(stack_configs)

    def get_documents(self, document_index: int, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, str]:
        """Get all documents for a specific FCL package"""
        from ....core.pdf_stack_processor import PDFStackProcessor

        try:
            stack_processor = PDFStackProcessor()
            documents = {}

            # Extract deed document (3 pages)
            documents["deed_pdf"] = stack_processor.get_document_from_stack(
                deed_path, document_index, 3
            )

            # Extract PT-61 document (1 page)
            documents["pt61_pdf"] = stack_processor.get_document_from_stack(
                pt61_path, document_index, 1
            )

            # Extract mortgage satisfaction document (1 page)
            documents["mortgage_pdf"] = stack_processor.get_document_from_stack(
                mortgage_path, document_index, 1
            )

            return documents

        except Exception as e:
            raise Exception(f"Error extracting FCL documents for index {document_index}: {str(e)}")

    def get_stack_summary(self, deed_path: str, pt61_path: str, mortgage_path: str) -> Dict[str, Any]:
        """Get summary information about all FCL stacks"""
        from ....core.pdf_stack_processor import PDFStackProcessor

        try:
            stack_processor = PDFStackProcessor()

            deed_info = stack_processor.get_stack_info(deed_path, 3)
            pt61_info = stack_processor.get_stack_info(pt61_path, 1)
            mortgage_info = stack_processor.get_stack_info(mortgage_path, 1)

            # Determine how many complete packages we can create
            max_packages = min(
                deed_info["complete_documents"],
                pt61_info["complete_documents"],
                mortgage_info["complete_documents"]
            )

            return {
                "deed_stack": deed_info,
                "pt61_stack": pt61_info,
                "mortgage_stack": mortgage_info,
                "max_packages": max_packages,
                "all_stacks_aligned": (
                    deed_info["complete_documents"] == pt61_info["complete_documents"] ==
                    mortgage_info["complete_documents"]
                )
            }

        except Exception as e:
            raise Exception(f"Error getting FCL stack summary: {str(e)}")