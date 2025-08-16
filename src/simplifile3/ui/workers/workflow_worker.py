# simplifile3/ui/workers/workflow_worker.py - Unified worker for all non-UI logic
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any


class WorkflowWorker(QThread):
    """Single worker thread for all non-UI workflow operations"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(object)  # Results (validation: bool, errors, summary) or (processing: dict)
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, mode: str, api_token: str, workflow_id: str, workflow_config: Dict[str, Any], file_paths: Dict[str, str]):
        super().__init__()
        self.mode = mode  # "validate" or "process"
        self.api_token = api_token
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.file_paths = file_paths
    
    def run(self):
        """Run the requested operation"""
        try:
            if self.mode == "validate":
                self._run_validation()
            elif self.mode == "process":
                self._run_processing()
            else:
                self.error.emit(f"Unknown mode: {self.mode}")
        except Exception as e:
            self.error.emit(f"{self.mode.title()} error: {str(e)}")
    
    def _run_validation(self):
        """Run validation logic"""
        from ...core.validator import Simplifile3Validator
        from ...utils.logging import Logger
        
        logger = Logger(ui_callback=self.log_message.emit)
        validator = Simplifile3Validator(workflow_id=self.workflow_id, logger=logger)
        
        is_valid, errors, summary = validator.validate_all(
            workflow_config=self.workflow_config,
            file_paths=self.file_paths
        )
        
        validator.cleanup()
        self.finished.emit((is_valid, errors, summary))
    
    def _run_processing(self):
        """Run processing logic"""
        from ...core.processor import Simplifile3Processor
        from ...utils.logging import Logger
        
        logger = Logger(ui_callback=self.log_message.emit)
        processor = Simplifile3Processor(
            api_token=self.api_token,
            workflow_id=self.workflow_id,
            logger=logger
        )
        
        results = processor.process_batch(
            workflow_config=self.workflow_config,
            file_paths=self.file_paths
        )
        
        self.finished.emit(results)