"""Simplified UI for Simplifile3."""

import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLineEdit, QLabel, QComboBox, QFileDialog, QMessageBox,
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtCore import QUrl

from .worker import Worker
from ..workflows import get_workflow, get_all_workflows


class SimplifileWindow(QWidget):
    """Main UI window for Simplifile3."""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.config_file = os.path.join(os.path.expanduser("~"), ".simplifile3_config.json")
        self.current_workflow = None
        self.file_paths = {}
        self.file_inputs = {}  # Store file input widgets
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # API Configuration
        api_group = QGroupBox("API Configuration")
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API Token:"))
        self.api_token_input = QLineEdit()
        self.api_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addWidget(self.api_token_input)
        
        self.save_config_btn = QPushButton("Save")
        self.save_config_btn.clicked.connect(self.save_config)
        api_layout.addWidget(self.save_config_btn)
        
        self.test_api_btn = QPushButton("Test")
        self.test_api_btn.clicked.connect(self.test_api)
        api_layout.addWidget(self.test_api_btn)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Workflow Selection
        workflow_group = QGroupBox("Workflow")
        workflow_layout = QHBoxLayout()
        workflow_layout.addWidget(QLabel("Select:"))
        
        self.workflow_combo = QComboBox()
        workflows = get_all_workflows()
        for workflow_id, workflow_info in workflows.items():
            # Use workflow ID as display name
            self.workflow_combo.addItem(workflow_id, workflow_id)
        self.workflow_combo.currentIndexChanged.connect(self.on_workflow_changed)
        workflow_layout.addWidget(self.workflow_combo)
        
        # Add docs button
        self.docs_btn = QPushButton("📖 Docs")
        self.docs_btn.clicked.connect(self.open_docs)
        self.docs_btn.setToolTip("Open workflow documentation (external link)")
        workflow_layout.addWidget(self.docs_btn)
        
        workflow_group.setLayout(workflow_layout)
        layout.addWidget(workflow_group)
        
        # File Inputs (dynamic)
        self.files_group = QGroupBox("Input Files")
        self.files_layout = QVBoxLayout()
        self.files_group.setLayout(self.files_layout)
        layout.addWidget(self.files_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Validate")
        self.validate_btn.clicked.connect(self.validate)
        button_layout.addWidget(self.validate_btn)
        
        self.process_btn = QPushButton("Process")
        self.process_btn.clicked.connect(self.process)
        self.process_btn.setEnabled(False)
        button_layout.addWidget(self.process_btn)
        
        layout.addLayout(button_layout)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Output Log
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)
        layout.addWidget(self.output_text)
        
        self.setLayout(layout)
        self.setWindowTitle("Simplifile3")
        self.resize(800, 600)
        
        # Initialize with first workflow
        if self.workflow_combo.count() > 0:
            self.on_workflow_changed()
    
    def open_docs(self):
        """Open documentation for current workflow."""
        workflow_id = self.workflow_combo.currentData()
        if not workflow_id:
            return
        
        try:
            workflow_class = get_workflow(workflow_id)
            if hasattr(workflow_class, 'docs_url') and workflow_class.docs_url:
                QDesktopServices.openUrl(QUrl(workflow_class.docs_url))
            else:
                QMessageBox.information(self, "No Documentation", "No documentation URL available for this workflow.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open documentation: {e}")
    
    def on_workflow_changed(self):
        """Handle workflow selection change."""
        workflow_id = self.workflow_combo.currentData()
        if not workflow_id:
            return
        
        try:
            # Get workflow class
            workflow_class = get_workflow(workflow_id)
            self.current_workflow = workflow_class()
            
            # Clear existing file inputs
            self.clear_file_inputs()
            
            self.file_paths = {}
            self.file_inputs = {}
            
            # Determine required files based on workflow
            self.add_file_inputs_for_workflow()
            
            # Reset buttons
            self.validate_btn.setText("Validate")
            self.process_btn.setEnabled(False)
            
            # Don't log workflow selection to reduce noise
            
        except Exception as e:
            self.log(f"Error loading workflow: {e}")
    
    def clear_file_inputs(self):
        """Properly clear all file input widgets."""
        while self.files_layout.count():
            child = self.files_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Handle nested layouts
                while child.layout().count():
                    nested_child = child.layout().takeAt(0)
                    if nested_child.widget():
                        nested_child.widget().deleteLater()
    
    def add_file_inputs_for_workflow(self):
        """Add file inputs based on current workflow requirements."""
        # Always need Excel
        self.add_file_input("excel", "Excel File", "Excel Files (*.xlsx *.xls)")
        
        # Determine other files based on workflow
        workflow_name = self.current_workflow.name
        
        if workflow_name == "BEA_HOR_DEEDBACK":
            # Variable-length PDF stack
            self.add_file_input("deed_stack", "Deed Stack PDF", "PDF Files (*.pdf)")
            
        elif workflow_name == "HORRY_MTG_FCL":
            # Fixed-length PDF stacks with optional affidavit
            self.add_file_input("deed_stack", "Deed Stack PDF (2 pages/doc)", "PDF Files (*.pdf)")
            self.add_file_input("affidavit_stack", "Affidavit Stack PDF", "PDF Files (*.pdf)", optional=True)
            self.add_file_input("mortgage_stack", "Mortgage Satisfaction Stack PDF (1 page/doc)", "PDF Files (*.pdf)")
            
        elif workflow_name == "BEAUFORT_MTG_FCL":
            # Same structure as Horry MTG but for Beaufort County (simplified requirements)
            self.add_file_input("deed_stack", "Deed Stack PDF (2 pages/doc)", "PDF Files (*.pdf)")
            self.add_file_input("affidavit_stack", "Affidavit Stack PDF", "PDF Files (*.pdf)", optional=True)
            self.add_file_input("mortgage_stack", "Mortgage Satisfaction Stack PDF (1 page/doc)", "PDF Files (*.pdf)")
            
        elif workflow_name == "HORRY_HOA_FCL":
            # Similar to MTG but with condo lien
            self.add_file_input("deed_stack", "Deed Stack PDF (2 pages/doc)", "PDF Files (*.pdf)")
            self.add_file_input("affidavit_stack", "Affidavit Stack PDF (Optional)", "PDF Files (*.pdf)", optional=True)
            self.add_file_input("condo_lien_stack", "Condo Lien Satisfaction Stack PDF (1 page/doc)", "PDF Files (*.pdf)")
            
        elif workflow_name == "BEAUFORT_MTG_FCL":
            # Same as Horry MTG
            self.add_file_input("deed_stack", "Deed Stack PDF (2 pages/doc)", "PDF Files (*.pdf)")
            self.add_file_input("affidavit_stack", "Affidavit Stack PDF (Optional)", "PDF Files (*.pdf)", optional=True)
            self.add_file_input("mortgage_stack", "Mortgage Satisfaction Stack PDF (1 page/doc)", "PDF Files (*.pdf)")
            
        elif workflow_name == "FULTON_FCL":
            # 3-page deeds with PT-61
            self.add_file_input("deed_stack", "Deed Stack PDF (3 pages/doc)", "PDF Files (*.pdf)")
            self.add_file_input("pt61_stack", "PT-61 Stack PDF (1 page/doc)", "PDF Files (*.pdf)")
            self.add_file_input("mortgage_stack", "Mortgage Satisfaction Stack PDF (1 page/doc)", "PDF Files (*.pdf)")
            
        elif workflow_name == "FULTON_DEEDBACKS":
            # Directory-based
            self.add_directory_input("documents_dir", "Documents Directory")
        
        # Add more workflow file requirements as needed
    
    def add_file_input(self, key: str, label: str, filter: str, optional: bool = False):
        """Add a file input row."""
        row = QHBoxLayout()
        
        label_widget = QLabel(f"{label}:")
        label_widget.setMinimumWidth(200)
        row.addWidget(label_widget)
        
        path_input = QLineEdit()
        path_input.setReadOnly(True)
        if optional:
            path_input.setPlaceholderText("(Optional)")
        row.addWidget(path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(
            lambda: self.browse_file(key, label, filter, path_input)
        )
        row.addWidget(browse_btn)
        
        self.files_layout.addLayout(row)
        self.file_inputs[key] = (path_input, optional)
    
    def add_directory_input(self, key: str, label: str):
        """Add a directory input row."""
        row = QHBoxLayout()
        
        label_widget = QLabel(f"{label}:")
        label_widget.setMinimumWidth(200)
        row.addWidget(label_widget)
        
        path_input = QLineEdit()
        path_input.setReadOnly(True)
        row.addWidget(path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(
            lambda: self.browse_directory(key, label, path_input)
        )
        row.addWidget(browse_btn)
        
        self.files_layout.addLayout(row)
        self.file_inputs[key] = (path_input, False)
    
    def browse_file(self, key: str, label: str, filter: str, path_input: QLineEdit):
        """Browse for file."""
        path, _ = QFileDialog.getOpenFileName(self, f"Select {label}", "", filter)
        if path:
            path_input.setText(path)
            self.file_paths[key] = path
    
    def browse_directory(self, key: str, label: str, path_input: QLineEdit):
        """Browse for directory."""
        path = QFileDialog.getExistingDirectory(self, f"Select {label}")
        if path:
            path_input.setText(path)
            self.file_paths[key] = path
    
    def validate(self):
        """Run validation."""
        if not self.check_inputs():
            return
        
        self.log("Starting validation...")
        self.progress_bar.setVisible(True)
        
        workflow_id = self.workflow_combo.currentData()
        self.worker = Worker("validate", self.api_token_input.text(), 
                            workflow_id, self.file_paths)
        self.worker.log_message.connect(self.log)
        self.worker.finished.connect(self.on_validation_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_validation_done(self, success: bool):
        """Handle validation completion."""
        self.progress_bar.setVisible(False)
        
        if success:
            self.validate_btn.setText("✓ Validated")
            self.process_btn.setEnabled(True)
            QMessageBox.information(self, "Success", "Validation passed!")
        else:
            self.validate_btn.setText("✗ Failed")
            QMessageBox.warning(self, "Validation Failed", "Check the log for errors")
    
    def process(self):
        """Run processing."""
        if not self.check_inputs():
            return
        
        reply = QMessageBox.question(
            self, "Confirm", "Start processing and upload to API?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.log("Starting processing...")
        self.progress_bar.setVisible(True)
        self.process_btn.setEnabled(False)
        
        workflow_id = self.workflow_combo.currentData()
        self.worker = Worker("process", self.api_token_input.text(),
                           workflow_id, self.file_paths)
        self.worker.log_message.connect(self.log)
        self.worker.finished.connect(self.on_process_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_process_done(self, result: dict):
        """Handle processing completion."""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        stats = result.get("stats", {})
        msg = (f"Processing complete!\n\n"
               f"Successful: {stats.get('successful_uploads', 0)}\n"
               f"Failed: {stats.get('failed_uploads', 0)}")
        
        QMessageBox.information(self, "Complete", msg)
        
        # Reset for next batch
        self.validate_btn.setText("Validate")
        self.process_btn.setEnabled(False)
    
    def test_api(self):
        """Test API connection."""
        from ..processor import Processor
        from ..workflows import get_workflow
        
        token = self.api_token_input.text()
        if not token:
            QMessageBox.warning(self, "Error", "Enter API token first")
            return
        
        try:
            # Use current workflow for testing
            workflow_id = self.workflow_combo.currentData()
            workflow_class = get_workflow(workflow_id)
            processor = Processor(token, workflow_class)
            
            if processor.test_connection():
                QMessageBox.information(self, "Success", "API connection successful!")
            else:
                QMessageBox.warning(self, "Failed", "API connection failed")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def check_inputs(self) -> bool:
        """Check all required inputs are provided."""
        if not self.api_token_input.text():
            QMessageBox.warning(self, "Error", "API token required")
            return False
        
        if not self.current_workflow:
            QMessageBox.warning(self, "Error", "No workflow selected")
            return False
        
        # Check required files
        for key, (input_widget, optional) in self.file_inputs.items():
            if not optional and not input_widget.text():
                QMessageBox.warning(self, "Error", f"Please select {key.replace('_', ' ').title()}")
                return False
        
        return True
    
    def save_config(self):
        """Save configuration."""
        config = {"api_token": self.api_token_input.text()}
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f)
            self.log("Config saved")
        except Exception as e:
            self.log(f"Failed to save config: {e}")
    
    def load_config(self):
        """Load configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    config = json.load(f)
                    self.api_token_input.setText(config.get("api_token", ""))
        except:
            pass
    
    def on_error(self, error: str):
        """Handle worker error."""
        self.progress_bar.setVisible(False)
        self.log(f"ERROR: {error}")
        QMessageBox.critical(self, "Error", error)
    
    def log(self, message: str):
        """Add message to log."""
        self.output_text.append(message)