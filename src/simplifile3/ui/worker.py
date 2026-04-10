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
            
            # Load Excel with workflow-specific columns
            required_columns = workflow.required_columns
            all_possible_columns = set(required_columns)
            if hasattr(workflow, 'field_mappings'):
                all_possible_columns.update(workflow.field_mappings.keys())
            
            columns_to_read = list(all_possible_columns)
            
            try:
                df = pd.read_excel(excel_path, dtype=str, usecols=columns_to_read)
            except ValueError:
                # If some columns don't exist, just read what's available
                temp_df = pd.read_excel(excel_path, nrows=0)
                available_columns = [col for col in columns_to_read if col in temp_df.columns]
                missing_required = [col for col in required_columns if col not in available_columns]
                if missing_required:
                    raise ValueError(f"Missing required columns: {missing_required}")
                df = pd.read_excel(excel_path, dtype=str, usecols=available_columns)
            
            logger.info(f"Loaded {len(df)} rows from Excel")
            
            # Validate Excel structure
            errors = workflow.validate_excel(df)
            if errors:
                for error in errors:
                    logger.error(error)
                self.finished.emit(False)
                return
            
            # Use pre-processed DataFrame if available (for multi-unit workflows)
            if hasattr(workflow, 'processed_df'):
                working_df = workflow.processed_df
                logger.info(f"Pre-processed into {len(working_df)} packages")
            else:
                working_df = df
            
            # Check row validity and collect invalid rows
            valid_rows = 0
            invalid_rows = []
            
            for idx, row in working_df.iterrows():
                row_dict = row.to_dict()
                excel_row_num = idx + 2  # +2 for 1-based and header
                
                if workflow.is_row_valid(row_dict):
                    valid_rows += 1
                else:
                    # Find which columns are invalid
                    invalid_columns = []
                    for col_idx, col in enumerate(workflow.required_columns):
                        value = row_dict.get(col)
                        if pd.isna(value) or str(value).strip() == "":
                            invalid_columns.append(col_idx)
                    
                    invalid_rows.append([excel_row_num, invalid_columns])
            
            logger.info(f"Validation complete: {valid_rows} valid rows, {len(invalid_rows)} invalid rows")
            
            # Report invalid rows if any
            if invalid_rows:
                logger.info(f"Invalid rows: {invalid_rows}")
            
            # Validate file paths
            for key, path in self.file_paths.items():
                if key != "excel" and path:  # Skip excel (already validated) and empty optional paths
                    import os
                    if not os.path.exists(path):
                        logger.error(f"{key} does not exist: {path}")
                        self.finished.emit(False)
                        return
            
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