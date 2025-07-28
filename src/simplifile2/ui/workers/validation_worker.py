# ui/workers/validation_worker.py - Updated validation thread worker for Horry MTG-FCL support
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List, Any


class ValidationWorker(QThread):
    """Worker thread for validation-only processing with dynamic workflow support"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(bool, list, dict)  # success, errors, summary
    
    def __init__(self, county_id: str, workflow_id: str, workflow_config: Dict[str, Any], file_paths: Dict[str, str]):
        super().__init__()
        self.county_id = county_id
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.file_paths = file_paths
    
    def run(self):
        """Run validation process based on workflow type"""
        try:
            # Determine workflow type and use appropriate validator
            input_type = self.workflow_config.get('input_type', 'unknown')
            
            if input_type == 'pdf_stacks':
                # Use stack-based validation (FCL and MTG-FCL workflows)
                self._validate_stack_workflow()
            elif input_type == 'directory':
                # Use directory-based validation (Deedbacks workflow)
                self._validate_directory_workflow()
            else:
                # Unsupported workflow type
                self.finished.emit(False, [f"Unsupported workflow input type: {input_type}"], {})
                
        except Exception as e:
            # Emit error
            self.finished.emit(False, [f"Validation error: {str(e)}"], {})
    
    def _validate_stack_workflow(self):
        """Validate traditional stack-based workflows (like FCL and MTG-FCL)"""
        from ...core.validator import SimplifileValidator
        from ...utils.logging import Logger
        
        # Create logger that emits to UI
        logger = Logger(ui_callback=self.log_message.emit)
        
        # Create validator
        validator = SimplifileValidator(
            county_id=self.county_id,
            workflow_type=self.workflow_id,
            logger=logger
        )
        
        # Run validation with expected file paths for stack workflows
        # Map file paths based on workflow type
        if self.workflow_id == "fcl":
            # Fulton FCL: deed_stack, pt61_stack, mortgage_stack
            is_valid, errors, summary = validator.validate_all(
                excel_path=self.file_paths.get("excel", ""),
                deed_path=self.file_paths.get("deed_stack", ""),
                stack2_path=self.file_paths.get("pt61_stack", ""),
                mortgage_path=self.file_paths.get("mortgage_stack", "")
            )
        elif self.workflow_id == "mtg_fcl":
            # Horry MTG-FCL: deed_stack, affidavit_stack, mortgage_stack
            is_valid, errors, summary = validator.validate_all(
                excel_path=self.file_paths.get("excel", ""),
                deed_path=self.file_paths.get("deed_stack", ""),
                stack2_path=self.file_paths.get("affidavit_stack", ""),
                mortgage_path=self.file_paths.get("mortgage_stack", "")
            )
        else:
            # Unknown stack workflow
            is_valid, errors, summary = False, [f"Unknown stack workflow: {self.workflow_id}"], {}
        
        # Cleanup
        validator.cleanup()
        
        # Emit results
        self.finished.emit(is_valid, errors, summary)
    
    def _validate_directory_workflow(self):
        """Validate directory-based workflows (like Deedbacks)"""
        from ...workflows.fulton_county.deedbacks.workflow import FultonDeedbacksValidator
        from ...utils.logging import Logger
        
        # Create logger that emits to UI
        logger = Logger(ui_callback=self.log_message.emit)
        
        # Create deedbacks validator
        validator = FultonDeedbacksValidator(
            county_id=self.county_id,
            workflow_type=self.workflow_id,
            logger=logger
        )
        
        # Run validation for directory-based workflow
        is_valid, errors, summary = validator.validate_all(
            excel_path=self.file_paths.get("excel", ""),
            documents_directory=self.file_paths.get("documents_directory", "")
        )
        
        # Cleanup
        validator.cleanup()
        
        # Emit results
        self.finished.emit(is_valid, errors, summary)