import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QFileDialog, QMessageBox, 
    QGroupBox, QTableWidget, QTableWidgetItem, QDateEdit, 
    QTextEdit, QProgressBar, QDialog, QFrame, QTabWidget,
    QSplitter
)
from PyQt6.QtCore import pyqtSignal, Qt, QDate
from PyQt6.QtGui import QFont, QColor
from simplifile.batch_processor import run_simplifile_batch_preview, run_simplifile_batch_process
from .batch_preview_dialog import BatchPreviewDialog
import json

# County recipient mapping
RECIPIENT_COUNTIES = [
    {"id": "SCCE6P", "name": "Williamsburg County, SC"},
    {"id": "GAC3TH", "name": "Fulton County, GA"},
    {"id": "NCCHLB", "name": "Forsyth County, NC"},
    {"id": "SCCY4G", "name": "Beaufort County, SC"},
    {"id": "SCCP49", "name": "Horry County, SC"}
]

# Document types
DOCUMENT_TYPES = ["Deed - Timeshare", "Mortgage Satisfaction"]

# Default parties that are always added
DEFAULT_GRANTORS = [
    {"nameUnparsed": "KING CUNNINGHAM LLC TR", "type": "ORGANIZATION"},
    {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "ORGANIZATION"}
]

DEFAULT_GRANTEES = [
    {"nameUnparsed": "OCEAN CLUB VACATIONS LLC", "type": "ORGANIZATION"}
]

class SimplifileUI(QWidget):
    start_simplifile_upload = pyqtSignal(str, str, str, dict, list)
    start_simplifile_batch_upload = pyqtSignal(str, str, str, str, str, str)
    
    def __init__(self):
        super().__init__()
        self.documents = []
        self.config_file = os.path.join(os.path.expanduser("~"), ".simplifile_config.json")
        self.load_config()
        self.init_ui()

    def update_batch_preview_functionality(self):
        """Update the batch preview functionality in SimplifileUI"""
        # Connect the preview button in SimplifileUI
        self.preview_btn.clicked.connect(self.generate_enhanced_batch_preview)
        
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
            self.mortgage_file_path.text()
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
            # Open the enhanced preview dialog
            from .batch_preview_dialog import BatchPreviewDialog
            dialog = BatchPreviewDialog(preview_json, self)
            dialog.exec()
            
        except Exception as e:
            self.show_error(f"Error displaying preview: {str(e)}")
    
    def load_config(self):
        """Load config from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "api_token": "",
                    "submitter_id": "SCTPG3",
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
        
        self.submitter_id = QLineEdit(self.config.get("submitter_id", "SCTPG3"))
        self.submitter_id.setPlaceholderText("e.g., SCTPG3")
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
        
        save_api_btn = QPushButton("Save API Configuration")
        save_api_btn.clicked.connect(self.save_api_settings)
        api_layout.addRow("", save_api_btn)
        
        api_group.setLayout(api_layout)
        return api_group

    def toggle_api_token_visibility(self):
        """Toggle the visibility of the API token"""
        if self.api_token.echoMode() == QLineEdit.EchoMode.Password:
            self.api_token.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_api_token_btn.setText("Hide")
        else:
            self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_api_token_btn.setText("Show")
    
    def setup_single_upload_tab(self):
        """Setup the single upload tab (existing functionality)"""
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
        
        # Documents Section
        doc_group = QGroupBox("Documents")
        doc_layout = QVBoxLayout()
        
        self.doc_table = QTableWidget(0, 4)
        self.doc_table.setHorizontalHeaderLabels(["Document Name", "Type", "Additional Persons", "Actions"])
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

    def setup_batch_upload_tab(self):
        """Setup the batch upload tab (primary functionality) with a simplified layout"""
        batch_layout = QVBoxLayout()
        
        # File Selection Section - No Group Box
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
        
        # Set up the enhanced preview functionality
        self.update_batch_preview_functionality()

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
    
    def browse_mortgage_file(self):
        """Browse for Mortgage Satisfaction PDF file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Mortgage Satisfaction PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.mortgage_file_path.setText(file_path)
            self.update_output(f"Selected Mortgage Satisfaction file: {os.path.basename(file_path)}")
    
    def generate_batch_preview(self):
        """Generate preview of batch processing"""
        # Check if all required files are selected
        if not self.excel_file_path.text():
            QMessageBox.warning(self, "Missing File", "Please select an Excel file.")
            return
            
        if not self.deeds_file_path.text() and not self.mortgage_file_path.text():
            QMessageBox.warning(self, "Missing Files", 
                               "Please select at least one PDF file (Deeds or Mortgage Satisfactions).")
            return
        
        # Run the preview generation
        self.update_output("Generating batch preview...")
        self.progress_bar.setValue(5)
        self.preview_btn.setEnabled(False)
        
        self.preview_thread, self.preview_worker = run_simplifile_batch_preview(
            self.excel_file_path.text(),
            self.deeds_file_path.text(),
            self.mortgage_file_path.text()
        )
        
        # Connect signals
        self.preview_worker.status.connect(self.update_status)
        self.preview_worker.progress.connect(self.update_progress)
        self.preview_worker.error.connect(self.show_error)
        self.preview_worker.preview_ready.connect(self.show_preview_dialog)
        
        # Connect cleanup handlers
        self.preview_thread.finished.connect(lambda: self.preview_btn.setEnabled(True))
        
        # Start thread
        self.preview_thread.start()
    
    def show_preview_dialog(self, preview_json):
        """Show the preview dialog with the generated data"""
        try:
            preview_data = json.loads(preview_json)
            
            # Open the preview dialog
            dialog = BatchPreviewDialog(preview_data, self)
            dialog.exec()
            
        except Exception as e:
            self.show_error(f"Error displaying preview: {str(e)}")
    
    # Update the process_batch_upload method in SimplifileUI class
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
        
        # Confirm batch upload
        recipient_name = self.recipient_combo.currentText()
        message = f"Process batch upload to {recipient_name}?\n\n"
        
        if self.deeds_file_path.text():
            message += f"- Deed Documents: {os.path.basename(self.deeds_file_path.text())}\n"
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
        
        self.batch_thread, self.batch_worker = run_simplifile_batch_process(
            self.excel_file_path.text(),
            self.deeds_file_path.text(),
            self.mortgage_file_path.text(),
            api_token,
            submitter_id,
            recipient_id,
            preview_mode
        )
        
        # Connect signals
        self.batch_worker.status.connect(self.update_status)
        self.batch_worker.progress.connect(self.update_progress)
        self.batch_worker.error.connect(self.show_error)
        self.batch_worker.finished.connect(self.batch_process_finished)
        
        # Start thread
        self.batch_thread.start()

    # Update the batch_process_finished method in SimplifileUI class
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
        
        self.update_output("Batch upload information cleared")
    
    # Existing methods from SimplifileUI class
    def add_document(self, doc_data=None):
        """Add a new document to the package"""
        dialog = DocumentDialog(self, doc_data)
        
        if dialog.exec():
            doc_data = dialog.get_document_data()
            if doc_data:
                # Add or update in documents list
                if doc_data in self.documents:
                    idx = self.documents.index(doc_data)
                    self.documents[idx] = doc_data
                else:
                    self.documents.append(doc_data)
                
                self.update_document_table()
                self.update_output(f"Added document: {doc_data['name']}")
    
    def edit_document(self, row):
        """Edit an existing document"""
        if 0 <= row < len(self.documents):
            doc_data = self.documents[row]
            self.add_document(doc_data)
    
    def remove_document(self, row):
        """Remove a document from the package"""
        if 0 <= row < len(self.documents):
            doc_name = self.documents[row]["name"]
            self.documents.pop(row)
            self.update_document_table()
            self.update_output(f"Removed document: {doc_name}")
    
    def update_document_table(self):
        """Update the document table display"""
        self.doc_table.setRowCount(0)
        
        for i, doc in enumerate(self.documents):
            self.doc_table.insertRow(i)
            
            # Document name
            self.doc_table.setItem(i, 0, QTableWidgetItem(doc.get("name", "")))
            
            # Document type
            self.doc_table.setItem(i, 1, QTableWidgetItem(doc.get("type", "")))
            
            # Additional persons summary
            person_count = len(doc.get("person_grantors", []))
            persons_text = f"{person_count} additional person(s)"
            self.doc_table.setItem(i, 2, QTableWidgetItem(persons_text))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, row=i: self.edit_document(row))
            
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_document(row))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(remove_btn)
            
            actions_widget.setLayout(actions_layout)
            self.doc_table.setCellWidget(i, 3, actions_widget)
    
    def save_api_settings(self):
        """Save API settings to config"""
        self.config["api_token"] = self.api_token.text()
        self.config["submitter_id"] = self.submitter_id.text()
        self.config["recipient_id"] = self.recipient_combo.currentData()
        
        if self.save_config():
            self.update_output("API configuration saved successfully")
        else:
            self.update_output("Error saving API configuration")
    
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
        
        # Prepare package data
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
    
    def upload_finished(self, response_data):
        """Handle completion of upload"""
        self.upload_btn.setEnabled(True)
        self.batch_upload_btn.setEnabled(True)
        
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
    
    def show_error(self, error_message):
        """Display error message"""
        self.update_output(f"Error: {error_message}")
        QMessageBox.critical(self, "Upload Error", error_message)
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

class PersonDialog(QDialog):
    """Dialog for adding person grantors or grantees"""
    
    def __init__(self, parent=None, person_data=None, title="Add Person"):
        super().__init__(parent)
        self.person_data = person_data or {}
        self.setWindowTitle(title)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.first_name = QLineEdit(self.person_data.get("first_name", ""))
        self.first_name.setPlaceholderText("First Name")
        layout.addRow("First Name:", self.first_name)
        
        self.middle_name = QLineEdit(self.person_data.get("middle_name", ""))
        self.middle_name.setPlaceholderText("Middle Name (Optional)")
        layout.addRow("Middle Name:", self.middle_name)
        
        self.last_name = QLineEdit(self.person_data.get("last_name", ""))
        self.last_name.setPlaceholderText("Last Name")
        layout.addRow("Last Name:", self.last_name)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def get_person_data(self):
        """Get the person data from the form"""
        if not self.first_name.text() or not self.last_name.text():
            QMessageBox.warning(self, "Missing Information", 
                               "First name and last name are required.")
            return None
        
        return {
            "first_name": self.first_name.text(),
            "middle_name": self.middle_name.text(),
            "last_name": self.last_name.text()
        }

class OrganizationDialog(QDialog):
    """Dialog for adding organization grantors or grantees"""
    
    def __init__(self, parent=None, org_data=None, title="Add Organization"):
        super().__init__(parent)
        self.org_data = org_data or {}
        self.setWindowTitle(title)
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        
        self.name = QLineEdit(self.org_data.get("name", ""))
        self.name.setPlaceholderText("Organization Name (will be converted to uppercase)")
        layout.addRow("Organization Name:", self.name)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addRow("", button_layout)
        self.setLayout(layout)
    
    def get_org_data(self):
        """Get the organization data from the form"""
        if not self.name.text():
            QMessageBox.warning(self, "Missing Information", 
                               "Organization name is required.")
            return None
        
        return {
            "name": self.name.text().upper()
        }

class DocumentDialog(QDialog):
    """Dialog for adding or editing a document in the package"""
    
    def __init__(self, parent=None, doc_data=None):
        super().__init__(parent)
        self.doc_data = doc_data or {}
        self.person_grantors = self.doc_data.get("person_grantors", [])
        self.person_grantees = self.doc_data.get("person_grantees", [])
        self.org_grantors = self.doc_data.get("org_grantors", [])
        self.org_grantees = self.doc_data.get("org_grantees", [])
        self.setWindowTitle("Document Details")
        self.setMinimumWidth(700)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Main document form
        form_layout = QFormLayout()
        
        # File path selection
        file_path_layout = QHBoxLayout()
        self.file_path = QLineEdit(self.doc_data.get("file_path", ""))
        self.file_path.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)
        file_path_layout.addWidget(self.file_path)
        file_path_layout.addWidget(browse_btn)
        form_layout.addRow("Document File:", file_path_layout)
        
        # Document ID and Name
        self.doc_id = QLineEdit(self.doc_data.get("document_id", ""))
        self.doc_id.setPlaceholderText("e.g., D-12345")
        form_layout.addRow("Document ID:", self.doc_id)
        
        self.doc_name = QLineEdit(self.doc_data.get("name", ""))
        self.doc_name.setPlaceholderText("e.g., SMITH 12345")
        self.doc_name.setToolTip("Will be converted to uppercase automatically")
        form_layout.addRow("Document Name:", self.doc_name)
        
        # Document type
        self.doc_type = QComboBox()
        self.doc_type.addItems(DOCUMENT_TYPES)
        current_type = self.doc_data.get("type", DOCUMENT_TYPES[0])
        if current_type in DOCUMENT_TYPES:
            self.doc_type.setCurrentText(current_type)
        form_layout.addRow("Document Type:", self.doc_type)
        
        # Consideration
        self.consideration = QLineEdit(self.doc_data.get("consideration", "0.00"))
        form_layout.addRow("Consideration:", self.consideration)
        
        # Execution date
        self.execution_date = QDateEdit()
        self.execution_date.setDisplayFormat("MM/dd/yyyy")
        current_date = QDate.currentDate()
        if "execution_date" in self.doc_data:
            try:
                date_parts = self.doc_data["execution_date"].split("/")
                if len(date_parts) == 3:
                    current_date = QDate(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))
            except:
                pass
        self.execution_date.setDate(current_date)
        form_layout.addRow("Execution Date:", self.execution_date)
        
        # Legal description
        self.legal_description = QTextEdit(self.doc_data.get("legal_description", ""))
        self.legal_description.setMaximumHeight(100)
        self.legal_description.setToolTip("Will be converted to uppercase automatically")
        form_layout.addRow("Legal Description:", self.legal_description)
        
        # Parcel ID
        self.parcel_id = QLineEdit(self.doc_data.get("parcel_id", ""))
        self.parcel_id.setToolTip("Will be converted to uppercase automatically")
        form_layout.addRow("Parcel ID:", self.parcel_id)
        
        # Default Parties Section - Show the automatically included parties
        default_group = QGroupBox("Default Parties (Always Included)")
        default_layout = QVBoxLayout()
        
        # Default Grantors
        default_layout.addWidget(QLabel("<b>Default Grantors:</b>"))
        for grantor in DEFAULT_GRANTORS:
            label = QLabel(f"• {grantor['nameUnparsed']} (Organization)")
            default_layout.addWidget(label)
        
        # Default Grantees
        default_layout.addWidget(QLabel("<b>Default Grantees:</b>"))
        for grantee in DEFAULT_GRANTEES:
            label = QLabel(f"• {grantee['nameUnparsed']} (Organization)")
            default_layout.addWidget(label)
        
        default_group.setLayout(default_layout)
        
        # Additional Parties Section
        parties_group = QGroupBox("Additional Parties")
        parties_layout = QVBoxLayout()
        
        # Additional Grantors Section
        grantor_layout = QVBoxLayout()
        grantor_layout.addWidget(QLabel("<b>Additional Grantors:</b>"))
        
        # Person Grantors Table
        self.person_grantor_table = QTableWidget(0, 4)
        self.person_grantor_table.setHorizontalHeaderLabels(["First Name", "Middle Name", "Last Name", "Actions"])
        self.person_grantor_table.horizontalHeader().setStretchLastSection(True)
        self.person_grantor_table.setMinimumHeight(100)
        grantor_layout.addWidget(self.person_grantor_table)
        
        # Org Grantors Table
        self.org_grantor_table = QTableWidget(0, 2)
        self.org_grantor_table.setHorizontalHeaderLabels(["Organization Name", "Actions"])
        self.org_grantor_table.horizontalHeader().setStretchLastSection(True)
        self.org_grantor_table.setMinimumHeight(50)
        grantor_layout.addWidget(self.org_grantor_table)
        
        # Grantor Buttons
        grantor_buttons = QHBoxLayout()
        add_person_grantor_btn = QPushButton("Add Person Grantor")
        add_person_grantor_btn.clicked.connect(lambda: self.add_person("grantor"))
        
        add_org_grantor_btn = QPushButton("Add Organization Grantor")
        add_org_grantor_btn.clicked.connect(lambda: self.add_organization("grantor"))
        
        grantor_buttons.addWidget(add_person_grantor_btn)
        grantor_buttons.addWidget(add_org_grantor_btn)
        grantor_layout.addLayout(grantor_buttons)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        
        # Additional Grantees Section
        grantee_layout = QVBoxLayout()
        grantee_layout.addWidget(QLabel("<b>Additional Grantees:</b>"))
        
        # Person Grantees Table
        self.person_grantee_table = QTableWidget(0, 4)
        self.person_grantee_table.setHorizontalHeaderLabels(["First Name", "Middle Name", "Last Name", "Actions"])
        self.person_grantee_table.horizontalHeader().setStretchLastSection(True)
        self.person_grantee_table.setMinimumHeight(100)
        grantee_layout.addWidget(self.person_grantee_table)
        
        # Org Grantees Table
        self.org_grantee_table = QTableWidget(0, 2)
        self.org_grantee_table.setHorizontalHeaderLabels(["Organization Name", "Actions"])
        self.org_grantee_table.horizontalHeader().setStretchLastSection(True)
        self.org_grantee_table.setMinimumHeight(50)
        grantee_layout.addWidget(self.org_grantee_table)
        
        # Grantee Buttons
        grantee_buttons = QHBoxLayout()
        add_person_grantee_btn = QPushButton("Add Person Grantee")
        add_person_grantee_btn.clicked.connect(lambda: self.add_person("grantee"))
        
        add_org_grantee_btn = QPushButton("Add Organization Grantee")
        add_org_grantee_btn.clicked.connect(lambda: self.add_organization("grantee"))
        
        grantee_buttons.addWidget(add_person_grantee_btn)
        grantee_buttons.addWidget(add_org_grantee_btn)
        grantee_layout.addLayout(grantee_buttons)
        
        # Assemble the parties layout
        parties_layout.addLayout(grantor_layout)
        parties_layout.addWidget(separator)
        parties_layout.addLayout(grantee_layout)
        parties_group.setLayout(parties_layout)
        
        # Load existing parties
        for person in self.person_grantors:
            self.add_person_to_table("grantor", person)
        
        for person in self.person_grantees:
            self.add_person_to_table("grantee", person)
            
        for org in self.org_grantors:
            self.add_org_to_table("grantor", org)
            
        for org in self.org_grantees:
            self.add_org_to_table("grantee", org)
        
        # Add layouts to main layout
        layout.addLayout(form_layout)
        layout.addWidget(default_group)
        layout.addWidget(parties_group)
        
        # Button box
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if file_path:
            self.file_path.setText(file_path)
            # Set default document name from filename if empty
            if not self.doc_name.text():
                base_name = os.path.basename(file_path)
                name_without_ext = os.path.splitext(base_name)[0]
                self.doc_name.setText(name_without_ext.upper())
    
    def add_person(self, party_type):
        """Add a person to grantors or grantees"""
        title = f"Add Person {party_type.capitalize()}"
        dialog = PersonDialog(self, title=title)
        if dialog.exec():
            person_data = dialog.get_person_data()
            if person_data:
                if party_type == "grantor":
                    self.person_grantors.append(person_data)
                else:
                    self.person_grantees.append(person_data)
                self.add_person_to_table(party_type, person_data)
    
    def add_organization(self, party_type):
        """Add an organization to grantors or grantees"""
        title = f"Add Organization {party_type.capitalize()}"
        dialog = OrganizationDialog(self, title=title)
        if dialog.exec():
            org_data = dialog.get_org_data()
            if org_data:
                if party_type == "grantor":
                    self.org_grantors.append(org_data)
                else:
                    self.org_grantees.append(org_data)
                self.add_org_to_table(party_type, org_data)
    
    def add_person_to_table(self, party_type, person_data):
        """Add a person to the appropriate table"""
        table = self.person_grantor_table if party_type == "grantor" else self.person_grantee_table
        row = table.rowCount()
        table.insertRow(row)
        
        table.setItem(row, 0, QTableWidgetItem(person_data.get("first_name", "")))
        table.setItem(row, 1, QTableWidgetItem(person_data.get("middle_name", "")))
        table.setItem(row, 2, QTableWidgetItem(person_data.get("last_name", "")))
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_person(party_type, row))
        table.setCellWidget(row, 3, remove_btn)
    
    def add_org_to_table(self, party_type, org_data):
        """Add an organization to the appropriate table"""
        table = self.org_grantor_table if party_type == "grantor" else self.org_grantee_table
        row = table.rowCount()
        table.insertRow(row)
        
        table.setItem(row, 0, QTableWidgetItem(org_data.get("name", "")))
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_org(party_type, row))
        table.setCellWidget(row, 1, remove_btn)
    
    def remove_person(self, party_type, row):
        """Remove a person from grantors or grantees"""
        if party_type == "grantor":
            table = self.person_grantor_table
            if 0 <= row < len(self.person_grantors):
                self.person_grantors.pop(row)
                table.removeRow(row)
        else:
            table = self.person_grantee_table
            if 0 <= row < len(self.person_grantees):
                self.person_grantees.pop(row)
                table.removeRow(row)
    
    def remove_org(self, party_type, row):
        """Remove an organization from grantors or grantees"""
        if party_type == "grantor":
            table = self.org_grantor_table
            if 0 <= row < len(self.org_grantors):
                self.org_grantors.pop(row)
                table.removeRow(row)
        else:
            table = self.org_grantee_table
            if 0 <= row < len(self.org_grantees):
                self.org_grantees.pop(row)
                table.removeRow(row)
    
    def get_document_data(self):
        """Get all document data from the form"""
        if not self.file_path.text():
            QMessageBox.warning(self, "Missing File", "Please select a document file.")
            return None
        
        # Basic document info
        doc_data = {
            "file_path": self.file_path.text(),
            "document_id": self.doc_id.text(),
            "name": self.doc_name.text().upper(),
            "type": self.doc_type.currentText(),
            "consideration": self.consideration.text(),
            "execution_date": self.execution_date.date().toString("MM/dd/yyyy"),
            "legal_description": self.legal_description.toPlainText().upper(),
            "parcel_id": self.parcel_id.text().upper(),
            "person_grantors": self.person_grantors,
            "person_grantees": self.person_grantees,
            "org_grantors": self.org_grantors,
            "org_grantees": self.org_grantees
        }
        
        return doc_data