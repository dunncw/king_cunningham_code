# simplifile_ui.py - Updated to remove single upload functionality
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QFormLayout, QFileDialog, QMessageBox, 
    QGroupBox, QTextEdit, QProgressBar, QFrame
)
from PyQt6.QtCore import (
    pyqtSignal, Qt, QTimer
)

from simplifile.batch_processor import run_simplifile_batch_preview, run_simplifile_batch_process
from simplifile.api import run_simplifile_connection_test
from .batch_preview_dialog import BatchPreviewDialog
from simplifile.county_config import COUNTY_CONFIGS, get_county_config


class SimplifileUI(QWidget):
    start_simplifile_batch_upload = pyqtSignal(str, str, str, str, str, str)

    def __init__(self):
        super().__init__()
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
                    "recipient_id": ""
                }
        except:
            self.config = {
                "api_token": "",
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
        
        # File Selection Section
        files_group = self.create_file_selection_group()
        main_layout.addWidget(files_group)
        
        # Batch preview
        preview_layout = QHBoxLayout()
        
        # Label for preview section
        preview_label = QLabel("Batch Preview:")
        preview_layout.addWidget(preview_label)
        
        # Preview button
        self.preview_btn = QPushButton("Generate Preview")
        self.preview_btn.clicked.connect(self.generate_enhanced_batch_preview)
        preview_layout.addWidget(self.preview_btn)
        preview_layout.addStretch()  # Push button to the left
        
        main_layout.addLayout(preview_layout)
        
        # Action buttons for batch upload
        actions_layout = QHBoxLayout()
        
        self.batch_upload_btn = QPushButton("Process Batch Upload")
        self.batch_upload_btn.clicked.connect(self.process_batch_upload)
        self.batch_upload_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        batch_clear_btn = QPushButton("Clear Batch")
        batch_clear_btn.clicked.connect(self.clear_batch)
        
        actions_layout.addWidget(batch_clear_btn)
        actions_layout.addWidget(self.batch_upload_btn)
        
        main_layout.addLayout(actions_layout)
        
        # Progress and output section
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.status_label = QLabel("Ready")
        
        progress_layout.addWidget(QLabel("Status:"))
        progress_layout.addWidget(self.status_label, 1)
        progress_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(progress_layout)
        
        # Output area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(150)
        main_layout.addWidget(self.output_text)
        
        self.setLayout(main_layout)
        
        # Update UI for initial county selection
        self.update_county_specific_ui(self.recipient_combo.currentIndex())

    def create_file_selection_group(self):
        """Create file selection group box with all document inputs"""
        files_group = QGroupBox("Document Files")
        files_layout = QFormLayout()
        
        # Excel File Selection
        excel_layout = QHBoxLayout()
        self.excel_file_path = QLineEdit()
        self.excel_file_path.setReadOnly(True)
        excel_browse_btn = QPushButton("Browse...")
        excel_browse_btn.clicked.connect(self.browse_excel_file)
        
        excel_layout.addWidget(self.excel_file_path)
        excel_layout.addWidget(excel_browse_btn)
        files_layout.addRow("Excel File:", excel_layout)
        
        # Deed Documents PDF Selection with county-specific label
        deeds_layout = QHBoxLayout()
        self.deeds_file_path = QLineEdit()
        self.deeds_file_path.setReadOnly(True)
        deeds_browse_btn = QPushButton("Browse...")
        deeds_browse_btn.clicked.connect(self.browse_deeds_file)
        deeds_layout.addWidget(self.deeds_file_path)
        deeds_layout.addWidget(deeds_browse_btn)
        self.deed_document_label = QLabel("Deed Documents (PDF):")
        files_layout.addRow(self.deed_document_label, deeds_layout)
        
        # Affidavit Documents PDF Selection
        affidavits_layout = QHBoxLayout()
        self.affidavits_file_path = QLineEdit()
        self.affidavits_file_path.setReadOnly(True)
        affidavits_browse_btn = QPushButton("Browse...")
        affidavits_browse_btn.clicked.connect(self.browse_affidavits_file)
        affidavits_layout.addWidget(self.affidavits_file_path)
        affidavits_layout.addWidget(affidavits_browse_btn)
        files_layout.addRow("Affidavits (PDF):", affidavits_layout)
        
        # Mortgage Satisfaction PDF Selection with county-specific label
        mortgage_layout = QHBoxLayout()
        self.mortgage_file_path = QLineEdit()
        self.mortgage_file_path.setReadOnly(True)
        mortgage_browse_btn = QPushButton("Browse...")
        mortgage_browse_btn.clicked.connect(self.browse_mortgage_file)
        mortgage_layout.addWidget(self.mortgage_file_path)
        mortgage_layout.addWidget(mortgage_browse_btn)
        self.mortgage_document_label = QLabel("Mortgage Satisfactions (PDF):")
        files_layout.addRow(self.mortgage_document_label, mortgage_layout)
        
        files_group.setLayout(files_layout)
        return files_group

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
        
        # County dropdown (recipient)
        self.recipient_combo = QComboBox()
        
        # Add an empty/initial option
        self.recipient_combo.addItem("-- Select County --", "")
        
        # Add all county options from config
        for county_id, county_config in COUNTY_CONFIGS.items():
            self.recipient_combo.addItem(county_config.COUNTY_NAME, county_id)
        
        # Set default from config if exists
        if self.config.get("recipient_id"):
            for i in range(self.recipient_combo.count()):
                if self.recipient_combo.itemData(i) == self.config["recipient_id"]:
                    self.recipient_combo.setCurrentIndex(i)
                    break

        # Connect change signal to update county-specific UI elements
        self.recipient_combo.currentIndexChanged.connect(self.update_county_specific_ui)
        
        # Add to form layout
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

    # Add a new method to update UI based on selected county
    def update_county_specific_ui(self, index):
        """Update UI elements based on selected county"""
        county_id = self.recipient_combo.currentData()
        if not county_id:
            return
            
        # Get county configuration
        county_config = get_county_config(county_id)
        
        # Update county-specific labels and hints in the UI
        self.update_output(f"Selected county: {county_config.COUNTY_NAME}")
        
        # Update document type labels
        if hasattr(self, 'deed_document_label'):
            self.deed_document_label.setText(f"Deed Documents ({county_config.DEED_DOCUMENT_TYPE}):")
            
        if hasattr(self, 'mortgage_document_label'):
            self.mortgage_document_label.setText(f"Mortgage Documents ({county_config.MORTGAGE_DOCUMENT_TYPE}):")
        
        # Update upload button text to include county name
        if hasattr(self, 'batch_upload_btn'):
            self.batch_upload_btn.setText(f"Process Batch Upload to {county_config.COUNTY_NAME}")
        
        # Update preview button to reflect county
        if hasattr(self, 'preview_btn'):
            self.preview_btn.setText(f"Generate Preview for {county_config.COUNTY_NAME}")
            
        # Save the selected county to config
        self.config["recipient_id"] = county_id
        self.save_config()

    def test_api_connection(self):
        """Test connection to Simplifile API with current credentials"""
        # Validate inputs
        api_token = self.api_token.text()
        submitter_id = "SCTP3G"  # Hardcoded submitter ID
        
        if not api_token:
            QMessageBox.warning(self, "Missing Credentials", 
                            "Please enter your API token to test the connection.")
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

    def generate_enhanced_batch_preview(self):
        """Generate enhanced preview of batch processing with county-specific configuration"""
        # Check if all required files are selected
        if not self.excel_file_path.text():
            QMessageBox.warning(self, "Missing File", "Please select an Excel file.")
            return
        
        if not self.deeds_file_path.text() and not self.mortgage_file_path.text():
            QMessageBox.warning(self, "Missing Files", 
                            "Please select at least one PDF file (Deeds or Mortgage Satisfactions).")
            return
        
        # Get selected county
        county_id = self.recipient_combo.currentData()
        if not county_id:
            QMessageBox.warning(self, "County Not Selected", "Please select a county before generating preview.")
            return
        
        # Run the enhanced preview generation with county ID
        self.update_output(f"Generating batch preview for {get_county_config(county_id).COUNTY_NAME}...")
        self.progress_bar.setValue(5)
        self.preview_btn.setEnabled(False)
        
        self.preview_thread, self.preview_worker = run_simplifile_batch_preview(
            self.excel_file_path.text(),
            self.deeds_file_path.text(),
            self.mortgage_file_path.text(),
            self.affidavits_file_path.text(),
            county_id
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
        """Process and start the batch upload directly without confirmation dialog"""
        # Validate API configuration
        api_token = self.api_token.text()
        submitter_id = "SCTP3G"  # Hardcoded submitter ID
        recipient_id = self.recipient_combo.currentData()
        
        if not api_token or not recipient_id:
            QMessageBox.warning(self, "Missing API Configuration", 
                            "Please enter your API token and select a county.")
            return
        
        # Validate file selection
        if not self.excel_file_path.text():
            QMessageBox.warning(self, "Missing Excel File", "Please select an Excel file.")
            return
            
        if not self.deeds_file_path.text() and not self.mortgage_file_path.text():
            QMessageBox.warning(self, "Missing PDF Files", 
                            "Please select at least one PDF file (Deeds or Mortgage Satisfactions).")
            return
        
        # Get county configuration
        county_config = get_county_config(recipient_id)
        
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
        
        # Start batch processing directly (no preview mode - always upload)
        self.update_output(f"Starting batch upload to {county_config.COUNTY_NAME}...")
        self.progress_bar.setValue(5)
        self.batch_upload_btn.setEnabled(False)
        
        # Show processing indicator and disable buttons
        self.show_processing_indicator()
        self.batch_upload_btn.setEnabled(False)
        
        # Give UI time to update before starting the heavy work
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Get file paths
        excel_path = self.excel_file_path.text()
        deeds_path = self.deeds_file_path.text()
        mortgage_path = self.mortgage_file_path.text()
        affidavits_path = self.affidavits_file_path.text() if hasattr(self, 'affidavits_file_path') else None
        
        # Use the batch processor to run the operation (always in upload mode, not preview)
        self.batch_thread, self.batch_worker = run_simplifile_batch_process(
            excel_path,
            deeds_path,
            mortgage_path,
            api_token,
            submitter_id,
            recipient_id,
            False,  # preview_mode = False (always upload)
            affidavits_path
        )
        
        # Connect signals with QueuedConnection type to ensure they're processed correctly
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
        
        # Connect thread finished signal
        self.batch_thread.finished.connect(self.hide_processing_indicator)
        
        # Start thread
        self.batch_thread.start()
        
        # Process events again to ensure UI updates
        QApplication.processEvents()

    def show_processing_indicator(self):
        """Show a processing indicator without using status bar"""
        # Create a processing label in the UI itself instead of using status bar
        if not hasattr(self, 'processing_indicator_layout'):
            # Create a layout for the indicator if it doesn't exist
            self.processing_indicator_layout = QHBoxLayout()
            self.processing_label = QLabel("⏳ Processing...")
            self.processing_indicator_layout.addWidget(self.processing_label)
            
            # Add to the main layout, just above the output area
            main_layout = self.layout()
            main_layout.insertLayout(main_layout.count()-1, self.processing_indicator_layout)
        else:
            # If layout exists, just update and show the label
            self.processing_label.setText("⏳ Processing...")
            self.processing_label.setVisible(True)
        
        # We can also show a "busy" cursor for the application
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # Start a timer to animate the indicator
        self.processing_timer = QTimer()
        self.processing_timer.timeout.connect(self.update_processing_indicator)
        self.processing_timer.start(500)  # Update every 500ms

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
            self.processing_label.setVisible(False)
        
        # Restore normal cursor
        from PyQt6.QtWidgets import QApplication
        QApplication.restoreOverrideCursor()

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
        
        # Always produce final outcome statement
        self.update_output("\n📋 Final outcome:")
        if successful == total:
            self.update_output(f"  ✅ All {total} packages were processed successfully.")
        elif successful > 0:
            self.update_output(f"  ⚠️ {successful} of {total} packages were successful, {failed} failed.")
        else:
            self.update_output(f"  ❌ All {total} packages failed to process.")

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

    def save_api_settings(self):
        """Save API settings to config"""
        self.config["api_token"] = self.api_token.text()
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
        from PyQt6.QtWidgets import QApplication
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
        self.batch_upload_btn.setEnabled(True)