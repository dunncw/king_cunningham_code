from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QProgressBar, QComboBox, QCheckBox, QFrame
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WebAutomationUI(QWidget):
    start_automation = pyqtSignal(str, str, str, str, str, str, bool)  # Document stacking parameter

    def __init__(self):
        super().__init__()
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_current_selection)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)

        # Title
        title_label = QLabel("PT-61 Form Automation")
        title_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Core Inputs Section
        inputs_frame = QFrame()
        inputs_layout = QVBoxLayout(inputs_frame)
        inputs_layout.setSpacing(15)

        # Row 1: Version selection and Excel validation
        version_row = QHBoxLayout()
        version_row.addWidget(QLabel("Version:"))
        
        self.version_combo = QComboBox()
        self.version_combo.setMinimumWidth(150)
        
        # Load version names from config
        try:
            from web_automation.pt61_config import get_all_version_display_names
            version_names = get_all_version_display_names()
            self.version_combo.addItems(version_names)
        except ImportError as e:
            # Fallback if import fails
            self.version_combo.addItems([
                "PT-61 New Batch",
                "PT-61 Deedbacks", 
                "PT61 Foreclosures"
            ])
            print(f"Warning: Could not import PT61 config, using fallback: {e}")
        
        self.version_combo.currentTextChanged.connect(self.on_version_changed)
        version_row.addWidget(self.version_combo)
        
        # Excel validation status (simple icon)
        self.excel_status_label = QLabel("Select Excel File")
        self.excel_status_label.setStyleSheet("color: #666; font-style: italic;")
        version_row.addStretch()
        version_row.addWidget(self.excel_status_label)
        
        inputs_layout.addLayout(version_row)

        # Row 2: Excel file selection
        excel_row = QHBoxLayout()
        excel_row.addWidget(QLabel("Excel File:"))
        
        self.excel_edit = QLineEdit()
        self.excel_edit.textChanged.connect(self.on_excel_path_changed)
        self.excel_edit.setPlaceholderText("Select your Excel file...")
        excel_row.addWidget(self.excel_edit)
        
        excel_button = QPushButton("Browse")
        excel_button.clicked.connect(self.select_excel_file)
        excel_row.addWidget(excel_button)
        
        inputs_layout.addLayout(excel_row)

        # Row 3: Browser, Username, Password in one row
        creds_row = QHBoxLayout()
        
        creds_row.addWidget(QLabel("Browser:"))
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge"])
        self.browser_combo.setMaximumWidth(100)
        creds_row.addWidget(self.browser_combo)
        
        creds_row.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        creds_row.addWidget(self.username_edit)
        
        creds_row.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Password")
        creds_row.addWidget(self.password_edit)
        
        inputs_layout.addLayout(creds_row)

        # Row 4: Save location and document stacking
        output_row = QHBoxLayout()
        
        output_row.addWidget(QLabel("Save Location:"))
        self.save_location_edit = QLineEdit()
        self.save_location_edit.setPlaceholderText("Output folder...")
        output_row.addWidget(self.save_location_edit)
        
        save_location_button = QPushButton("📁")
        save_location_button.setMaximumWidth(40)
        save_location_button.clicked.connect(self.select_save_location)
        output_row.addWidget(save_location_button)
        
        # Document stacking checkbox
        self.document_stacking_checkbox = QCheckBox("Stack Documents")
        self.document_stacking_checkbox.setToolTip("Combine all PDFs into one document")
        output_row.addWidget(self.document_stacking_checkbox)
        
        inputs_layout.addLayout(output_row)
        
        layout.addWidget(inputs_frame)

        # Action Section - Start Button (prominent)
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.start_button = QPushButton("▶ Start PT-61 Automation")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.on_start_clicked)
        
        # Make button prominent
        button_font = QFont("Segoe UI", 12, QFont.Weight.Bold)
        self.start_button.setFont(button_font)
        self.start_button.setMinimumHeight(50)
        self.start_button.setMinimumWidth(250)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        
        action_layout.addWidget(self.start_button)
        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Progress Section (hidden by default)
        self.progress_frame = QFrame()
        self.progress_frame.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_frame)
        
        # Status line
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = QFont("Segoe UI", 10)
        self.status_label.setFont(status_font)
        progress_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(20)
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_frame)

        # Results Section (hidden by default)  
        self.results_frame = QFrame()
        self.results_frame.setVisible(False)
        results_layout = QVBoxLayout(self.results_frame)
        
        self.results_label = QLabel()
        self.results_label.setWordWrap(True)
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_font = QFont("Segoe UI", 11)
        self.results_label.setFont(results_font)
        results_layout.addWidget(self.results_label)
        
        layout.addWidget(self.results_frame)

        # Error Section (hidden by default)
        self.error_frame = QFrame()
        self.error_frame.setVisible(False)
        self.error_frame.setStyleSheet("background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; padding: 10px;")
        error_layout = QVBoxLayout(self.error_frame)
        
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #721c24; font-weight: bold;")
        error_layout.addWidget(self.error_label)
        
        layout.addWidget(self.error_frame)

        # Add some space at bottom
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Initialize version info
        self.on_version_changed()

    def on_version_changed(self):
        """Handle version selection change"""
        try:
            from web_automation.pt61_config import get_version_config, is_valid_version_name, get_default_document_stacking
            
            version_name = self.version_combo.currentText()
            
            # Validate version name exists in config
            if not is_valid_version_name(version_name):
                return
            
            # Set document stacking checkbox based on version default
            default_stacking = get_default_document_stacking(version_name)
            self.document_stacking_checkbox.setChecked(default_stacking)
            
            # Trigger validation if Excel file is selected
            if self.excel_edit.text():
                self.validation_timer.start(300)  # Quick validation
                
        except Exception as e:
            print(f"Error loading version info: {str(e)}")

    def on_excel_path_changed(self):
        """Handle Excel file path change"""
        if self.excel_edit.text():
            self.validation_timer.start(300)  # Quick validation
        else:
            self.excel_status_label.setText("Select Excel File")
            self.excel_status_label.setStyleSheet("color: #666; font-style: italic;")
            self.start_button.setEnabled(False)

    def validate_current_selection(self):
        """Validate current Excel file against selected version"""
        excel_path = self.excel_edit.text()
        version_name = self.version_combo.currentText()
        
        if not excel_path:
            self.excel_status_label.setText("Select Excel File")
            self.excel_status_label.setStyleSheet("color: #666; font-style: italic;")
            self.start_button.setEnabled(False)
            return
        
        try:
            from web_automation.version_validator import validate_excel_for_version
            from web_automation.pt61_config import is_valid_version_name
            
            # Validate version name first
            if not is_valid_version_name(version_name):
                self.excel_status_label.setText("❌ Invalid Version")
                self.excel_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.start_button.setEnabled(False)
                return
            
            result = validate_excel_for_version(excel_path, version_name)
            
            if result.is_valid:
                self.excel_status_label.setText("✅ Excel Valid")
                self.excel_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.start_button.setEnabled(True)
            else:
                # Show first error only
                first_error = result.errors[0] if result.errors else "Validation failed"
                self.excel_status_label.setText(f"❌ {first_error}")
                self.excel_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.start_button.setEnabled(False)
                
        except Exception as e:
            self.excel_status_label.setText("❌ Validation Error")
            self.excel_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            self.start_button.setEnabled(False)

    def select_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_edit.setText(file_path)
    
    def select_save_location(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder_path:
            self.save_location_edit.setText(folder_path)

    def on_start_clicked(self):
        excel_path = self.excel_edit.text()
        browser = self.browser_combo.currentText()
        username = self.username_edit.text()
        password = self.password_edit.text()
        save_location = self.save_location_edit.text()
        version = self.version_combo.currentText()
        document_stacking = self.document_stacking_checkbox.isChecked()
        
        if excel_path and username and password and save_location:
            # Hide results/error sections
            self.results_frame.setVisible(False)
            self.error_frame.setVisible(False)
            
            # Show progress section
            self.progress_frame.setVisible(True)
            self.status_label.setText("Starting automation...")
            self.progress_bar.setValue(0)
            
            # Disable inputs
            self.start_button.setEnabled(False)
            self.start_button.setText("⏸ Running...")
            
            # Emit signal
            self.start_automation.emit(excel_path, browser, username, password, save_location, version, document_stacking)
        else:
            # Show what's missing
            missing = []
            if not excel_path: missing.append("Excel file")
            if not username: missing.append("Username") 
            if not password: missing.append("Password")
            if not save_location: missing.append("Save location")
            
            self.show_error(f"Please provide: {', '.join(missing)}")

    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)

    def update_status(self, text):
        """Update status line"""
        self.status_label.setText(text)

    def automation_finished(self):
        """Called when automation completes successfully"""
        # Hide progress
        self.progress_frame.setVisible(False)
        
        # Show results
        self.results_frame.setVisible(True)
        
        # Count files and show summary
        save_location = self.save_location_edit.text()
        if os.path.exists(save_location):
            pdf_files = [f for f in os.listdir(save_location) if f.endswith('.pdf')]
            individual_pdfs = [f for f in pdf_files if not f.startswith('PT61_')]
            combined_pdfs = [f for f in pdf_files if f.startswith('PT61_')]
            
            result_text = f"✅ Completed: {len(individual_pdfs)} PDFs saved"
            if combined_pdfs:
                result_text += f"\n📄 Combined PDF: {combined_pdfs[0]}"
        else:
            result_text = "✅ Automation completed successfully"
        
        self.results_label.setText(result_text)
        self.results_label.setStyleSheet("color: #27ae60;")
        
        # Reset button
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Start PT-61 Automation")

    def show_error(self, error_message):
        """Show error message"""
        # Hide progress and results
        self.progress_frame.setVisible(False)
        self.results_frame.setVisible(False)
        
        # Show error
        self.error_frame.setVisible(True)
        self.error_label.setText(f"❌ Error: {error_message}")
        
        # Reset button
        self.start_button.setEnabled(True)
        self.start_button.setText("▶ Start PT-61 Automation")