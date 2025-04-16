# simplifile_ui.py - Updated to use centralized models
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QFileDialog, QMessageBox, 
    QGroupBox, QTableWidget, QTableWidgetItem,
    QTextEdit, QProgressBar, QFrame, QTabWidget, QApplication,
)
from PyQt6.QtCore import (
    pyqtSignal, Qt, QTimer
)

from simplifile.batch_processor import run_simplifile_batch_preview, run_simplifile_batch_process
from simplifile.api import run_simplifile_connection_test
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
        """Generate enhanced preview of batch processing with reduced output messages"""
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
        
        # Connect signals - but filter status messages
        self.preview_worker.status.connect(self.filter_status_updates)
        self.preview_worker.progress.connect(self.update_progress)
        self.preview_worker.error.connect(self.show_error)
        self.preview_worker.preview_ready.connect(self.show_enhanced_preview_dialog)
        
        # Connect cleanup handlers
        self.preview_thread.finished.connect(lambda: self.preview_btn.setEnabled(True))
        
        # Start thread
        self.preview_thread.start()


    def filter_status_updates(self, status_message):
        """Filter status updates with rate limiting to prevent UI freezing"""
        # Define messages to ignore (don't output these to the window)
        ignore_messages = [
            "Starting preview generation...",
            "Analyzing deed documents...",
            "Analyzing affidavit documents...",
            "Analyzing merged deed and affidavit documents...",
            "Analyzing mortgage satisfaction documents..."
        ]
        
        # Only update status label for all messages (keep UI responsive)
        self.status_label.setText(status_message)
        
        # But only output to text area if it's not in the ignore list
        if status_message not in ignore_messages:
            # Use the asynchronous update method
            self.update_output(status_message)


    def show_enhanced_preview_dialog(self, preview_json):
        """Show the enhanced preview dialog with the generated data and output validation warnings"""
        try:
            # Convert JSON to Python object if it's a string
            preview_data = json.loads(preview_json) if isinstance(preview_json, str) else preview_json
            
            # Output validation warnings to the output window
            validation = preview_data.get("validation", {})
            validation_summary = preview_data.get("validation_summary", {})
            
            # Output validation summary
            total_issues = (
                validation_summary.get("missing_data_issues", 0) + 
                validation_summary.get("format_issues", 0) + 
                validation_summary.get("document_issues", 0)
            )
            
            if total_issues > 0:
                self.update_output(f"⚠️ Validation found {total_issues} potential issues:")
                
                # Output missing data issues
                for issue in validation.get("missing_data", []):
                    self.update_output(f"  ❗ Missing data: {issue}")
                
                # Output format issues (from Excel validation)
                for issue in validation.get("format_issues", []):
                    self.update_output(f"  ⚠️ Format issue: {issue}")
                
                # Output document issues
                for issue in validation.get("document_issues", []):
                    self.update_output(f"  ❗ Document issue: {issue}")
                    
                self.update_output("Review the preview window for more details.")
            else:
                self.update_output("✅ Validation complete: No issues found!")
            
            # Open the enhanced preview dialog with the JSON data
            dialog = BatchPreviewDialog(preview_data, self)
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
        """Process and start the batch upload with non-blocking UI updates"""
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
        mode_text = 'preview' if preview_mode else 'API upload'
        self.update_output(f"Starting batch processing in {mode_text} mode...")
        self.progress_bar.setValue(5)
        self.batch_upload_btn.setEnabled(False)
        
        # Create a "processing" indicator for the status bar
        self.show_processing_indicator()
        
        # Get file paths before passing to thread
        excel_path = self.excel_file_path.text()
        deeds_path = self.deeds_file_path.text()
        mortgage_path = self.mortgage_file_path.text()
        affidavits_path = self.affidavits_file_path.text() if hasattr(self, 'affidavits_file_path') else None
        
        # Use the centralized batch processor to run the operation
        self.batch_thread, self.batch_worker = run_simplifile_batch_process(
            excel_path,
            deeds_path,
            mortgage_path,
            api_token,
            submitter_id,
            recipient_id,
            preview_mode,
            affidavits_path
        )
        
        # Connect signals with filtering for status messages
        # Update with correct PyQt6 connection type
        self.batch_worker.status.connect(
            self.filter_status_updates, 
            type=Qt.ConnectionType.QueuedConnection
        )
        self.batch_worker.progress.connect(
            self.update_progress, 
            type=Qt.ConnectionType.QueuedConnection
        )
        self.batch_worker.error.connect(
            self.show_error, 
            type=Qt.ConnectionType.QueuedConnection
        )
        self.batch_worker.finished.connect(
            self.batch_process_finished, 
            type=Qt.ConnectionType.QueuedConnection
        )
        
        # Connect thread finished to remove processing indicator
        self.batch_thread.finished.connect(self.hide_processing_indicator)
        
        # Start thread
        self.batch_thread.start()


    def show_processing_indicator(self):
        """Show a processing indicator in the status bar"""
        self.processing_label = QLabel("⏳ Processing...")
        self.statusBar().addWidget(self.processing_label)
        
        # We can also show a "busy" cursor for the application
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # Start a timer to animate the indicator
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self.update_processing_indicator)
        self.processing_timer.start(500)  # Update every 500ms
        
        # Set window title to indicate processing
        self.setWindowTitle(f"{self.windowTitle()} - Processing...")


    def update_processing_indicator(self):
        """Animate the processing indicator"""
        if hasattr(self, 'processing_label') and self.processing_label:
            current_text = self.processing_label.text()
            if "⏳ Processing..." == current_text:
                self.processing_label.setText("⌛ Processing...")
            else:
                self.processing_label.setText("⏳ Processing...")


    def hide_processing_indicator(self):
        """Hide the processing indicator when done"""
        if hasattr(self, 'processing_timer') and self.processing_timer:
            self.processing_timer.stop()
            
        if hasattr(self, 'processing_label') and self.processing_label:
            self.statusBar().removeWidget(self.processing_label)
            self.processing_label = None
        
        # Restore normal cursor
        QApplication.restoreOverrideCursor()
        
        # Restore original window title
        if " - Processing..." in self.windowTitle():
            self.setWindowTitle(self.windowTitle().replace(" - Processing...", ""))


    def batch_process_finished(self, result_data):
        """Handle completion of batch processing with improved summary statistics"""
        self.batch_upload_btn.setEnabled(True)
        
        # Extract summary statistics
        summary = result_data.get("summary", {})
        total = summary.get("total", 0)
        successful = summary.get("successful", 0)
        failed = summary.get("failed", 0)
        
        # Get result status
        result_code = result_data.get("resultCode", "")
        
        # Display clear summary statistics header
        self.update_output("")  # Add blank line for separation
        self.update_output("====== BATCH PROCESSING SUMMARY ======")
        self.update_output(f"📊 Total packages: {total}")
        self.update_output(f"✅ Successfully uploaded: {successful}")
        self.update_output(f"❌ Failed to upload: {failed}")
        
        # Handle different result scenarios
        if result_code == "SUCCESS":
            self.update_output("✨ Status: COMPLETE SUCCESS")
            self.update_output("======================================")
            
            # Show success message
            QMessageBox.information(
                self,
                "Processing Complete",
                f"Batch processing completed successfully!\n\n"
                f"✅ All {successful} packages were uploaded successfully."
            )
            
        elif result_code == "PARTIAL_SUCCESS":
            self.update_output("⚠️ Status: PARTIAL SUCCESS")
            self.update_output("======================================")
            
            # Only show details for failed packages
            if failed > 0:
                self.update_output("\n❌ Failed packages:")
                packages = result_data.get("packages", [])
                
                # Group failures by error type
                error_groups = {}
                for package in packages:
                    if package.get("status") != "success":
                        error_type = package.get("status", "unknown")
                        package_name = package.get("package_name", "")
                        
                        if error_type not in error_groups:
                            error_groups[error_type] = []
                        
                        error_groups[error_type].append(package_name)
                
                # Display error summary by group
                for error_type, package_list in error_groups.items():
                    self.update_output(f"\n  Error type: {error_type.upper()} ({len(package_list)} packages)")
                    # Show first 5 packages of this error type
                    for i, package_name in enumerate(package_list):
                        if i < 5:
                            self.update_output(f"    • {package_name}")
                        elif i == 5:
                            self.update_output(f"    • ... and {len(package_list) - 5} more")
                            break
                
                # Show detailed warning dialog
                QMessageBox.warning(
                    self,
                    "Partial Success",
                    f"Batch processing completed with partial success.\n\n"
                    f"✅ {successful} of {total} packages were uploaded successfully.\n"
                    f"❌ {failed} of {total} packages failed.\n\n"
                    f"See the output window for details on failed packages."
                )
            else:
                # This shouldn't happen, but just in case
                QMessageBox.information(
                    self,
                    "Processing Complete",
                    f"Batch processing completed successfully!"
                )
                
        else:  # FAILED or ERROR
            self.update_output("🛑 Status: FAILED")
            self.update_output("======================================")
            
            # Extract main error message
            error_msg = result_data.get("message", "Unknown error")
            
            # Show error dialog with summary
            QMessageBox.critical(
                self,
                "Processing Failed",
                f"Batch processing failed.\n\n"
                f"Error: {error_msg}\n\n"
                f"See the output window for detailed error information."
            )
            
            # If there are packages with specific errors, summarize them
            packages = result_data.get("packages", [])
            if packages:
                # Group failures by error type
                error_groups = {}
                for package in packages:
                    error_type = package.get("status", "unknown")
                    error_msg = package.get("message", "Unknown error")
                    package_name = package.get("package_name", "")
                    
                    # Create a key based on both error type and message
                    # This helps group similar errors together
                    key = f"{error_type}: {error_msg[:50]}"
                    
                    if key not in error_groups:
                        error_groups[key] = {
                            "count": 0,
                            "type": error_type,
                            "message": error_msg,
                            "examples": []
                        }
                    
                    error_groups[key]["count"] += 1
                    if len(error_groups[key]["examples"]) < 3:
                        error_groups[key]["examples"].append(package_name)
                
                # Display error summary by group
                self.update_output("\n🔍 Error analysis:")
                for key, info in error_groups.items():
                    self.update_output(f"\n  {info['type'].upper()} ({info['count']} packages):")
                    self.update_output(f"    Message: {info['message']}")
                    if info["examples"]:
                        self.update_output(f"    Examples: {', '.join(info['examples'])}" + 
                                        (f" and {info['count'] - len(info['examples'])} more" 
                                        if info['count'] > len(info['examples']) else ""))
        
        # Always produce final outcome statement
        self.update_output("\n📋 Final outcome:")
        if successful == total:
            self.update_output(f"  ✅ All {total} packages were processed successfully.")
        elif successful > 0:
            self.update_output(f"  ⚠️ {successful} of {total} packages were successful, {failed} failed.")
        else:
            self.update_output(f"  ❌ All {total} packages failed to process.")


    def copy_to_clipboard(self, text):
        """Helper method to copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Copied", "Error report copied to clipboard")


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
        """Update the progress bar with rate limiting to prevent UI freezing"""
        # Don't update progress bar too frequently - can cause UI freezing
        current_time = datetime.now()
        should_update = True
        
        # Rate limit updates to reduce UI pressure (only for small increments)
        if hasattr(self, '_last_progress_update'):
            time_diff = (current_time - self._last_progress_update).total_seconds()
            value_diff = abs(value - self._last_progress_value)
            
            # Only update if it's been at least 0.1 seconds or the change is significant
            if time_diff < 0.1 and value_diff < 5:
                should_update = False
        
        if should_update:
            self.progress_bar.setValue(value)
            self._last_progress_update = current_time
            self._last_progress_value = value
        
        # Process events occasionally to keep UI responsive
        QApplication.processEvents()


    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)
        self.update_output(status)


    def update_output(self, message):
        """Add a message to the output text area with enhanced formatting"""
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        
        # Check for error/success indicators to add color formatting
        html_message = message
        if "❌" in message or "Error:" in message or "Failed:" in message:
            # Format error messages in red
            html_message = f'<span style="color: #d9534f;">{message}</span>'
        elif "✅" in message or "Success" in message:
            # Format success messages in green
            html_message = f'<span style="color: #5cb85c;">{message}</span>'
        elif "⚠️" in message or "Warning:" in message:
            # Format warning messages in orange
            html_message = f'<span style="color: #f0ad4e;">{message}</span>'
        elif "📊" in message:
            # Format statistics in blue
            html_message = f'<span style="color: #5bc0de;">{message}</span>'
        
        # Enable rich text if we're using HTML formatting
        if html_message != message:
            current_format = self.output_text.currentCharFormat()
            self.output_text.setHtml(self.output_text.toHtml() + f"{timestamp} {html_message}<br>")
        else:
            # Plain text append for regular messages
            self.output_text.append(f"{timestamp} {message}")
        
        # Scroll to the bottom
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )


    def show_error(self, error_message):
        """Display enhanced error message with better formatting"""
        self.update_output(f"❌ Error: {error_message}")
        
        # Check for common API-related keywords to enhance the message
        if "API" in error_message and ("token" in error_message.lower() or "unauthorized" in error_message.lower()):
            error_message += "\n\nThis appears to be an API authentication issue. Please check your API token and submitter ID."
        elif "connection" in error_message.lower():
            error_message += "\n\nThis appears to be a network connection issue. Please check your internet connection."
        elif "timeout" in error_message.lower():
            error_message += "\n\nThe request timed out. This could be due to large files or server issues."
        
        QMessageBox.critical(self, "Process Error", error_message)
        self.upload_btn.setEnabled(True)
        self.batch_upload_btn.setEnabled(True)


    def update_output(self, message):
        """Add a message to the output text area with efficient UI updates"""
        # Use QTimer.singleShot to process UI updates on the main thread without blocking
        QTimer.singleShot(0, lambda: self._do_update_output(message))


    def _do_update_output(self, message):
        """Actual implementation of update_output to be run in the main thread"""
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        
        # Check for error/success indicators to add color formatting
        html_message = message
        if "❌" in message or "Error:" in message or "Failed:" in message:
            # Format error messages in red
            html_message = f'<span style="color: #d9534f;">{message}</span>'
        elif "✅" in message or "Success" in message:
            # Format success messages in green
            html_message = f'<span style="color: #5cb85c;">{message}</span>'
        elif "⚠️" in message or "Warning:" in message:
            # Format warning messages in orange
            html_message = f'<span style="color: #f0ad4e;">{message}</span>'
        elif "📊" in message:
            # Format statistics in blue
            html_message = f'<span style="color: #5bc0de;">{message}</span>'
        
        # Enable rich text if we're using HTML formatting
        if html_message != message:
            self.output_text.insertHtml(f"{timestamp} {html_message}<br>")
        else:
            # Plain text append for regular messages
            self.output_text.append(f"{timestamp} {message}")
        
        # Scroll to the bottom - avoid using full scrollbar calculation which can be expensive
        self.output_text.ensureCursorVisible()


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


    def display_error_summary(self, result_data):
        """Display a clear, concise summary of error categories"""
        if "error_categories" not in result_data or not result_data["error_categories"]:
            return
        
        self.update_output("\n🔍 Error Category Summary:")
        
        # Sort categories by count (highest first)
        sorted_categories = sorted(
            result_data["error_categories"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        for category_key, info in sorted_categories:
            # Create a bar chart-like visualization
            count = info["count"]
            description = info["description"]
            bar_length = min(40, count)  # Limit bar length for very large numbers
            
            # Create a simple ASCII bar
            bar = "█" * bar_length
            
            self.update_output(f"  {description}: {count}")
            self.update_output(f"  {bar}")
            
            # Show examples if available
            if info["examples"]:
                self.update_output("  Examples:")
                for i, example in enumerate(info["examples"]):
                    pkg_id = example.get("package_id", "")
                    message = example.get("message", "")
                    
                    # Truncate very long messages
                    if len(message) > 100:
                        message = message[:100] + "..."
                        
                    self.update_output(f"    • Package {pkg_id}: {message}")


    def batch_process_finished(self, result_data):
        """Handle completion of batch processing with improved summary statistics and visualization"""
        self.batch_upload_btn.setEnabled(True)
    
        # Process large result data asynchronously
        QTimer.singleShot(0, lambda: self._process_batch_result(result_data))


    def _process_batch_result(self, result_data):
        """Process batch result data in the main thread without blocking"""
        # Extract summary statistics
        summary = result_data.get("summary", {})
        total = summary.get("total", 0)
        successful = summary.get("successful", 0)
        failed = summary.get("failed", 0)
        
        # Get result status
        result_code = result_data.get("resultCode", "")
        
        # Display clear summary statistics header
        self.update_output("")  # Add blank line for separation
        self.update_output("====== BATCH PROCESSING SUMMARY ======")
        self.update_output(f"📊 Total packages: {total}")
        self.update_output(f"✅ Successfully uploaded: {successful}")
        self.update_output(f"❌ Failed to upload: {failed}")
        
        # Add a visual representation of success/failure ratio
        if total > 0:
            success_ratio = successful / total
            bar_length = 30  # Total bar length
            success_bar = "█" * int(bar_length * success_ratio)
            fail_bar = "▒" * (bar_length - int(bar_length * success_ratio))
            
            # Colorize if possible with HTML formatting
            success_percent = int(success_ratio * 100)
            self.update_output(f"📈 Success rate: {success_percent}%")
            self.update_output(f"  {success_bar}{fail_bar}")
        
        # Handle different result scenarios - use QTimer to avoid blocking
        if result_code == "SUCCESS":
            self.update_output("✨ Status: COMPLETE SUCCESS")
            self.update_output("======================================")
            
            # Show success message using a timer to avoid blocking
            QTimer.singleShot(100, lambda: QMessageBox.information(
                self,
                "Processing Complete",
                f"Batch processing completed successfully!\n\n"
                f"✅ All {successful} packages were uploaded successfully."
            ))
            
        elif result_code == "PARTIAL_SUCCESS":
            self.update_output("⚠️ Status: PARTIAL SUCCESS")
            self.update_output("======================================")
            
            # Display error category summary - limit to most common errors
            self._display_error_summary_limited(result_data)
            
            # Show detailed warning dialog after a short delay
            QTimer.singleShot(100, lambda: QMessageBox.warning(
                self,
                "Partial Success",
                f"Batch processing completed with partial success.\n\n"
                f"✅ {successful} of {total} packages were uploaded successfully.\n"
                f"❌ {failed} of {total} packages failed.\n\n"
                f"See the output window for details on failed packages."
            ))
                
        else:  # FAILED or ERROR
            self.update_output("🛑 Status: FAILED")
            self.update_output("======================================")
            
            # Display error category summary - limit to most common errors
            self._display_error_summary_limited(result_data)
            
            # Extract main error message
            error_msg = result_data.get("message", "Unknown error")
            error_summary = result_data.get("error_summary", "")
            
            # Show error dialog with summary after a short delay
            error_details = f"Error: {error_msg}"
            if error_summary:
                error_details += f"\n\nError summary: {error_summary}"
                
            QTimer.singleShot(100, lambda: QMessageBox.critical(
                self,
                "Processing Failed",
                f"Batch processing failed.\n\n{error_details}\n\n"
                f"See the output window for detailed error information."
            ))
        
        # Always produce final outcome statement
        self.update_output("\n📋 Final outcome:")
        if successful == total:
            self.update_output(f"  ✅ All {total} packages were processed successfully.")
        elif successful > 0:
            self.update_output(f"  ⚠️ {successful} of {total} packages were successful, {failed} failed.")
        else:
            self.update_output(f"  ❌ All {total} packages failed to process.")
            
        # Add timestamp
        self.update_output(f"\n⏱️ Process completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


    def _display_error_summary_limited(self, result_data):
        """Display a clear, concise summary of error categories with limits to prevent UI freezing"""
        if "error_categories" not in result_data or not result_data["error_categories"]:
            return
        
        self.update_output("\n🔍 Error Category Summary:")
        
        # Sort categories by count (highest first)
        sorted_categories = sorted(
            result_data["error_categories"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        # Limit to top 5 categories to prevent UI overload
        for i, (category_key, info) in enumerate(sorted_categories):
            if i >= 5:  # Only show top 5 categories
                remaining = len(sorted_categories) - 5
                if remaining > 0:
                    self.update_output(f"  ... and {remaining} more error categories")
                break
                
            # Create a bar chart-like visualization
            count = info["count"]
            description = info["description"]
            bar_length = min(20, count)  # Limit bar length for very large numbers
            
            # Create a simple ASCII bar
            bar = "█" * bar_length
            
            self.update_output(f"  {description}: {count}")
            self.update_output(f"  {bar}")
            
            # Show examples if available - limit to 2 examples max
            if info["examples"]:
                self.update_output("  Examples:")
                for i, example in enumerate(info["examples"]):
                    if i >= 2:  # Only show 2 examples max
                        remaining = len(info["examples"]) - 2
                        if remaining > 0:
                            self.update_output(f"    • ... and {remaining} more similar errors")
                        break
                        
                    pkg_id = example.get("package_id", "")
                    message = example.get("message", "")
                    
                    # Truncate very long messages
                    if len(message) > 80:
                        message = message[:80] + "..."
                        
                    self.update_output(f"    • Package {pkg_id}: {message}")