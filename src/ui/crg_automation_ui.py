from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QComboBox, QFrame, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, QThread
from crg_automation.crg import CRGAutomationWorker

class CRGAutomationUI(QWidget):
    start_automation = pyqtSignal(str, str, str, str, str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.thread = None
        self.worker = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        title_label = QLabel("Court Records CRG")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)

        row = 0
        grid.addWidget(QLabel("Excel File:"), row, 0)
        self.excel_edit = QLineEdit()
        grid.addWidget(self.excel_edit, row, 1)
        excel_button = QPushButton("Browse")
        excel_button.setFixedWidth(80)
        excel_button.clicked.connect(self.select_excel_file)
        grid.addWidget(excel_button, row, 2)

        row += 1
        grid.addWidget(QLabel("Browser:"), row, 0)
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge"])
        grid.addWidget(self.browser_combo, row, 1, 1, 2)

        row += 1
        grid.addWidget(QLabel("Username:"), row, 0)
        self.username_edit = QLineEdit()
        grid.addWidget(self.username_edit, row, 1, 1, 2)

        row += 1
        grid.addWidget(QLabel("Password:"), row, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        grid.addWidget(self.password_edit, row, 1, 1, 2)

        row += 1
        grid.addWidget(QLabel("Save Location:"), row, 0)
        self.save_location_edit = QLineEdit()
        grid.addWidget(self.save_location_edit, row, 1)
        save_button = QPushButton("Browse")
        save_button.setFixedWidth(80)
        save_button.clicked.connect(self.select_save_location)
        grid.addWidget(save_button, row, 2)

        layout.addLayout(grid)

        self.start_button = QPushButton("Start Automation")
        self.start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_button)

        status_layout = QHBoxLayout()
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)

        self.spinner = QProgressBar()
        self.spinner.setRange(0, 0)
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

        self.warning_frame = QFrame()
        self.warning_frame.setStyleSheet("background-color: #332b1a; border: 1px solid #4a3f2a; border-radius: 6px;")
        warning_layout = QVBoxLayout(self.warning_frame)
        warning_label = QLabel("WARNING: Do not switch windows or use the keyboard until automation is complete. The output folder should be empty.")
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #d4a854; font-weight: bold;")
        warning_layout.addWidget(warning_label)
        self.warning_frame.hide()
        layout.addWidget(self.warning_frame)

        self.save_button = QPushButton("Save Output")
        self.save_button.clicked.connect(self.save_output)
        layout.addWidget(self.save_button)

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
        browser = self.browser_combo.currentText()
        username = self.username_edit.text()
        password = self.password_edit.text()
        save_location = self.save_location_edit.text()
        if excel_path and username and password and save_location:
            window = self.window()
            if hasattr(window, 'tile_left'):
                window.tile_left()

            self.start_button.setEnabled(False)
            self.status_label.setText("Automation in progress...")
            self.spinner.show()
            self.warning_frame.show()

            self.thread = QThread()
            self.worker = CRGAutomationWorker(excel_path, browser, username, password, save_location)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.worker.progress.connect(self.update_progress)
            self.worker.status.connect(self.update_output)
            self.worker.error.connect(self.show_error)
            self.thread.finished.connect(self.automation_finished)

            self.thread.start()
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
