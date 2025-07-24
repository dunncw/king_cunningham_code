# ui/main_window.py - Updated main UI window with dynamic workflow support
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QProgressBar, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any

from .components.api_config import APIConfigWidget
from .components.county_workflow import CountyWorkflowWidget
from .components.file_inputs import FileInputsWidget
from .workers.validation_worker import ValidationWorker
from .workers.processing_worker import ProcessingWorker


class SimplifileMainWindow(QWidget):
    """Main Simplifile UI window with validation-first flow and dynamic workflow support"""
    
    def __init__(self):
        super().__init__()
        self.validation_worker = None
        self.processing_worker = None
        self.validation_passed = False
        self.validation_summary = {}
        self.current_workflow_config = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # API Configuration Section
        self.api_config = APIConfigWidget()
        self.api_config.test_requested.connect(self.test_api_connection)
        main_layout.addWidget(self.api_config)
        
        # County/Workflow Selection
        self.county_workflow = CountyWorkflowWidget()
        self.county_workflow.selection_changed.connect(self.on_workflow_selection_changed)
        main_layout.addWidget(self.county_workflow)
        
        # File Inputs (dynamic based on workflow)
        self.file_inputs = FileInputsWidget()
        self.file_inputs.files_changed.connect(self.reset_validation_state)
        main_layout.addWidget(self.file_inputs)
        
        # Action Buttons
        button_layout = QVBoxLayout()
        
        self.validate_button = QPushButton("Validate Files")
        self.validate_button.clicked.connect(self.validate_files)
        
        self.process_button = QPushButton("Process Batch")
        self.process_button.clicked.connect(self.process_batch)
        self.process_button.setEnabled(False)
        
        # Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        button_layout.addWidget(self.validate_button)
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(button_layout)
        
        # Output Log
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        self.output_text.setPlaceholderText("Processing output will appear here...")
        main_layout.addWidget(self.output_text)
        
        self.setLayout(main_layout)
    
    def on_workflow_selection_changed(self, county_id: str, workflow_id: str, workflow_config: Dict[str, Any]):
        """Handle workflow selection changes"""
        self.current_workflow_config = workflow_config
        
        # Update file inputs based on workflow
        self.file_inputs.update_for_workflow(workflow_config)
        
        # Reset validation state
        self.reset_validation_state()
        
        # Log the selection
        if county_id and workflow_id:
            county_name = self.county_workflow.get_county_name()
            workflow_name = self.county_workflow.get_workflow_name()
            self.log_output(f"Selected: {county_name} - {workflow_name}")
            
            if workflow_config:
                input_type = workflow_config.get('input_type', 'unknown')
                self.log_output(f"Input type: {input_type}")
    
    def reset_validation_state(self):
        """Reset validation state when inputs change"""
        self.validation_passed = False
        self.validation_summary = {}
        
        # Only update UI components if they exist
        if hasattr(self, 'process_button'):
            self.process_button.setEnabled(False)
        if hasattr(self, 'validate_button'):
            self.validate_button.setText("Validate Files")
            self.validate_button.setEnabled(True)
    
    def validate_basic_inputs(self) -> list[str]:
        """Basic input validation before running comprehensive validation"""
        errors = []
        
        if not self.api_config.is_configured():
            errors.append("API Token is required")
        
        if not self.county_workflow.is_selection_valid():
            errors.append("County and workflow selection required")
        
        file_errors = self.file_inputs.validate_files()
        errors.extend(file_errors)
        
        return errors
    
    def validate_files(self):
        """Run comprehensive validation on all files"""
        # Basic input validation first
        validation_errors = self.validate_basic_inputs()
        if validation_errors:
            error_msg = "Please fix the following errors:\n\n" + "\n".join(f"- {error}" for error in validation_errors)
            QMessageBox.warning(self, "Input Error", error_msg)
            return
        
        # Clear output and start validation
        self.output_text.clear()
        self.log_validation_header()
        
        # Start validation worker
        self.validation_worker = ValidationWorker(
            county_id=self.county_workflow.get_county_id(),
            workflow_id=self.county_workflow.get_workflow_id(),
            workflow_config=self.current_workflow_config,
            file_paths=self.file_inputs.get_file_paths()
        )
        
        self.validation_worker.log_message.connect(self.log_output)
        self.validation_worker.finished.connect(self.on_validation_finished)
        
        # Update UI state
        self.validate_button.setEnabled(False)
        self.validate_button.setText("Validating...")
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.validation_worker.start()
    
    def on_validation_finished(self, is_valid: bool, errors: list, summary: Dict[str, Any]):
        """Handle validation completion"""
        self.progress_bar.setVisible(False)
        self.log_output("-" * 60)
        
        if is_valid:
            self.validation_passed = True
            self.validation_summary = summary

            # Update buttons
            self.validate_button.setText("Validation Passed")
            self.validate_button.setEnabled(True)
            
            # Only enable process button for workflows that support processing
            workflow_config = self.current_workflow_config
            if workflow_config.get('supports_processing', True):  # Default to True for backward compatibility
                self.process_button.setEnabled(True)
            else:
                self.process_button.setEnabled(False)
                self.log_output("NOTE: This workflow only supports validation and file discovery.")
            
            # Show success message
            valid_packages = summary.get("valid_packages", 0)
            if workflow_config.get('supports_processing', True):
                message_text = (
                    f"All validations passed!\n\n"
                    f"Ready to process {valid_packages} packages.\n\n"
                    f"Click 'Process Batch' to submit to Simplifile API."
                )
            else:
                message_text = (
                    f"File discovery and validation completed!\n\n"
                    f"Found {valid_packages} valid packages.\n\n"
                    f"Check the log for detailed file matching results."
                )
            
            QMessageBox.information(self, "Validation Successful", message_text)
        else:
            self.validation_passed = False
            self.validation_summary = {}
            
            self.log_output("VALIDATION FAILED")
            self.log_output("=" * 60)
            
            # Log errors
            for error in errors:
                self.log_output(f"   {error}")
            
            # Update buttons
            self.validate_button.setText("Validation Failed")
            self.validate_button.setEnabled(True)
            self.process_button.setEnabled(False)
            
            # Show error message
            error_msg = "Validation failed with the following errors:\n\n" + "\n".join(f"- {error}" for error in errors[:10])
            if len(errors) > 10:
                error_msg += f"\n\n... and {len(errors) - 10} more errors (see log for details)"
            error_msg += "\n\nPlease fix these issues and run validation again before processing."
            
            QMessageBox.critical(self, "Validation Failed", error_msg)
    
    def process_batch(self):
        """Start batch processing"""
        if not self.validation_passed:
            QMessageBox.warning(self, "Validation Required", "Please run validation first and ensure it passes before processing.")
            return
        
        # Check if current workflow supports processing
        if not self.current_workflow_config.get('supports_processing', True):
            QMessageBox.information(self, "Processing Not Supported", "This workflow only supports file discovery and validation.")
            return
        
        # Confirm processing
        valid_packages = self.validation_summary.get("valid_packages", 0)
        reply = QMessageBox.question(
            self,
            "Confirm Processing",
            f"Are you sure you want to process {valid_packages} packages?\n\n"
            f"This will submit documents to the Simplifile API and cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Start processing
        self.log_output("")
        self.log_output("BATCH PROCESSING STARTED")
        
        # Start processing worker
        self.processing_worker = ProcessingWorker(
            api_token=self.api_config.get_api_token(),
            county_id=self.county_workflow.get_county_id(),
            workflow_id=self.county_workflow.get_workflow_id(),
            workflow_config=self.current_workflow_config,
            file_paths=self.file_inputs.get_file_paths()
        )
        
        self.processing_worker.log_message.connect(self.log_output)
        self.processing_worker.finished.connect(self.on_processing_finished)
        self.processing_worker.error.connect(self.on_processing_error)
        
        # Update UI state
        self.validate_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.process_button.setText("Processing...")
        self.progress_bar.setVisible(True)
        
        self.processing_worker.start()
    
    def on_processing_finished(self, results: Dict[str, Any]):
        """Handle processing completion"""
        
        # Reset UI state
        self.progress_bar.setVisible(False)
        self.validate_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.process_button.setText("Process Batch")
        
        # Reset validation state
        self.reset_validation_state()
        
        # Show completion message
        stats = results.get("stats", {})
        success_count = stats.get("successful_uploads", 0)
        failed_count = stats.get("failed_uploads", 0)
        
        if failed_count == 0:
            QMessageBox.information(
                self,
                "Processing Complete",
                f"Batch processing completed successfully!\n\n"
                f"Successfully processed: {success_count} packages"
            )
        else:
            QMessageBox.warning(
                self,
                "Processing Complete with Errors",
                f"Batch processing completed with some errors:\n\n"
                f"Successful: {success_count} packages\n"
                f"Failed: {failed_count} packages\n\n"
                f"Check the log for details on failed packages."
            )
    
    def on_processing_error(self, error_message: str):
        """Handle processing error"""
        self.log_output(f"ERROR: {error_message}")
        self.log_output("=" * 60)
        
        # Reset UI state
        self.progress_bar.setVisible(False)
        self.validate_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.process_button.setText("Process Batch")
        
        # Reset validation state
        self.reset_validation_state()
        
        # Show error message
        QMessageBox.critical(self, "Processing Error", error_message)
    
    def test_api_connection(self, api_token: str):
        """Test API connection"""
        if not self.county_workflow.is_selection_valid():
            QMessageBox.warning(self, "Error", "Please select county and workflow first.")
            return
        
        self.log_output("Testing API connection...")
        
        try:
            from ..core.processor import SimplifileProcessor
            from ..utils.logging import Logger
            
            logger = Logger(ui_callback=self.log_output)
            
            processor = SimplifileProcessor(
                api_token=api_token,
                county_id=self.county_workflow.get_county_id(),
                workflow_type=self.county_workflow.get_workflow_id(),
                logger=logger
            )
            
            success, message = processor.test_api_connection()
            
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Connection Failed", message)
                
        except Exception as e:
            error_msg = f"Error testing connection: {str(e)}"
            self.log_output(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def log_validation_header(self):
        """Log validation header"""
        self.log_output("FILE VALIDATION AND DISCOVERY")
        self.log_output(f"County: {self.county_workflow.get_county_name()}")
        self.log_output(f"Workflow: {self.county_workflow.get_workflow_name()}")
        
        workflow_config = self.current_workflow_config
        if workflow_config:
            input_type = workflow_config.get('input_type', 'unknown')
            self.log_output(f"Input Type: {input_type}")
        
        self.log_output("-" * 60)
    
    def log_output(self, message: str):
        """Add message to output log (message should already be timestamped)"""
        self.output_text.append(message)
        
        # Auto-scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)