# ui/workers/processing_worker.py - Processing thread worker
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict


class ProcessingWorker(QThread):
    """Worker thread for batch processing"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(dict)  # Processing results
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, api_token: str, county_id: str, workflow_id: str, file_paths: Dict[str, str]):
        super().__init__()
        self.api_token = api_token
        self.county_id = county_id
        self.workflow_id = workflow_id
        self.file_paths = file_paths
    
    def run(self):
        """Run batch processing"""
        try:
            from ...core.processor import SimplifileProcessor
            from ...utils.logging import Logger
            
            # Create logger that emits to UI
            logger = Logger(ui_callback=self.log_message.emit)
            
            # Create processor
            processor = SimplifileProcessor(
                api_token=self.api_token,
                county_id=self.county_id,
                workflow_type=self.workflow_id,
                logger=logger
            )
            
            # Process the batch
            results = processor.process_batch(
                excel_path=self.file_paths["excel_path"],
                deed_path=self.file_paths["deed_path"],
                pt61_path=self.file_paths["pt61_path"],
                mortgage_path=self.file_paths["mortgage_path"]
            )
            
            # Emit results
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")