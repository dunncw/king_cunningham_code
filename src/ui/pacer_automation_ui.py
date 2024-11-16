# File: ui/pacer_automation_ui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QFrame, QToolTip, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QThread, Qt
from PyQt6.QtGui import QIcon
from pacer.pacer import PACERAutomationWorker

class InfoLabel(QLabel):
    """Custom label with info icon and tooltip"""
    def __init__(self, text: str, tooltip: str, parent=None):
        super().__init__(text, parent)
        self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)

class PACERAutomationUI(QWidget):
    start_automation = pyqtSignal(str, str, str, str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.thread = None
        self.worker = None

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("PACER Automation")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Excel file selection
        excel_layout = QHBoxLayout()
        excel_label = InfoLabel(
            "Excel File:", 
            "Select an Excel file (.xlsx) with the following required columns:\n"
            "- Account #\n"
            "- Last Name 1\n"
            "- SSN 1\n"
            "- Last Name 2 (optional)\n"
            "- SSN 2 (optional)\n"
            "\nThe automation will process all rows that have valid SSNs "
            "and haven't been processed yet."
        )
        self.excel_edit = QLineEdit()
        excel_button = QPushButton("Select Excel File")
        excel_button.clicked.connect(self.select_excel_file)
        excel_layout.addWidget(excel_label)
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(excel_button)
        layout.addLayout(excel_layout)

        # PACER credentials
        credentials_frame = QFrame()
        credentials_layout = QVBoxLayout(credentials_frame)
        
        # Username input
        username_layout = QHBoxLayout()
        username_label = InfoLabel(
            "PACER Username:",
            "Enter your PACER account username.\n"
            "This account will be billed for the searches.\n"
            "Each search costs $0.10."
        )
        self.username_edit = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_edit)
        credentials_layout.addLayout(username_layout)

        # Password input
        password_layout = QHBoxLayout()
        password_label = InfoLabel(
            "PACER Password:",
            "Enter your PACER account password"
        )
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_edit)
        credentials_layout.addLayout(password_layout)

        layout.addWidget(credentials_frame)

        # Save location input
        save_location_layout = QHBoxLayout()
        save_location_label = InfoLabel(
            "Save Location:",
            "Select a folder where the API response data will be saved.\n"
            "A single JSON file containing all search results will be created\n"
            "with a timestamp in the filename."
        )
        self.save_location_edit = QLineEdit()
        save_location_button = QPushButton("Select Save Location")
        save_location_button.clicked.connect(self.select_save_location)
        save_location_layout.addWidget(save_location_label)
        save_location_layout.addWidget(self.save_location_edit)
        save_location_layout.addWidget(save_location_button)
        layout.addLayout(save_location_layout)

        # Start button
        self.start_button = QPushButton("Start PACER Automation")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.on_start_clicked)
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

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Output text area
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Warning message
        self.warning_frame = QFrame()
        warning_layout = QVBoxLayout(self.warning_frame)
        warning_label = QLabel(
            "NOTICE: PACER automation in progress. Each SSN search will incur "
            "a $0.10 charge to your PACER account."
        )
        warning_label.setWordWrap(True)
        warning_layout.addWidget(warning_label)
        self.warning_frame.hide()
        layout.addWidget(self.warning_frame)

        self.setLayout(layout)

    def select_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls *.xlsm)"
        )
        if file_path:
            self.excel_edit.setText(file_path)
    
    def select_save_location(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder_path:
            self.save_location_edit.setText(folder_path)

    def on_start_clicked(self):
        excel_path = self.excel_edit.text()
        username = self.username_edit.text()
        password = self.password_edit.text()
        save_location = self.save_location_edit.text()
        
        if excel_path and username and password and save_location:
            # Check if there's existing output and warn user
            if self.output_text.toPlainText():
                reply = QMessageBox.warning(
                    self,
                    "Confirm Restart",
                    "Starting a new automation will:\n\n"
                    "1. Overwrite existing results in the Excel file\n"
                    "2. Create a new API response file in the save location\n"
                    "3. Incur new PACER charges ($0.10 per SSN search)\n\n"
                    "Do you want to continue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.No:
                    return
            
            self.start_button.setEnabled(False)
            self.status_label.setText("PACER Automation in progress...")
            self.spinner.show()
            self.warning_frame.show()
            self.output_text.clear()  # Clear previous output
            
            # Create worker and thread
            self.thread = QThread()
            self.worker = PACERAutomationWorker(
                excel_path=excel_path,
                username=username,
                password=password,
                save_location=save_location
            )
            self.worker.moveToThread(self.thread)
            
            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.update_progress)
            self.worker.status.connect(self.update_output)
            self.worker.error.connect(self.show_error)
            self.thread.finished.connect(self.automation_finished)
            
            # Start the thread
            self.thread.start()
        else:
            self.status_label.setText("Please provide all required information.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        """Update output with color highlighting for open bankruptcies"""
        if "OPEN Bankruptcy Found" in text:
            # Create HTML formatted text with red background and white text
            formatted_text = f'<div style="background-color: #ff0000; color: white; padding: 2px;">{text}</div>'
            self.output_text.append(formatted_text)
        else:
            self.output_text.append(text)

    def automation_finished(self):
        self.start_button.setEnabled(True)
        self.status_label.setText("PACER Automation complete!")
        self.spinner.hide()
        self.warning_frame.hide()

    def show_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.spinner.hide()
        self.start_button.setEnabled(True)
        self.warning_frame.hide()