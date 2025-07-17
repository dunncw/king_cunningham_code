# simplifile2/simplifile_ui.py - Clean, simplified UI for Simplifile 2 with validation-first flow
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QPushButton, QLineEdit, QLabel, QComboBox, QTextEdit,
    QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import os
import json


class ValidationWorker(QThread):
    """Worker thread for validation-only processing"""
    progress = pyqtSignal(str)  # Status message
    finished = pyqtSignal(bool, list, dict)  # success, errors, summary
    
    def __init__(self, config_data, input_files):
        super().__init__()
        self.config_data = config_data
        self.input_files = input_files
    
    def run(self):
        """Run validation only"""
        try:
            from .validator import SimplifileValidator
            
            # Create validator
            validator = SimplifileValidator(
                county_id=self.config_data["county_id"],
                workflow_type=self.config_data["workflow_type"],
                log_callback=self.progress.emit
            )
            
            # Run validation
            is_valid, errors, summary = validator.validate_all(
                excel_path=self.input_files["excel_path"],
                deed_path=self.input_files["deed_path"],
                pt61_path=self.input_files["pt61_path"],
                mortgage_path=self.input_files["mortgage_path"]
            )
            
            # Cleanup
            validator.cleanup()
            
            # Emit results
            self.finished.emit(is_valid, errors, summary)
            
        except Exception as e:
            self.finished.emit(False, [f"Validation error: {str(e)}"], {})


class SimplifileWorker(QThread):
    """Worker thread for batch processing"""
    progress = pyqtSignal(str)  # Status message
    finished = pyqtSignal(dict)  # Results
    error = pyqtSignal(str)  # Error message
    
    def __init__(self, config_data, input_files):
        super().__init__()
        self.config_data = config_data
        self.input_files = input_files
    
    def run(self):
        """Main processing logic using SimplifileProcessor"""
        try:
            from .main_processor import SimplifileProcessor
            
            # Create processor with logging callback
            processor = SimplifileProcessor(
                api_token=self.config_data["api_token"],
                county_id=self.config_data["county_id"],
                workflow_type=self.config_data["workflow_type"],
                log_callback=self.progress.emit
            )
            
            # Process the batch
            results = processor.process_batch(
                excel_path=self.input_files["excel_path"],
                deed_path=self.input_files["deed_path"],
                pt61_path=self.input_files["pt61_path"],
                mortgage_path=self.input_files["mortgage_path"]
            )
            
            # Emit results
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Processing error: {str(e)}")


class SimplifileUI(QWidget):
    """Clean, simplified Simplifile UI with validation-first flow"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.validation_worker = None
        self.validation_passed = False
        self.validation_summary = {}
        
        # Config file for saving API settings
        self.config_file = os.path.join(os.path.expanduser("~"), ".simplifile_conf.json")
        self.config = {}
        
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # API Configuration Section
        api_group = self.create_api_config_section()
        main_layout.addWidget(api_group)
        
        # County - Workflow Section (now dynamic)
        county_workflow_group = self.create_county_workflow_section()
        main_layout.addWidget(county_workflow_group)
        
        # Inputs Section
        inputs_group = self.create_inputs_section()
        main_layout.addWidget(inputs_group)
        
        # Validate/Process Button and Progress
        process_layout = QVBoxLayout()
        
        self.validate_button = QPushButton("Validate Files")
        self.validate_button.clicked.connect(self.validate_files)
        
        self.process_button = QPushButton("Process Batch")
        self.process_button.clicked.connect(self.process_batch)
        self.process_button.setEnabled(False)  # Disabled until validation passes
        
        # Simple progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        process_layout.addWidget(self.validate_button)
        process_layout.addWidget(self.process_button)
        process_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(process_layout)
        
        # Output/Logging Section
        output_group = QGroupBox("Processing Log")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        self.output_text.setPlaceholderText("Processing output will appear here...")
        
        output_layout.addWidget(self.output_text)
        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)
        
        self.setLayout(main_layout)
    
    def create_api_config_section(self):
        """Create API configuration section"""
        group = QGroupBox("API Configuration")
        layout = QVBoxLayout()
        
        # API Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("API Token:"))
        
        self.api_token = QLineEdit()
        self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token.setPlaceholderText("Enter your Simplifile API token")
        self.api_token.textChanged.connect(self.reset_validation_state)
        token_layout.addWidget(self.api_token)
        
        layout.addLayout(token_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_config_btn = QPushButton("Save API Config")
        save_config_btn.clicked.connect(self.save_api_config)
        
        test_connection_btn = QPushButton("Test API Connection")
        test_connection_btn.clicked.connect(self.test_api_connection)
        
        button_layout.addWidget(save_config_btn, 1)
        button_layout.addWidget(test_connection_btn, 1)
        
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group
    
    def create_county_workflow_section(self):
        """Create county and workflow selection section (now dynamic)"""
        group = QGroupBox("County - Workflow")
        layout = QVBoxLayout()
        
        # County selection (populate from county config)
        county_layout = QHBoxLayout()
        county_layout.addWidget(QLabel("County:"))
        
        self.county_combo = QComboBox()
        self.county_combo.currentTextChanged.connect(self.update_workflow_options)
        self.county_combo.currentTextChanged.connect(self.reset_validation_state)
        county_layout.addWidget(self.county_combo)
        
        layout.addLayout(county_layout)
        
        # Workflow selection (populate dynamically)
        workflow_layout = QHBoxLayout()
        workflow_layout.addWidget(QLabel("Workflow:"))
        
        self.workflow_combo = QComboBox()
        self.workflow_combo.currentTextChanged.connect(self.reset_validation_state)
        workflow_layout.addWidget(self.workflow_combo)
        
        layout.addLayout(workflow_layout)
        
        # Populate counties and workflows
        self.populate_counties()
        
        group.setLayout(layout)
        return group
    
    def populate_counties(self):
        """Populate county dropdown from county config"""
        try:
            from .county_config import get_available_counties
            
            counties = get_available_counties()
            
            for county_id, county_name in counties.items():
                self.county_combo.addItem(county_name, county_id)
            
            # Initialize workflows for first county
            if self.county_combo.count() > 0:
                self.update_workflow_options()
                
        except Exception as e:
            self.log_output(f"Error loading counties: {str(e)}")
    
    def update_workflow_options(self):
        """Update workflow dropdown based on selected county"""
        self.workflow_combo.clear()
        
        county_id = self.county_combo.currentData()
        if not county_id:
            return
        
        try:
            from .workflow_definition import get_available_workflows
            
            workflows = get_available_workflows(county_id)
            
            for workflow_id, workflow_name in workflows.items():
                self.workflow_combo.addItem(workflow_name, workflow_id)
                
        except Exception as e:
            self.log_output(f"Error loading workflows for {county_id}: {str(e)}")
    
    def create_inputs_section(self):
        """Create file inputs section"""
        group = QGroupBox("Input Files")
        layout = QVBoxLayout()
        
        # Excel file
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel File:"))
        
        self.excel_path = QLineEdit()
        self.excel_path.setPlaceholderText("Select Excel file with package data")
        self.excel_path.setReadOnly(True)
        self.excel_path.textChanged.connect(self.reset_validation_state)
        excel_layout.addWidget(self.excel_path)
        
        excel_browse_btn = QPushButton("Browse")
        excel_browse_btn.clicked.connect(lambda: self.browse_file(self.excel_path, "Excel Files (*.xlsx *.xls)"))
        excel_layout.addWidget(excel_browse_btn)
        
        layout.addLayout(excel_layout)
        
        # Deed Stack PDF
        deed_layout = QHBoxLayout()
        deed_layout.addWidget(QLabel("Deed Stack PDF:"))
        
        self.deed_path = QLineEdit()
        self.deed_path.setPlaceholderText("Select deed stack PDF (3 pages per document)")
        self.deed_path.setReadOnly(True)
        self.deed_path.textChanged.connect(self.reset_validation_state)
        deed_layout.addWidget(self.deed_path)
        
        deed_browse_btn = QPushButton("Browse")
        deed_browse_btn.clicked.connect(lambda: self.browse_file(self.deed_path, "PDF Files (*.pdf)"))
        deed_layout.addWidget(deed_browse_btn)
        
        layout.addLayout(deed_layout)
        
        # PT-61 Stack PDF
        pt61_layout = QHBoxLayout()
        pt61_layout.addWidget(QLabel("PT-61 Stack PDF:"))
        
        self.pt61_path = QLineEdit()
        self.pt61_path.setPlaceholderText("Select PT-61 stack PDF (1 page per document)")
        self.pt61_path.setReadOnly(True)
        self.pt61_path.textChanged.connect(self.reset_validation_state)
        pt61_layout.addWidget(self.pt61_path)
        
        pt61_browse_btn = QPushButton("Browse")
        pt61_browse_btn.clicked.connect(lambda: self.browse_file(self.pt61_path, "PDF Files (*.pdf)"))
        pt61_layout.addWidget(pt61_browse_btn)
        
        layout.addLayout(pt61_layout)
        
        # Mortgage Satisfaction Stack PDF
        mortgage_layout = QHBoxLayout()
        mortgage_layout.addWidget(QLabel("Mortgage Satisfaction Stack PDF:"))
        
        self.mortgage_path = QLineEdit()
        self.mortgage_path.setPlaceholderText("Select mortgage satisfaction stack PDF (1 page per document)")
        self.mortgage_path.setReadOnly(True)
        self.mortgage_path.textChanged.connect(self.reset_validation_state)
        mortgage_layout.addWidget(self.mortgage_path)
        
        mortgage_browse_btn = QPushButton("Browse")
        mortgage_browse_btn.clicked.connect(lambda: self.browse_file(self.mortgage_path, "PDF Files (*.pdf)"))
        mortgage_layout.addWidget(mortgage_browse_btn)
        
        layout.addLayout(mortgage_layout)
        
        group.setLayout(layout)
        return group
    
    def reset_validation_state(self):
        """Reset validation state when inputs change"""
        self.validation_passed = False
        self.validation_summary = {}
        
        # Only update UI components if they exist (prevents errors during initialization)
        if hasattr(self, 'process_button'):
            self.process_button.setEnabled(False)
        if hasattr(self, 'validate_button'):
            self.validate_button.setText("Validate Files")
            self.validate_button.setEnabled(True)
    
    def load_config(self):
        """Load config from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "api_token": ""
                }
        except Exception as e:
            self.log_output(f"Error loading config: {str(e)}")
            self.config = {
                "api_token": ""
            }
        
        # Apply loaded config to UI
        if self.config.get("api_token"):
            self.api_token.setText(self.config["api_token"])
    
    def save_api_config(self):
        """Save API configuration"""
        try:
            self.config["api_token"] = self.api_token.text().strip()
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.log_output("API configuration saved successfully.")
            QMessageBox.information(self, "Success", "API configuration saved.")
            return True
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            self.log_output(f"ERROR: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            return False
    
    def browse_file(self, line_edit, file_filter):
        """Open file browser and set path in line edit"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", file_filter
        )
        if file_path:
            line_edit.setText(file_path)
    
    def test_api_connection(self):
        """Test API connection"""
        api_token = self.api_token.text().strip()
        
        if not api_token:
            QMessageBox.warning(self, "Error", "Please enter an API token.")
            return
        
        county_id = self.county_combo.currentData()
        workflow_type = self.workflow_combo.currentData()
        
        if not county_id or not workflow_type:
            QMessageBox.warning(self, "Error", "Please select county and workflow.")
            return
        
        self.log_output("Testing API connection...")
        
        try:
            from .main_processor import SimplifileProcessor
            
            processor = SimplifileProcessor(
                api_token=api_token,
                county_id=county_id,
                workflow_type=workflow_type,
                log_callback=self.log_output
            )
            
            success, message = processor.test_api_connection()
            
            self.log_output(f"API Connection Result: {message}")
            
            if success:
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Connection Failed", message)
                
        except Exception as e:
            error_msg = f"Error testing connection: {str(e)}"
            self.log_output(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
    
    def validate_basic_inputs(self):
        """Basic input validation before running comprehensive validation"""
        errors = []
        
        if not self.api_token.text().strip():
            errors.append("API Token is required")
        
        if not self.county_combo.currentData():
            errors.append("County selection is required")
            
        if not self.workflow_combo.currentData():
            errors.append("Workflow selection is required")
        
        if not self.excel_path.text().strip():
            errors.append("Excel file is required")
        
        if not self.deed_path.text().strip():
            errors.append("Deed Stack PDF is required")
        
        if not self.pt61_path.text().strip():
            errors.append("PT-61 Stack PDF is required")
        
        if not self.mortgage_path.text().strip():
            errors.append("Mortgage Satisfaction Stack PDF is required")
        
        return errors
    
    def validate_files(self):
        """Run comprehensive validation on all files"""
        # Basic input validation first
        validation_errors = self.validate_basic_inputs()
        if validation_errors:
            error_msg = "Please fix the following errors:\n\n" + "\n".join(f"• {error}" for error in validation_errors)
            QMessageBox.warning(self, "Input Error", error_msg)
            return
        
        # Prepare configuration data
        config_data = {
            "api_token": self.api_token.text().strip(),
            "county_id": self.county_combo.currentData(),
            "workflow_type": self.workflow_combo.currentData()
        }
        
        # Prepare input files
        input_files = {
            "excel_path": self.excel_path.text().strip(),
            "deed_path": self.deed_path.text().strip(),
            "pt61_path": self.pt61_path.text().strip(),
            "mortgage_path": self.mortgage_path.text().strip()
        }
        
        # Clear output and start validation
        self.output_text.clear()
        self.log_output("=" * 60)
        self.log_output("SIMPLIFILE 2 - FILE VALIDATION")
        self.log_output("=" * 60)
        self.log_output(f"County: {self.county_combo.currentText()}")
        self.log_output(f"Workflow: {self.workflow_combo.currentText()}")
        self.log_output("-" * 60)
        
        # Start validation worker thread
        self.validation_worker = ValidationWorker(config_data, input_files)
        self.validation_worker.progress.connect(self.log_output)
        self.validation_worker.finished.connect(self.on_validation_finished)
        
        # Update UI state
        self.validate_button.setEnabled(False)
        self.validate_button.setText("Validating...")
        self.process_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.validation_worker.start()
    
    def on_validation_finished(self, is_valid, errors, summary):
        """Handle validation completion"""
        self.log_output("-" * 60)
        
        # Reset UI state
        self.progress_bar.setVisible(False)
        
        if is_valid:
            self.validation_passed = True
            self.validation_summary = summary
            
            self.log_output("VALIDATION PASSED - Ready to Process!")
            self.log_output("=" * 60)
            
            # Update buttons
            self.validate_button.setText("Validation Passed")
            self.validate_button.setEnabled(True)
            self.process_button.setEnabled(True)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Validation Successful", 
                f"All validations passed!\n\n"
                f"Ready to process {summary.get('valid_packages', 0)} packages.\n\n"
                f"Click 'Process Batch' to submit to Simplifile API."
            )
            
        else:
            self.validation_passed = False
            self.validation_summary = {}
            
            self.log_output("VALIDATION FAILED")
            self.log_output("=" * 60)
            
            # Log all errors
            for error in errors:
                self.log_output(f"   {error}")
            
            # Update buttons
            self.validate_button.setText("Validation Failed")
            self.validate_button.setEnabled(True)
            self.process_button.setEnabled(False)
            
            # Show error message
            error_msg = "Validation failed with the following errors:\n\n" + "\n".join(f"- {error}" for error in errors[:10])  # Limit to first 10 errors
            if len(errors) > 10:
                error_msg += f"\n\n... and {len(errors) - 10} more errors (see log for details)"
            
            error_msg += "\n\nPlease fix these issues and run validation again before processing."
            
            QMessageBox.critical(self, "Validation Failed", error_msg)
    
    def process_batch(self):
        """Start batch processing (only enabled after successful validation)"""
        if not self.validation_passed:
            QMessageBox.warning(self, "Validation Required", "Please run validation first and ensure it passes before processing.")
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
        
        # Prepare configuration data
        config_data = {
            "api_token": self.api_token.text().strip(),
            "county_id": self.county_combo.currentData(),
            "workflow_type": self.workflow_combo.currentData()
        }
        
        # Prepare input files
        input_files = {
            "excel_path": self.excel_path.text().strip(),
            "deed_path": self.deed_path.text().strip(),
            "pt61_path": self.pt61_path.text().strip(),
            "mortgage_path": self.mortgage_path.text().strip()
        }
        
        # Add processing header to log
        self.log_output("")
        self.log_output("=" * 60)
        self.log_output("SIMPLIFILE 2 - BATCH PROCESSING STARTED")
        self.log_output("=" * 60)
        
        # Start worker thread
        self.worker = SimplifileWorker(config_data, input_files)
        self.worker.progress.connect(self.log_output)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error.connect(self.on_processing_error)
        
        # Update UI state
        self.validate_button.setEnabled(False)
        self.process_button.setEnabled(False)
        self.process_button.setText("Processing...")
        self.progress_bar.setVisible(True)
        
        self.worker.start()
    
    def on_processing_finished(self, results):
        """Handle processing completion"""
        
        # Reset UI state
        self.progress_bar.setVisible(False)
        self.validate_button.setEnabled(True)
        self.process_button.setEnabled(True)
        self.process_button.setText("Process Batch")
        
        # Reset validation state (user should re-validate after processing)
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
    
    def on_processing_error(self, error_message):
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
    
    def log_output(self, message):
        """Add message to output log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.output_text.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)