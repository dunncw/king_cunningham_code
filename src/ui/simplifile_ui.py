# simplifile_ui.py - Updated to use centralized models
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QFileDialog, QMessageBox, 
    QGroupBox, QTableWidget, QTableWidgetItem, QDateEdit, 
    QTextEdit, QProgressBar, QDialog, QFrame, QTabWidget, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
from PyQt6.QtGui import QFont, QColor

from simplifile.batch_processor import (
    run_simplifile_batch_preview, 
    run_simplifile_batch_process
)
from simplifile.api import run_simplifile_connection_test
from simplifile.models import SimplifilePackage, SimplifileDocument, Party, LegalDescription, ReferenceInformation
from .batch_preview_dialog import BatchPreviewDialog

# County recipient mapping
RECIPIENT_COUNTIES = [
    {"id": "SCCE6P", "name": "Williamsburg County, SC"},
    {"id": "GAC3TH", "name": "Fulton County, GA"},
    {"id": "NCCHLB", "name": "Forsyth County, NC"},
    {"id": "SCCY4G", "name": "Beaufort County, SC"},
    {"id": "SCCP49", "name": "Horry County, SC"}
]

class SimplifileUI(QWidget):
    start_simplifile_upload = pyqtSignal(str, str, str, dict, list)
    start_simplifile_batch_upload = pyqtSignal(str, str, str, str, str, str)

    def __init__(self):
        super().__init__()
        self.documents = []
        self.config_file = os.path.join(os.path.expanduser("~"), ".simplifile_config.json")
        self.load_config()

        # Initialize thread and worker variables
        self.preview_thread = None
        self.preview_worker = None
        self.batch_thread = None
        self.batch_worker = None
        self.test_thread = None
        self.test_worker = None

        self.init_ui()

    def load_config(self):
        """Load config from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "api_token": "",
                    "submitter_id": "SCTP3G",
                    "recipient_id": ""
                }
        except:
            self.config = {
                "api_token": "",
                "submitter_id": "",
                "recipient_id": ""
            }

    def save_config(self):
        """Save config to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except:
            return False

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # API Configuration Section
        api_group = self.create_api_config_group()
        main_layout.addWidget(api_group)
        
        # Create tab widget for Single and Batch uploads
        self.tab_widget = QTabWidget()

        # Batch Upload Tab (primary functionality)
        self.batch_upload_tab = QWidget()
        self.setup_batch_upload_tab()
        self.tab_widget.addTab(self.batch_upload_tab, "Batch Upload")

        # Single Upload Tab (secondary functionality)
        self.single_upload_tab = QWidget()
        self.setup_single_upload_tab()
        self.tab_widget.addTab(self.single_upload_tab, "Single Upload")
        
        main_layout.addWidget(self.tab_widget)
        
        # Progress and output section (shared between tabs)
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        
        progress_layout.addWidget(QLabel("Status:"))
        progress_layout.addWidget(self.status_label, 1)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
        
        # Output area (shared between tabs)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        main_layout.addWidget(self.output_text)
        
        self.setLayout(main_layout)

    def create_api_config_group(self):
        """Create collapsible API configuration group box"""
        api_group = QGroupBox("API Configuration")
        api_layout = QFormLayout()
            
        # Create a horizontal layout for the API token field and show/hide button
        api_token_layout = QHBoxLayout()
        
        self.api_token = QLineEdit(self.config.get("api_token", ""))
        self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token.setPlaceholderText("Your Simplifile API token")
        api_token_layout.addWidget(self.api_token)
        
        # Add a toggle button for showing/hiding API token
        self.toggle_api_token_btn = QPushButton("Show")
        self.toggle_api_token_btn.setFixedWidth(60)
        self.toggle_api_token_btn.clicked.connect(self.toggle_api_token_visibility)
        api_token_layout.addWidget(self.toggle_api_token_btn)
        
        api_layout.addRow("API Token:", api_token_layout)
        
        self.submitter_id = QLineEdit(self.config.get("submitter_id", "SCTP3G"))
        self.submitter_id.setPlaceholderText("e.g., SCTP3G")
        api_layout.addRow("Submitter ID:", self.submitter_id)
        
        # County dropdown (recipient)
        self.recipient_combo = QComboBox()
        
        # Add an empty/initial option
        self.recipient_combo.addItem("-- Select County --", "")
        
        # Add all county options
        for county in RECIPIENT_COUNTIES:
            self.recipient_combo.addItem(county["name"], county["id"])
        
        # Set default from config if exists
        if self.config.get("recipient_id"):
            # If we have a config value, find and select that county
            county_found = False
            for i, county in enumerate(RECIPIENT_COUNTIES, 1):  # Start from 1 because of empty item
                if county["id"] == self.config["recipient_id"]:
                    self.recipient_combo.setCurrentIndex(i)
                    county_found = True
                    break
            
            # If county wasn't found, default to the empty selection
            if not county_found:
                self.recipient_combo.setCurrentIndex(0)
        else:
            # No config value, default to the empty selection
            self.recipient_combo.setCurrentIndex(0)
        
        api_layout.addRow("County:", self.recipient_combo)
        
        # Add buttons in a horizontal layout
        buttons_layout = QHBoxLayout()
        
        save_api_btn = QPushButton("Save API Configuration")
        save_api_btn.clicked.connect(self.save_api_settings)
        buttons_layout.addWidget(save_api_btn)
        
        # Add test connection button
        test_connection_btn = QPushButton("Test API Connection")
        test_connection_btn.clicked.connect(self.test_api_connection)
        test_connection_btn.setStyleSheet("background-color: #3498db; color: white;")
        buttons_layout.addWidget(test_connection_btn)
        
        api_layout.addRow("", buttons_layout)
        
        api_group.setLayout(api_layout)
        return api_group

    def test_api_connection(self):
        """Test connection to Simplifile API with current credentials"""
        # Validate inputs
        api_token = self.api_token.text()
        submitter_id = self.submitter_id.text()
        
        if not api_token or not submitter_id:
            QMessageBox.warning(self, "Missing Credentials", 
                            "Please enter your API token and submitter ID to test the connection.")
            return
        
        # Get the button that triggered this action
        test_button = self.sender()
        if test_button:
            test_button.setEnabled(False)
        
        # Run the connection test
        self.update_output("Testing API connection...")
        self.progress_bar.setValue(10)
        
        self.test_thread, self.test_worker = run_simplifile_connection_test(api_token, submitter_id)
        
        # Connect only to finished signal, not to error signal
        self.test_worker.status.connect(self.update_status)
        self.test_worker.finished.connect(self.connection_test_finished)
        
        # Ensure the button is re-enabled when the thread finishes
        self.test_thread.finished.connect(lambda: test_button.setEnabled(True) if test_button else None)
        
        # Start thread
        self.test_thread.start()

    def connection_test_finished(self, result):
        """Handle connection test completion"""
        # Extract test result from the dictionary
        if isinstance(result, dict) and "test_result" in result:
            success, message = result["test_result"]
            
            if success:
                self.update_output("API Connection Successful!")
                self.progress_bar.setValue(100)
                QMessageBox.information(self, "Connection Successful", 
                                    "Successfully connected to Simplifile API with your credentials.")
            else:
                # Check for specific error types
                if "UNAUTHORIZED" in message or "401" in message:
                    error_message = "Authentication failed: Invalid API token or submitter ID"
                    self.show_connection_error(error_message)
                else:
                    self.show_connection_error(message)
        else:
            # If we didn't get a valid result structure, use a generic message
            self.progress_bar.setValue(0)
            self.update_output("Connection test completed with unknown result")

    def show_connection_error(self, error_message):
        """Display connection error message"""
        self.update_output(f"Connection Error: {error_message}")
        QMessageBox.critical(self, "Connection Failed", error_message)
        self.progress_bar.setValue(0)

    def toggle_api_token_visibility(self):
        """Toggle the visibility of the API token"""
        if self.api_token.echoMode() == QLineEdit.EchoMode.Password:
            self.api_token.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_api_token_btn.setText("Hide")
        else:
            self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_api_token_btn.setText("Show")

    def setup_batch_upload_tab(self):
        """Setup the batch upload tab (primary functionality)"""
        batch_layout = QVBoxLayout()
        
        # File Selection Section
        files_layout = QFormLayout()
        
        # Excel File Selection
        excel_layout = QHBoxLayout()
        self.excel_file_path = QLineEdit()
        self.excel_file_path.setReadOnly(True)
        excel_browse_btn = QPushButton("Browse...")
        excel_browse_btn.clicked.connect(self.browse_excel_file)
        
        # Add template download button
        excel_template_btn = QPushButton("Download Template")
        excel_template_btn.clicked.connect(self.download_excel_template)
        excel_template_btn.setToolTip("Download an Excel template with the required format")
        
        excel_layout.addWidget(self.excel_file_path)
        excel_layout.addWidget(excel_browse_btn)
        excel_layout.addWidget(excel_template_btn)
        files_layout.addRow("Excel File:", excel_layout)
        
        # Deed Documents PDF Selection
        deeds_layout = QHBoxLayout()
        self.deeds_file_path = QLineEdit()
        self.deeds_file_path.setReadOnly(True)
        deeds_browse_btn = QPushButton("Browse...")
        deeds_browse_btn.clicked.connect(self.browse_deeds_file)
        deeds_layout.addWidget(self.deeds_file_path)
        deeds_layout.addWidget(deeds_browse_btn)
        files_layout.addRow("Deed Documents (PDF):", deeds_layout)
        
        # Affidavit Documents PDF Selection
        affidavits_layout = QHBoxLayout()
        self.affidavits_file_path = QLineEdit()
        self.affidavits_file_path.setReadOnly(True)
        affidavits_browse_btn = QPushButton("Browse...")
        affidavits_browse_btn.clicked.connect(self.browse_affidavits_file)
        affidavits_layout.addWidget(self.affidavits_file_path)
        affidavits_layout.addWidget(affidavits_browse_btn)
        files_layout.addRow("Affidavits (PDF):", affidavits_layout)
        
        # Mortgage Satisfaction PDF Selection
        mortgage_layout = QHBoxLayout()
        self.mortgage_file_path = QLineEdit()
        self.mortgage_file_path.setReadOnly(True)
        mortgage_browse_btn = QPushButton("Browse...")
        mortgage_browse_btn.clicked.connect(self.browse_mortgage_file)
        mortgage_layout.addWidget(self.mortgage_file_path)
        mortgage_layout.addWidget(mortgage_browse_btn)
        files_layout.addRow("Mortgage Satisfactions (PDF):", mortgage_layout)
        
        # Add files layout directly to batch layout
        batch_layout.addLayout(files_layout)
        
        # Add a separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        batch_layout.addWidget(separator)
        
        # Batch preview - No Group Box
        preview_layout = QHBoxLayout()
        
        # Label for preview section
        preview_label = QLabel("Batch Preview:")
        preview_layout.addWidget(preview_label)
        
        # Preview button
        self.preview_btn = QPushButton("Generate Preview")
        self.preview_btn.clicked.connect(self.generate_enhanced_batch_preview)
        preview_layout.addWidget(self.preview_btn)
        preview_layout.addStretch()  # Push button to the left
        
        batch_layout.addLayout(preview_layout)
        
        # Add another separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        batch_layout.addWidget(separator2)
        
        # Action buttons for batch upload
        actions_layout = QHBoxLayout()
        
        self.batch_upload_btn = QPushButton("Process Batch Upload")
        self.batch_upload_btn.clicked.connect(self.process_batch_upload)
        self.batch_upload_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        batch_clear_btn = QPushButton("Clear Batch")
        batch_clear_btn.clicked.connect(self.clear_batch)
        
        actions_layout.addWidget(batch_clear_btn)
        actions_layout.addWidget(self.batch_upload_btn)
        
        batch_layout.addLayout(actions_layout)
        
        # Add some stretch at the bottom to push everything up
        batch_layout.addStretch()
        
        self.batch_upload_tab.setLayout(batch_layout)

    def setup_single_upload_tab(self):
        """Setup the single upload tab (existing simplified functionality)"""
        single_layout = QVBoxLayout()
        
        # Package Configuration
        package_group = QGroupBox("Package Information")
        package_layout = QFormLayout()
        
        self.package_id = QLineEdit()
        self.package_id.setPlaceholderText(f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        package_layout.addRow("Package ID:", self.package_id)
        
        self.package_name = QLineEdit()
        self.package_name.setPlaceholderText(f"Package {datetime.now().strftime('%Y%m%d%H%M%S')}")
        package_layout.addRow("Package Name:", self.package_name)
        
        package_group.setLayout(package_layout)
        single_layout.addWidget(package_group)
        
        # Documents Section - simplified
        doc_group = QGroupBox("Documents")
        doc_layout = QVBoxLayout()
        
        self.doc_table = QTableWidget(0, 3)
        self.doc_table.setHorizontalHeaderLabels(["Document Name", "Type", "Actions"])
        self.doc_table.horizontalHeader().setStretchLastSection(True)
        self.doc_table.setMinimumHeight(200)
        
        doc_buttons_layout = QHBoxLayout()
        
        add_doc_btn = QPushButton("Add Document")
        add_doc_btn.clicked.connect(self.add_document)
        
        doc_buttons_layout.addWidget(add_doc_btn)
        
        doc_layout.addWidget(self.doc_table)
        doc_layout.addLayout(doc_buttons_layout)
        
        doc_group.setLayout(doc_layout)
        single_layout.addWidget(doc_group)
        
        # Action buttons for single upload
        actions_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton("Upload to Simplifile")
        self.upload_btn.clicked.connect(self.upload_to_simplifile)
        self.upload_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        
        actions_layout.addWidget(clear_btn)
        actions_layout.addWidget(self.upload_btn)
        
        single_layout.addLayout(actions_layout)
        
        self.single_upload_tab.setLayout(single_layout)

    def generate_enhanced_batch_preview(self):
        """Generate enhanced preview of batch processing"""
        # Check if all required files are selected
        if not self.excel_file_path.text():
            QMessageBox.warning(self, "Missing File", "Please select an Excel file.")
            return
        
        if not self.deeds_file_path.text() and not self.mortgage_file_path.text():
            QMessageBox.warning(self, "Missing Files", 
                            "Please select at least one PDF file (Deeds or Mortgage Satisfactions).")
            return
        
        # Run the enhanced preview generation
        self.update_output("Generating enhanced batch preview...")
        self.progress_bar.setValue(5)
        self.preview_btn.setEnabled(False)
        
        self.preview_thread, self.preview_worker = run_simplifile_batch_preview(
            self.excel_file_path.text(),
            self.deeds_file_path.text(),
            self.mortgage_file_path.text(),
            self.affidavits_file_path.text()
        )
        
        # Connect signals
        self.preview_worker.status.connect(self.update_status)
        self.preview_worker.progress.connect(self.update_progress)
        self.preview_worker.error.connect(self.show_error)
        self.preview_worker.preview_ready.connect(self.show_enhanced_preview_dialog)
        
        # Connect cleanup handlers
        self.preview_thread.finished.connect(lambda: self.preview_btn.setEnabled(True))
        
        # Start thread
        self.preview_thread.start()

    def show_enhanced_preview_dialog(self, preview_json):
        """Show the enhanced preview dialog with the generated data"""
        try:
            # Open the enhanced preview dialog with the JSON data
            dialog = BatchPreviewDialog(preview_json, self)
            dialog.exec()
            
        except Exception as e:
            self.show_error(f"Error displaying preview: {str(e)}")

    def browse_excel_file(self):
        """Browse for Excel file for batch processing"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.excel_file_path.setText(file_path)
            self.update_output(f"Selected Excel file: {os.path.basename(file_path)}")
    
    def browse_deeds_file(self):
        """Browse for Deed documents PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Deed Documents PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.deeds_file_path.setText(file_path)
            self.update_output(f"Selected Deed documents file: {os.path.basename(file_path)}")
    
    def browse_affidavits_file(self):
        """Browse for Affidavit documents PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Affidavit Documents PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.affidavits_file_path.setText(file_path)
            self.update_output(f"Selected Affidavit documents file: {os.path.basename(file_path)}")
    
    def browse_mortgage_file(self):
        """Browse for Mortgage Satisfaction PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Mortgage Satisfaction PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.mortgage_file_path.setText(file_path)
            self.update_output(f"Selected Mortgage Satisfaction file: {os.path.basename(file_path)}")

    def process_batch_upload(self):
        """Process and start the batch upload with actual API calls"""
        # Validate API configuration
        api_token = self.api_token.text()
        submitter_id = self.submitter_id.text()
        recipient_id = self.recipient_combo.currentData()
        
        if not api_token or not submitter_id or not recipient_id:
            QMessageBox.warning(self, "Missing API Configuration", 
                            "Please enter your API token, submitter ID, and select a county.")
            return
        
        # Validate file selection
        if not self.excel_file_path.text():
            QMessageBox.warning(self, "Missing Excel File", "Please select an Excel file.")
            return
            
        if not self.deeds_file_path.text() and not self.mortgage_file_path.text():
            QMessageBox.warning(self, "Missing PDF Files", 
                            "Please select at least one PDF file (Deeds or Mortgage Satisfactions).")
            return
        
        # Validate deed and affidavit files if deeds are provided
        if self.deeds_file_path.text() and not self.affidavits_file_path.text():
            reply = QMessageBox.question(
                self, 
                "Missing Affidavits",
                "You've selected a Deed file but no Affidavit file. The Deeds will be processed without affidavits. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Confirm batch upload
        recipient_name = self.recipient_combo.currentText()
        message = f"Process batch upload to {recipient_name}?\n\n"
        
        if self.deeds_file_path.text():
            message += f"- Deed Documents: {os.path.basename(self.deeds_file_path.text())}\n"
        if self.affidavits_file_path.text():
            message += f"- Affidavit Documents: {os.path.basename(self.affidavits_file_path.text())}\n"
        if self.mortgage_file_path.text():
            message += f"- Mortgage Satisfactions: {os.path.basename(self.mortgage_file_path.text())}\n"
        message += f"- Excel Data: {os.path.basename(self.excel_file_path.text())}\n\n"
        
        # Ask if this should be an actual upload or preview
        message += "Do you want to perform an actual API upload?\n"
        message += "- Click 'Yes' to upload to Simplifile\n"
        message += "- Click 'No' to run in preview mode (no API calls)\n"
        message += "- Click 'Cancel' to abort"
        
        reply = QMessageBox.question(self, "Confirm Batch Processing", message,
                                QMessageBox.StandardButton.Yes | 
                                QMessageBox.StandardButton.No | 
                                QMessageBox.StandardButton.Cancel)
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
            
        # Determine if this is preview mode or actual upload
        preview_mode = (reply == QMessageBox.StandardButton.No)
        
        # Run the batch process
        self.update_output(f"Starting batch processing in {'preview' if preview_mode else 'API upload'} mode...")
        self.progress_bar.setValue(5)
        self.batch_upload_btn.setEnabled(False)
        
        # Use the centralized batch processor to run the operation
        self.batch_thread, self.batch_worker = run_simplifile_batch_process(
            self.excel_file_path.text(),
            self.deeds_file_path.text(),
            self.mortgage_file_path.text(),
            api_token,
            submitter_id,
            recipient_id,
            preview_mode,
            self.affidavits_file_path.text()
        )
        
        # Connect signals
        self.batch_worker.status.connect(self.update_status)
        self.batch_worker.progress.connect(self.update_progress)
        self.batch_worker.error.connect(self.show_error)
        self.batch_worker.finished.connect(self.batch_process_finished)
        
        # Start thread
        self.batch_thread.start()

    def batch_process_finished(self, result_data):
        """Handle completion of batch processing with detailed error reporting"""
        self.batch_upload_btn.setEnabled(True)
        
        if result_data.get("resultCode") == "SUCCESS":
            self.update_output("Batch processing completed successfully.")
            packages = result_data.get("packages", [])
            self.update_output(f"Processed {len(packages)} packages.")
            
            # Show details of each package
            for package in packages:
                status = package.get("status", "unknown")
                msg = package.get("message", "")
                package_id = package.get("package_id", "")
                package_name = package.get("package_name", "")
                
                if status == "success":
                    self.update_output(f"✓ {package_id}: {package_name} - Uploaded successfully")
                elif status == "preview_success":
                    self.update_output(f"✓ {package_id}: {package_name} - Prepared successfully (preview mode)")
                else:
                    self.update_output(f"✗ {package_id}: {package_name} - Failed: {msg}")
                    
                    # Add detailed error information from API response if available
                    if "api_response" in package:
                        api_response = package.get("api_response", {})
                        errors = api_response.get("errors", [])
                        if errors:
                            self.update_output("  Detailed errors:")
                            for error in errors:
                                path = error.get("path", "Unknown field")
                                error_msg = error.get("message", "Unknown error")
                                self.update_output(f"  • {path}: {error_msg}")
                    
                    # Add HTTP error details if available
                    if "response_text" in package:
                        self.update_output(f"  Response: {package.get('response_text', '')}")
            
            # Show success message with appropriate text based on result
            if "summary" in result_data:
                summary = result_data["summary"]
                total = summary.get("total", len(packages))
                successful = summary.get("successful", 0)
                failed = summary.get("failed", 0)
                
                if failed > 0:
                    error_dialog = QMessageBox(self)
                    error_dialog.setWindowTitle("Processing Completed with Issues")
                    error_dialog.setIcon(QMessageBox.Icon.Warning)
                    
                    # Create detailed message with package-specific errors
                    detailed_msg = f"Batch processing completed with {successful} successful and {failed} failed packages.\n\nDetails:\n"
                    for package in packages:
                        if package.get("status") != "success" and package.get("status") != "preview_success":
                            detailed_msg += f"\n{package.get('package_id')}: {package.get('message')}"
                    
                    error_dialog.setText(detailed_msg)
                    error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
                    error_dialog.exec()
                else:
                    QMessageBox.information(self, "Processing Complete", 
                                        f"Batch processing completed successfully. {successful} packages processed.")
        elif result_data.get("resultCode") == "PARTIAL_SUCCESS":
            # Handle partial success
            self.update_output(f"Batch processing completed with partial success: {result_data.get('message', '')}")
            
            # Show detailed warning with all errors
            packages = result_data.get("packages", [])
            error_msg = f"Some packages failed to upload:\n\n"
            
            for package in packages:
                if package.get("status") != "success" and package.get("status") != "preview_success":
                    error_msg += f"{package.get('package_id')}: {package.get('message')}\n"
            
            QMessageBox.warning(self, "Processing Completed with Issues", error_msg)
        else:
            # Handle failure with more detailed information
            error_msg = result_data.get("message", "Unknown error")
            self.update_output(f"Batch processing failed: {error_msg}")
            
            # Create detailed error report
            detailed_error = "Batch processing failed\n\n"
            detailed_error += f"Error: {error_msg}\n\n"
            
            # Add details for each package if available
            packages = result_data.get("packages", [])
            if packages:
                detailed_error += "Package details:\n"
                for package in packages:
                    status = package.get("status", "unknown")
                    msg = package.get("message", "")
                    package_id = package.get("package_id", "")
                    detailed_error += f"\n• {package_id} ({status}): {msg}"
            
            # Show error message dialog with scroll area for large error reports
            from PyQt6.QtWidgets import QScrollArea, QDialog, QVBoxLayout, QTextEdit, QPushButton
            
            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("Processing Failed")
            error_dialog.resize(600, 400)
            
            layout = QVBoxLayout()
            
            error_text = QTextEdit()
            error_text.setReadOnly(True)
            error_text.setText(detailed_error)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(error_dialog.accept)
            
            layout.addWidget(error_text)
            layout.addWidget(close_btn)
            
            error_dialog.setLayout(layout)
            error_dialog.exec()

    def clear_batch(self):
        """Clear batch upload form"""
        reply = QMessageBox.question(self, "Confirm Clear", 
                                "Clear all batch upload information?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.excel_file_path.clear()
        self.deeds_file_path.clear()
        self.mortgage_file_path.clear()
        self.affidavits_file_path.clear()
        
        self.update_output("Batch upload information cleared")

    def download_excel_template(self):
        """Create and download a very simple Excel template file with only headers"""
        try:
            import pandas as pd
            
            # Ask user where to save the template
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Excel Template", "simplifile_template.xlsx", "Excel Files (*.xlsx)"
            )
            
            if not file_path:
                return
                
            # Add .xlsx extension if not present
            if not file_path.lower().endswith('.xlsx'):
                file_path += '.xlsx'
            
            # Create headers only
            headers = [
                'KC File No.', 'Account', 'Last Name #1', 'First Name #1',
                '&', 'Last Name #2', 'First Name #2', 'Deed Book',
                'Deed Page', 'Mortgage Book', 'Mortgage Page', 'Recorded Date',
                'Execution Date', 'Consideration', 'Suite', 'GRANTOR/GRANTEE',
                'LEGAL DESCRIPTION'
            ]
            
            # Create empty DataFrame with just the headers
            df = pd.DataFrame(columns=headers)
            
            # Save with basic formatting - no need for xlsxwriter
            df.to_excel(file_path, index=False)
            
            # Show success message
            QMessageBox.information(
                self, 
                "Template Created", 
                f"Excel template has been saved to:\n{file_path}"
            )
            
            # Open the file directory
            import os
            import subprocess
            
            # Get the directory containing the file
            dir_path = os.path.dirname(os.path.abspath(file_path))
            
            # Open the directory in file explorer
            if os.name == 'nt':  # Windows
                subprocess.Popen(f'explorer "{dir_path}"')
            elif os.name == 'posix':  # macOS or Linux
                try:
                    # Try macOS first
                    subprocess.Popen(['open', dir_path])
                except:
                    try:
                        # Try Linux
                        subprocess.Popen(['xdg-open', dir_path])
                    except:
                        pass
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error Creating Template", 
                f"Failed to create Excel template:\n{str(e)}"
            )

    def add_document(self):
        """Add a document to the single upload tab - simplified version"""
        # Open file dialog to select a document
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document File", "", "PDF Files (*.pdf);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Create a document name from the file name
        file_name = os.path.basename(file_path)
        name_without_ext = os.path.splitext(file_name)[0].upper()
        
        # Simplified document data
        doc_data = {
            "file_path": file_path,
            "name": name_without_ext,
            "type": "Deed - Timeshare",  # Default type
            "execution_date": datetime.now().strftime('%m/%d/%Y')
        }
        
        # Add document to list
        self.documents.append(doc_data)
        
        # Update document table
        self.update_document_table()
        self.update_output(f"Added document: {doc_data['name']}")

    def update_document_table(self):
        """Update the document table in single upload tab"""
        self.doc_table.setRowCount(0)
        
        for i, doc in enumerate(self.documents):
            self.doc_table.insertRow(i)
            
            # Document name
            self.doc_table.setItem(i, 0, QTableWidgetItem(doc.get("name", "")))
            
            # Document type
            self.doc_table.setItem(i, 1, QTableWidgetItem(doc.get("type", "")))
            
            # Actions - Add remove button
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_document(row))
            
            actions_layout.addWidget(remove_btn)
            actions_widget.setLayout(actions_layout)
            
            self.doc_table.setCellWidget(i, 2, actions_widget)

    def remove_document(self, row):
        """Remove a document from the list"""
        if 0 <= row < len(self.documents):
            doc_name = self.documents[row]["name"]
            self.documents.pop(row)
            self.update_document_table()
            self.update_output(f"Removed document: {doc_name}")

    def upload_to_simplifile(self):
        """Validate and upload package to Simplifile"""
        # Check API configuration
        api_token = self.api_token.text()
        submitter_id = self.submitter_id.text()
        recipient_id = self.recipient_combo.currentData()
        
        if not api_token or not submitter_id or not recipient_id:
            QMessageBox.warning(self, "Missing API Configuration", 
                               "Please enter your API token, submitter ID, and select a county.")
            return
        
        # Check documents
        if not self.documents:
            QMessageBox.warning(self, "No Documents", 
                               "Please add at least one document to the package.")
            return
        
        # Prepare package data - simplified for UI example
        package_data = {
            "package_id": self.package_id.text() or f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "package_name": self.package_name.text() or f"Package {datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Validate documents
        for doc in self.documents:
            if not os.path.exists(doc["file_path"]):
                QMessageBox.warning(self, "Invalid Document", 
                                  f"Document file not found: {doc['file_path']}")
                return
        
        # Confirm upload
        recipient_name = self.recipient_combo.currentText()
        reply = QMessageBox.question(self, "Confirm Upload", 
                                   f"Upload package '{package_data['package_name']}' with {len(self.documents)} document(s) to {recipient_name}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Emit signal to start upload
        self.start_simplifile_upload.emit(
            api_token,
            submitter_id,
            recipient_id,
            package_data,
            self.documents
        )
        
        self.upload_btn.setEnabled(False)
        self.update_output(f"Starting upload of package '{package_data['package_name']}' to {recipient_name}...")
        self.progress_bar.setValue(5)

    def upload_finished(self, response_data):
        """Handle completion of upload"""
        self.upload_btn.setEnabled(True)
        
        if "error" in response_data:
            self.update_output(f"Upload failed: {response_data.get('error', 'Unknown error')}")
            return
        
        if response_data.get("resultCode") == "SUCCESS":
            self.update_output("Upload completed successfully!")
            
            # Display package details
            if "packageStatus" in response_data:
                pkg_status = response_data["packageStatus"]
                self.update_output(f"Package ID: {pkg_status.get('id', 'Unknown')}")
                self.update_output(f"Status: {pkg_status.get('status', 'Unknown')}")
                self.update_output(f"View URL: {pkg_status.get('viewPackageUrl', 'N/A')}")
                
                # Show success message
                QMessageBox.information(self, "Upload Successful", 
                                     f"Package '{pkg_status.get('name', 'Unknown')}' was uploaded successfully.")
        else:
            self.update_output(f"Upload completed with errors. Result code: {response_data.get('resultCode', 'Unknown')}")

    def save_api_settings(self):
        """Save API settings to config"""
        self.config["api_token"] = self.api_token.text()
        self.config["submitter_id"] = self.submitter_id.text()
        self.config["recipient_id"] = self.recipient_combo.currentData()
        
        if self.save_config():
            self.update_output("API configuration saved successfully")
        else:
            self.update_output("Error saving API configuration")

    def update_progress(self, value):
        """Update the progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        self.update_output(status)
    
    def update_output(self, message):
        """Add a message to the output text area"""
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        self.output_text.append(f"{timestamp} {message}")
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )
    
    def show_error(self, error_message):
        """Display error message"""
        self.update_output(f"Error: {error_message}")
        QMessageBox.critical(self, "Process Error", error_message)
        self.upload_btn.setEnabled(True)
        self.batch_upload_btn.setEnabled(True)
    
    def clear_all(self):
        """Clear all input fields and documents"""
        reply = QMessageBox.question(self, "Confirm Clear", 
                                   "Clear all documents and package information?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Clear package info
        self.package_id.clear()
        self.package_name.clear()
        
        # Clear documents
        self.documents.clear()
        self.update_document_table()
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        
        self.update_output("All data cleared")