# ui/workers/validation_worker.py - Validation thread worker
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List, Any


class ValidationWorker(QThread):
    """Worker thread for validation-only processing"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(bool, list, dict)  # success, errors, summary
    
    def __init__(self, county_id: str, workflow_id: str, file_paths: Dict[str, str]):
        super().__init__()
        self.county_id = county_id
        self.workflow_id = workflow_id
        self.file_paths = file_paths
    
    def run(self):
        """Run validation process"""
        try:
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
            
            # Run validation
            is_valid, errors, summary = validator.validate_all(
                excel_path=self.file_paths["excel_path"],
                deed_path=self.file_paths["deed_path"],
                pt61_path=self.file_paths["pt61_path"],
                mortgage_path=self.file_paths["mortgage_path"]
            )
            
            # Cleanup
            validator.cleanup()
            
            # Emit results
            self.finished.emit(is_valid, errors, summary)
            
        except Exception as e:
            # Emit error
            self.finished.emit(False, [f"Validation error: {str(e)}"], {})