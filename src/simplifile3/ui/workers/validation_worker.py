# simplifile3/ui/workers/validation_worker.py - Validation worker for simplifile3
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List, Any


class ValidationWorker(QThread):
    """Worker thread for validation-only processing"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(bool, list, dict)  # success, errors, summary
    
    def __init__(self, workflow_id: str, workflow_config: Dict[str, Any], file_paths: Dict[str, str]):
        super().__init__()
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.file_paths = file_paths
    
    def run(self):
        """Run validation process based on workflow type"""
        try:
            from ...core.validator import Simplifile3Validator
            from ...utils.logging import Logger
            
            # Create logger that emits to UI
            logger = Logger(ui_callback=self.log_message.emit)
            
            # Create validator
            validator = Simplifile3Validator(
                workflow_id=self.workflow_id,
                logger=logger
            )
            
            # Run validation
            is_valid, errors, summary = validator.validate_all(
                workflow_config=self.workflow_config,
                file_paths=self.file_paths
            )
            
            # Cleanup
            validator.cleanup()
            
            # Emit results
            self.finished.emit(is_valid, errors, summary)
            
        except Exception as e:
            # Emit error
            self.finished.emit(False, [f"Validation error: {str(e)}"], {})