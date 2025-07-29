# workflows/beaufort_county/mtg_fcl/pdf_processor.py - Beaufort County MTG-FCL PDF processor
from typing import Dict, List, Any

from ...base.workflow import BasePDFProcessor


class BeaufortMTGFCLPDFProcessor(BasePDFProcessor):
    """PDF processor for Beaufort MTG-FCL workflow - same structure as Horry"""

    def __init__(self, logger=None):
        super().__init__(logger)

    def validate_stacks(self, deed_path: str, affidavit_path: str, mortgage_path: str) -> List[str]:
        """Validate all three Beaufort MTG-FCL PDF stacks"""
        from ....core.pdf_stack_processor import PDFStackProcessor

        stack_processor = PDFStackProcessor()

        stack_configs = [
            {
                "pdf_path": deed_path,
                "pages_per_document": 2,
                "stack_name": "Deed Stack"
            },
            {
                "pdf_path": affidavit_path,
                "pages_per_document": 2,
                "stack_name": "Affidavit Stack"
            },
            {
                "pdf_path": mortgage_path,
                "pages_per_document": 1,
                "stack_name": "Mortgage Satisfaction Stack"
            }
        ]

        return stack_processor.validate_stacks_alignment(stack_configs)

    def get_documents(self, document_index: int, deed_path: str, affidavit_path: str, mortgage_path: str) -> Dict[str, str]:
        """Get all documents for a specific Beaufort MTG-FCL package with deed+affidavit merging"""
        from ....core.pdf_stack_processor import PDFStackProcessor
        import io
        from PyPDF2 import PdfReader, PdfWriter
        import base64

        try:
            stack_processor = PDFStackProcessor()
            
            # Extract deed document (2 pages)
            deed_pdf_b64 = stack_processor.get_document_from_stack(
                deed_path, document_index, 2
            )
            
            # Extract affidavit document (2 pages) 
            affidavit_pdf_b64 = stack_processor.get_document_from_stack(
                affidavit_path, document_index, 2
            )
            
            # Extract mortgage satisfaction document (1 page)
            mortgage_pdf_b64 = stack_processor.get_document_from_stack(
                mortgage_path, document_index, 1
            )
            
            # Merge deed and affidavit into single 4-page document
            merged_deed_pdf_b64 = self._merge_deed_and_affidavit(deed_pdf_b64, affidavit_pdf_b64)

            return {
                "deed_pdf": merged_deed_pdf_b64,  # 4 pages (2 deed + 2 affidavit)
                "mortgage_pdf": mortgage_pdf_b64  # 1 page
            }

        except Exception as e:
            raise Exception(f"Error extracting Beaufort MTG-FCL documents for index {document_index}: {str(e)}")

    def _merge_deed_and_affidavit(self, deed_pdf_b64: str, affidavit_pdf_b64: str) -> str:
        """Merge deed and affidavit PDFs into single 4-page document"""
        try:
            import base64
            import io
            from PyPDF2 import PdfReader, PdfWriter
            
            # Decode base64 PDFs
            deed_bytes = base64.b64decode(deed_pdf_b64)
            affidavit_bytes = base64.b64decode(affidavit_pdf_b64)
            
            # Create PDF readers
            deed_reader = PdfReader(io.BytesIO(deed_bytes))
            affidavit_reader = PdfReader(io.BytesIO(affidavit_bytes))
            
            # Create new PDF writer for merged document
            merged_writer = PdfWriter()
            
            # Add all pages from deed document first
            for page in deed_reader.pages:
                merged_writer.add_page(page)
            
            # Add all pages from affidavit document
            for page in affidavit_reader.pages:
                merged_writer.add_page(page)
            
            # Convert merged PDF back to base64
            merged_buffer = io.BytesIO()
            merged_writer.write(merged_buffer)
            merged_bytes = merged_buffer.getvalue()
            merged_buffer.close()
            
            return base64.b64encode(merged_bytes).decode('utf-8')
            
        except Exception as e:
            raise Exception(f"Error merging deed and affidavit PDFs: {str(e)}")

    def get_stack_summary(self, deed_path: str, affidavit_path: str, mortgage_path: str) -> Dict[str, Any]:
        """Get summary information about all Beaufort MTG-FCL stacks"""
        from ....core.pdf_stack_processor import PDFStackProcessor

        try:
            stack_processor = PDFStackProcessor()

            deed_info = stack_processor.get_stack_info(deed_path, 2)
            affidavit_info = stack_processor.get_stack_info(affidavit_path, 2)
            mortgage_info = stack_processor.get_stack_info(mortgage_path, 1)

            # Determine how many complete packages we can create
            max_packages = min(
                deed_info["complete_documents"],
                affidavit_info["complete_documents"],
                mortgage_info["complete_documents"]
            )

            return {
                "deed_stack": deed_info,
                "affidavit_stack": affidavit_info,
                "mortgage_stack": mortgage_info,
                "max_packages": max_packages,
                "all_stacks_aligned": (
                    deed_info["complete_documents"] == affidavit_info["complete_documents"] ==
                    mortgage_info["complete_documents"]
                ),
                "merged_documents": True  # Beaufort always merges deed+affidavit
            }

        except Exception as e:
            raise Exception(f"Error getting Beaufort MTG-FCL stack summary: {str(e)}")