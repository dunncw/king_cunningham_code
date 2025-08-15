# simplifile3/workflows/bea_hor_countys_deedback/pdf_processor.py - Variable PDF processor for deedback workflow
from typing import Dict, List, Any
from ...workflows.base import BasePDFProcessor
from ...core.variable_pdf_processor import VariablePDFProcessor


class BeaHorCountysDeedbackPDFProcessor(BasePDFProcessor):
    """PDF processor for BEA-HOR-COUNTYS-DEEDBACK workflow with variable-length documents"""

    def __init__(self, logger=None):
        super().__init__(logger)
        self.variable_processor = VariablePDFProcessor()
        self.processed_contracts = set()  # Track processed contract numbers to avoid duplicates

    def validate_pdfs(self, file_paths: Dict[str, str], excel_data: List[Dict[str, Any]]) -> List[str]:
        """Validate PDF files against Excel data"""
        errors = []
        
        deed_stack_path = file_paths.get("deed_stack", "")
        if not deed_stack_path:
            errors.append("Deed Stack PDF path is required")
            return errors
        
        # Extract page counts from Excel data
        page_counts = []
        multi_unit_groups = self._identify_multi_unit_groups(excel_data)
        
        for i, row in enumerate(excel_data):
            try:
                # Skip rows that should not be processed
                project = int(row.get("Project", 0))
                if project == 98:  # Skip project 98
                    continue
                
                # For multi-unit contracts, only process the first occurrence
                contract_key = f"{row.get('Project')}-{row.get('Number')}"
                if contract_key in multi_unit_groups:
                    if i == multi_unit_groups[contract_key][0]:  # First occurrence
                        page_counts.append(int(row.get("DB Pages", 0)))
                    # Skip subsequent occurrences
                else:
                    # Single unit contract
                    page_counts.append(int(row.get("DB Pages", 0)))
                    
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid page count at row {i + 2}: {str(e)}")
        
        # Validate page counts against PDF
        pdf_errors = self.variable_processor.validate_page_counts(deed_stack_path, page_counts)
        errors.extend(pdf_errors)
        
        return errors

    def get_documents_for_row(self, row_data: Dict[str, Any], file_paths: Dict[str, str]) -> Dict[str, str]:
        """Get PDF document for a specific row as base64 string"""
        deed_stack_path = file_paths.get("deed_stack", "")
        if not deed_stack_path:
            raise Exception("Deed Stack PDF path is required")
        
        page_count = row_data.get("document_pages", 0)
        if page_count <= 0:
            raise Exception("Invalid page count for document extraction")
        
        # Check if this is a duplicate contract (already processed)
        contract_key = f"{row_data.get('project_number')}-{row_data.get('contract_number')}"
        
        if contract_key in self.processed_contracts:
            # Skip PDF extraction but advance position
            self.variable_processor.skip_document(page_count)
            # Return empty - caller should handle this case
            return {}
        else:
            # Extract PDF and mark contract as processed
            pdf_b64 = self.variable_processor.get_next_document(deed_stack_path, page_count)
            self.processed_contracts.add(contract_key)
            
            return {
                "deed_pdf": pdf_b64
            }

    def get_pdf_summary(self, file_paths: Dict[str, str], excel_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary information about PDF files"""
        deed_stack_path = file_paths.get("deed_stack", "")
        if not deed_stack_path:
            return {"error": "Deed Stack PDF path is required"}
        
        try:
            # Calculate actual page counts needed (excluding skipped and duplicate contracts)
            page_counts = []
            multi_unit_groups = self._identify_multi_unit_groups(excel_data)
            processed_contracts = set()
            
            for i, row in enumerate(excel_data):
                try:
                    # Skip rows that should not be processed
                    project = int(row.get("Project", 0))
                    if project == 98:  # Skip project 98
                        continue
                    
                    # For multi-unit contracts, only count the first occurrence
                    contract_key = f"{row.get('Project')}-{row.get('Number')}"
                    if contract_key in processed_contracts:
                        continue  # Skip duplicate contract
                    
                    page_counts.append(int(row.get("DB Pages", 0)))
                    processed_contracts.add(contract_key)
                    
                except (ValueError, TypeError):
                    continue  # Skip invalid rows
            
            # Get stack info
            stack_info = self.variable_processor.get_stack_info(deed_stack_path, page_counts)
            
            # Add workflow-specific info
            stack_info.update({
                "workflow_type": "variable_pdf_deedback",
                "multi_unit_contracts": len(multi_unit_groups),
                "unique_contracts": len(processed_contracts),
                "total_excel_rows": len(excel_data),
                "skipped_project_98": sum(1 for row in excel_data if int(row.get("Project", 0)) == 98)
            })
            
            return stack_info
            
        except Exception as e:
            return {"error": f"Error analyzing PDF stack: {str(e)}"}

    def _identify_multi_unit_groups(self, excel_data: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        Identify multi-unit contracts (same Project + Number)
        
        Returns:
            Dictionary mapping "project-number" to list of row indices
        """
        contract_groups = {}
        
        for i, row in enumerate(excel_data):
            project = row.get("Project", "")
            number = row.get("Number", "")
            contract_key = f"{project}-{number}"
            
            if contract_key not in contract_groups:
                contract_groups[contract_key] = []
            contract_groups[contract_key].append(i)
        
        # Return only groups with multiple rows
        return {k: v for k, v in contract_groups.items() if len(v) > 1}

    def reset_for_new_batch(self):
        """Reset processor state for new batch processing"""
        self.variable_processor.reset_position()
        self.processed_contracts.clear()

    def cleanup(self):
        """Clean up resources"""
        self.variable_processor.clear_cache()
        self.processed_contracts.clear()