from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QComboBox
)
from PyQt6.QtCore import pyqtSignal

class WebAutomationUI(QWidget):
    start_automation = pyqtSignal(str, str, str, str, str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("Web Automation")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        # Excel file selection
        excel_layout = QHBoxLayout()
        self.excel_edit = QLineEdit()
        excel_button = QPushButton("Select Excel File")
        excel_button.clicked.connect(self.select_excel_file)
        excel_layout.addWidget(QLabel("Excel File:"))
        excel_layout.addWidget(self.excel_edit)
        excel_layout.addWidget(excel_button)
        layout.addLayout(excel_layout)

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

        # Add save location input
        save_location_layout = QHBoxLayout()
        self.save_location_edit = QLineEdit()
        save_location_button = QPushButton("Select Save Location")
        save_location_button.clicked.connect(self.select_save_location)
        save_location_layout.addWidget(QLabel("Save Location:"))
        save_location_layout.addWidget(self.save_location_edit)
        save_location_layout.addWidget(save_location_button)
        layout.addLayout(save_location_layout)

        # Start button
        self.start_button = QPushButton("Start Web Automation")
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

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

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
        if excel_path and username and password and save_location:
            self.start_automation.emit(excel_path, browser, username, password, save_location)
            self.start_button.setEnabled(False)
            self.status_label.setText("Automation in progress...")
            self.spinner.show()
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

    def show_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.spinner.hide()
        self.start_button.setEnabled(True)