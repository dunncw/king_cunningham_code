# simplifile3/ui/workers/processing_worker.py - Processing worker for simplifile3
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict


class ProcessingWorker(QThread):
    """Worker thread for batch processing"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(dict)  # Processing results
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, api_token: str, workflow_id: str, workflow_config: Dict[str, str], file_paths: Dict[str, str]):
        super().__init__()
        self.api_token = api_token
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.file_paths = file_paths
    
    def run(self):
        """Run batch processing"""
        try:
            from ...core.processor import Simplifile3Processor
            from ...utils.logging import Logger
            
            # Create logger that emits to UI
            logger = Logger(ui_callback=self.log_message.emit)
            
            # Create processor
            processor = Simplifile3Processor(
                api_token=self.api_token,
                workflow_id=self.workflow_id,
                logger=logger
            )
            
            # Process the batch
            results = processor.process_batch(
                workflow_config=self.workflow_config,
                file_paths=self.file_paths
            )
            
            # Emit results
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")