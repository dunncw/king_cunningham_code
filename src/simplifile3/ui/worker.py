"""Worker thread for UI operations."""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, Any
import pandas as pd

from ..processor import Processor
from ..workflows import get_workflow
from ..logging import Logger


class Worker(QThread):
    """Single worker for all operations."""
    
    log_message = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, mode: str, api_token: str, workflow_id: str, 
                 file_paths: Dict[str, str]):
        super().__init__()
        self.mode = mode
        self.api_token = api_token
        self.workflow_id = workflow_id
        self.file_paths = file_paths
    
    def run(self):
        """Run the requested operation."""
        try:
            logger = Logger(ui_callback=self.log_message.emit)
            
            # Get workflow class
            workflow_class = get_workflow(self.workflow_id)
            
            if self.mode == "validate":
                self._run_validation(workflow_class, logger)
            elif self.mode == "process":
                self._run_processing(workflow_class, logger)
            else:
                raise ValueError(f"Unknown mode: {self.mode}")
                
        except Exception as e:
            self.error.emit(str(e))
    
    def _run_validation(self, workflow_class, logger: Logger):
        """Run validation only."""
        try:
            # Create workflow instance
            workflow = workflow_class(logger)
            
            # Load Excel
            excel_path = self.file_paths.get("excel", "")
            if not excel_path:
                raise ValueError("Excel file path not provided")
            
            df = pd.read_excel(excel_path, dtype=str)
            logger.info(f"Loaded {len(df)} rows from Excel")
            
            # Validate Excel structure
            errors = workflow.validate_excel(df)
            if errors:
                for error in errors:
                    logger.error(error)
                self.finished.emit(False)
                return
            
            # Validate file paths
            for key, path in self.file_paths.items():
                if path:  # Only check non-empty paths
                    import os
                    if not os.path.exists(path):
                        logger.error(f"{key} does not exist: {path}")
                        self.finished.emit(False)
                        return
            
            # Check row validity
            valid_rows = 0
            invalid_rows = 0
            
            for idx, row in df.iterrows():
                if workflow.is_row_valid(row.to_dict()):
                    valid_rows += 1
                else:
                    invalid_rows += 1
            
            logger.info(f"Validation complete: {valid_rows} valid rows, {invalid_rows} invalid rows")
            
            if valid_rows > 0:
                self.finished.emit(True)
            else:
                logger.error("No valid rows found")
                self.finished.emit(False)
            
        except Exception as e:
            logger.error(str(e))
            self.finished.emit(False)
    
    def _run_processing(self, workflow_class, logger: Logger):
        """Run full processing."""
        try:
            processor = Processor(self.api_token, workflow_class, logger)
            
            excel_path = self.file_paths.get("excel", "")
            if not excel_path:
                raise ValueError("Excel file path not provided")
            
            result = processor.process_batch(excel_path, self.file_paths)
            
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(str(e))
            self.error.emit(str(e))