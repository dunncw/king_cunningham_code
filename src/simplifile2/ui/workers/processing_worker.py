# ui/workers/processing_worker.py - Updated processing thread worker for Deedbacks support
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict


class ProcessingWorker(QThread):
    """Worker thread for batch processing with dynamic workflow support including Deedbacks"""
    
    # Signals
    log_message = pyqtSignal(str)  # Log message
    finished = pyqtSignal(dict)  # Processing results
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, api_token: str, county_id: str, workflow_id: str, workflow_config: Dict[str, str], file_paths: Dict[str, str]):
        super().__init__()
        self.api_token = api_token
        self.county_id = county_id
        self.workflow_id = workflow_id
        self.workflow_config = workflow_config
        self.file_paths = file_paths
    
    def run(self):
        """Run batch processing based on workflow type"""
        try:
            # Determine workflow type and use appropriate processor
            input_type = self.workflow_config.get('input_type', 'unknown')
            
            if input_type == 'pdf_stacks':
                # Use existing stack-based processing (FCL workflow)
                self._process_stack_workflow()
            elif input_type == 'directory':
                # Use new directory-based processing (Deedbacks workflow)
                self._process_directory_workflow()
            else:
                # Unsupported workflow type
                self.error.emit(f"Processing not supported for workflow input type: {input_type}")
                
        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")
    
    def _process_stack_workflow(self):
            """Process traditional stack-based workflows (like FCL and MTG-FCL)"""
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
            
            # Process the batch with expected file paths for stack workflows
            # Map file paths based on workflow type
            if self.workflow_id == "fcl":
                # Fulton FCL: deed_stack, pt61_stack, mortgage_stack
                results = processor.process_batch(
                    excel_path=self.file_paths.get("excel", ""),
                    deed_path=self.file_paths.get("deed_stack", ""),
                    stack2_path=self.file_paths.get("pt61_stack", ""),
                    mortgage_path=self.file_paths.get("mortgage_stack", "")
                )
            elif self.workflow_id == "mtg_fcl":
                # Horry MTG-FCL: deed_stack, affidavit_stack, mortgage_stack
                results = processor.process_batch(
                    excel_path=self.file_paths.get("excel", ""),
                    deed_path=self.file_paths.get("deed_stack", ""),
                    stack2_path=self.file_paths.get("affidavit_stack", ""),
                    mortgage_path=self.file_paths.get("mortgage_stack", "")
                )
            else:
                # Unknown stack workflow - use generic parameter names
                results = processor.process_batch(
                    excel_path=self.file_paths.get("excel", ""),
                    deed_path=self.file_paths.get("deed_stack", ""),
                    stack2_path=self.file_paths.get("stack2", ""),
                    mortgage_path=self.file_paths.get("mortgage_stack", "")
                )
            
            # Emit results
            self.finished.emit(results)
    
    def _process_directory_workflow(self):
        """Process directory-based workflows (like Deedbacks)"""
        from ...workflows.fulton_county.deedbacks.workflow import FultonDeedbacksProcessor
        from ...utils.logging import Logger
        
        # Create logger that emits to UI
        logger = Logger(ui_callback=self.log_message.emit)
        
        # Create Deedbacks processor
        processor = FultonDeedbacksProcessor(
            api_token=self.api_token,
            county_id=self.county_id,
            logger=logger
        )
        
        # Process the batch with directory-based file paths
        results = processor.process_batch(
            excel_path=self.file_paths.get("excel", ""),
            documents_directory=self.file_paths.get("documents_directory", "")
        )
        
        # Emit results
        self.finished.emit(results)