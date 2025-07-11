from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QComboBox, QFrame, QScrollArea,
    QCheckBox
)
from PyQt6.QtCore import pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import sys
import os

# Add the parent directory to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class WebAutomationUI(QWidget):
    start_automation = pyqtSignal(str, str, str, str, str, str, bool)  # Added document_stacking parameter

    def __init__(self):
        super().__init__()
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self.validate_current_selection)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("PT-61 Form Automation")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Version selection - Using config as single source of truth
        version_layout = QHBoxLayout()
        self.version_combo = QComboBox()
        
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
        version_layout.addWidget(QLabel("Version:"))
        version_layout.addWidget(self.version_combo)
        layout.addLayout(version_layout)

        # Version info panel - Two column layout
        self.version_info_frame = QFrame()
        self.version_info_layout = QVBoxLayout(self.version_info_frame)
        
        self.version_description = QLabel()
        self.version_description.setWordWrap(True)
        self.version_info_layout.addWidget(self.version_description)
        
        # Two column layout for requirements and constants
        columns_layout = QHBoxLayout()
        
        # Left column - Excel Requirements
        excel_column = QWidget()
        excel_layout = QVBoxLayout(excel_column)
        
        self.required_columns_label = QLabel("Required Excel Columns:")
        self.required_columns_label.setFont(QFont("", 9, QFont.Weight.Bold))
        excel_layout.addWidget(self.required_columns_label)
        
        # Scrollable area for required columns
        excel_scroll = QScrollArea()
        excel_scroll.setMaximumHeight(200)
        excel_scroll.setWidgetResizable(True)
        
        self.required_columns_list = QLabel()
        self.required_columns_list.setWordWrap(True)
        excel_scroll.setWidget(self.required_columns_list)
        excel_layout.addWidget(excel_scroll)
        
        # Right column - Constants
        constants_column = QWidget()
        constants_layout = QVBoxLayout(constants_column)
        
        self.constants_label = QLabel("Version Constants:")
        self.constants_label.setFont(QFont("", 9, QFont.Weight.Bold))
        constants_layout.addWidget(self.constants_label)
        
        # Scrollable area for constants
        constants_scroll = QScrollArea()
        constants_scroll.setMaximumHeight(200)
        constants_scroll.setWidgetResizable(True)
        
        self.constants_display = QLabel()
        self.constants_display.setWordWrap(True)
        self.constants_display.setFont(QFont("Courier", 8))  # Monospace for JSON
        constants_scroll.setWidget(self.constants_display)
        constants_layout.addWidget(constants_scroll)
        
        # Add columns to layout
        columns_layout.addWidget(excel_column)
        columns_layout.addWidget(constants_column)
        
        self.version_info_layout.addLayout(columns_layout)
        layout.addWidget(self.version_info_frame)

        # Excel file selection
        excel_layout = QHBoxLayout()
        self.excel_edit = QLineEdit()
        self.excel_edit.textChanged.connect(self.on_excel_path_changed)
        excel_button = QPushButton("Select Excel File")
        excel_button.clicked.connect(self.select_excel_file)
        excel_layout.addWidget(QLabel("Excel File:"))
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(excel_button)
        layout.addLayout(excel_layout)

        # Validation status
        self.validation_frame = QFrame()
        self.validation_frame.setVisible(False)
        self.validation_layout = QVBoxLayout(self.validation_frame)
        
        self.validation_status = QLabel()
        self.validation_status.setFont(QFont("", 9, QFont.Weight.Bold))
        self.validation_layout.addWidget(self.validation_status)
        
        # Scrollable area for validation details
        scroll_area = QScrollArea()
        scroll_area.setMaximumHeight(150)
        scroll_area.setWidgetResizable(True)
        
        self.validation_details = QLabel()
        self.validation_details.setWordWrap(True)
        scroll_area.setWidget(self.validation_details)
        self.validation_layout.addWidget(scroll_area)
        
        layout.addWidget(self.validation_frame)

        # Browser selection
        browser_layout = QHBoxLayout()
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge"])
        browser_layout.addWidget(QLabel("Select Browser:"))
        browser_layout.addWidget(self.browser_combo)
        layout.addLayout(browser_layout)

        # Username input
        username_layout = QHBoxLayout()
        self.username_edit = QLineEdit()
        username_layout.addWidget(QLabel("Username:"))
        username_layout.addWidget(self.username_edit)
        layout.addLayout(username_layout)

        # Password input
        password_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(QLabel("Password:"))
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)

        # Save location input
        save_location_layout = QHBoxLayout()
        self.save_location_edit = QLineEdit()
        save_location_button = QPushButton("Select Save Location")
        save_location_button.clicked.connect(self.select_save_location)
        save_location_layout.addWidget(QLabel("Save Location:"))
        save_location_layout.addWidget(self.save_location_edit)
        save_location_layout.addWidget(save_location_button)
        layout.addLayout(save_location_layout)

        # NEW: Output Options section
        output_options_layout = QHBoxLayout()
        output_options_label = QLabel("Output Options:")
        self.document_stacking_checkbox = QCheckBox("Document Stacking")
        self.document_stacking_checkbox.setToolTip("Combine all PDFs into one document after processing")
        
        output_options_layout.addWidget(output_options_label)
        output_options_layout.addWidget(self.document_stacking_checkbox)
        output_options_layout.addStretch()  # Push everything to the left
        layout.addLayout(output_options_layout)

        # Start button
        self.start_button = QPushButton("Start PT-61 Automation")
        self.start_button.clicked.connect(self.on_start_clicked)
        self.start_button.setEnabled(False)  # Disabled until validation passes
        layout.addWidget(self.start_button)

        # Status and progress
        status_layout = QHBoxLayout()
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)

        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)  # Indeterminate mode
        self.spinner.setTextVisible(False)
        self.spinner.hide()
        status_layout.addWidget(self.spinner)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Add warning message
        self.warning_frame = QFrame()
        self.warning_frame.setStyleSheet("background-color: #FFF3CD; border: 1px solid #FFEEBA; border-radius: 4px;")
        warning_layout = QVBoxLayout(self.warning_frame)
        warning_label = QLabel("WARNING: Do not switch windows or use the keyboard until automation is complete. Doing so may interfere with the process. Note folder your writing output to should be empty! Click X to stop automation")
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #856404; font-weight: bold;")
        warning_layout.addWidget(warning_label)
        self.warning_frame.hide()  # Initially hidden
        layout.addWidget(self.warning_frame)

        # Add Save Output button
        self.save_button = QPushButton("Save Output")
        self.save_button.clicked.connect(self.save_output)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        
        # Initialize version info
        self.on_version_changed()

    def on_version_changed(self):
        """Handle version selection change"""
        try:
            from web_automation.pt61_config import get_version_config, is_valid_version_name, get_default_document_stacking
            import json
            
            version_name = self.version_combo.currentText()
            
            # Validate version name exists in config
            if not is_valid_version_name(version_name):
                self.version_description.setText(f"Error: Unknown version '{version_name}'")
                return
            
            _, config = get_version_config(version_name)
            
            # Update version description
            description = config.get("description", "No description available")
            self.version_description.setText(f"Description: {description}")
            
            # Update required columns list
            required_cols = config["required_columns"]
            cols_text = "• " + "\n• ".join(required_cols)
            self.required_columns_list.setText(cols_text)
            
            # Update constants display with formatted JSON
            constants = config.get("constants", {})
            try:
                constants_json = json.dumps(constants, indent=2)
                self.constants_display.setText(constants_json)
            except Exception as e:
                self.constants_display.setText(f"Error formatting constants: {str(e)}")
            
            # NEW: Set document stacking checkbox based on version default
            default_stacking = get_default_document_stacking(version_name)
            self.document_stacking_checkbox.setChecked(default_stacking)
            
            # Trigger validation if Excel file is selected
            if self.excel_edit.text():
                self.validation_timer.start(500)  # Delay to avoid too frequent validation
                
        except Exception as e:
            self.version_description.setText(f"Error loading version info: {str(e)}")
            self.constants_display.setText("Error loading constants")

    def on_excel_path_changed(self):
        """Handle Excel file path change"""
        if self.excel_edit.text():
            self.validation_timer.start(500)  # Delay validation by 500ms
        else:
            self.validation_frame.setVisible(False)
            self.start_button.setEnabled(False)

    def validate_current_selection(self):
        """Validate current Excel file against selected version"""
        excel_path = self.excel_edit.text()
        version_name = self.version_combo.currentText()
        
        if not excel_path:
            self.validation_frame.setVisible(False)
            self.start_button.setEnabled(False)
            return
        
        try:
            from web_automation.version_validator import validate_excel_for_version
            from web_automation.pt61_config import is_valid_version_name
            
            # Validate version name first
            if not is_valid_version_name(version_name):
                self.validation_status.setText(f"❌ Invalid version: {version_name}")
                self.validation_details.setText("Please select a valid version from the dropdown.")
                self.start_button.setEnabled(False)
                return
            
            result = validate_excel_for_version(excel_path, version_name)
            
            # Show validation frame
            self.validation_frame.setVisible(True)
            
            if result.is_valid:
                self.validation_status.setText("✅ Excel file is valid for this version")
                self.start_button.setEnabled(True)
            else:
                self.validation_status.setText("❌ Excel file validation failed")
                self.start_button.setEnabled(False)
            
            # Show detailed validation info
            details = []
            
            if result.errors:
                details.append("ERRORS:")
                for error in result.errors:
                    details.append(f"  • {error}")
                details.append("")
            
            if result.warnings:
                details.append("WARNINGS:")
                for warning in result.warnings:
                    details.append(f"  • {warning}")
            
            self.validation_details.setText("\n".join(details))
            
        except Exception as e:
            self.validation_status.setText(f"❌ Validation error: {str(e)}")
            self.validation_details.setText("")
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
        document_stacking = self.document_stacking_checkbox.isChecked()  # NEW: Get checkbox state
        
        if excel_path and username and password and save_location:
            self.start_automation.emit(excel_path, browser, username, password, save_location, version, document_stacking)
            self.start_button.setEnabled(False)
            self.status_label.setText("Automation in progress...")
            self.spinner.show()
            self.warning_frame.show()
        else:
            self.status_label.setText("Please provide all required information.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

    def automation_finished(self):
        self.start_button.setEnabled(True)
        self.status_label.setText("Automation complete!")
        self.spinner.hide()
        self.warning_frame.hide()

    def show_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.spinner.hide()
        self.start_button.setEnabled(True)
        self.warning_frame.hide()

    def save_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output", "", "Text Files (*.txt)"
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.output_text.toPlainText())
            self.status_label.setText(f"Output saved to {file_path}")