# File: ui/scra_automation_ui.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QProgressBar, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, QThread
from scra_automation.scra_multi_request_formatter import SCRAMultiRequestFormatter
import os

class SCRAAutomationUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.thread = None
        self.worker = None

    def init_ui(self):
        layout = QVBoxLayout()

        # Title
        title_label = QLabel("SCRA File Formatter")
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

        # Output location selection
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        output_button = QPushButton("Select Output Location")
        output_button.clicked.connect(self.select_output_location)
        output_layout.addWidget(QLabel("Output Location:"))
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        # Process button
        self.process_button = QPushButton("Format SCRA File")
        self.process_button.clicked.connect(self.on_process_clicked)
        layout.addWidget(self.process_button)

        # Status label
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Output display
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.setLayout(layout)

    def select_excel_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls *.xlsm)"
        )
        if file_path:
            self.excel_edit.setText(file_path)
            self.output_text.append(f"Selected input file: {file_path}")
    
    def select_output_location(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Formatted File", "", "Text Files (*.txt)"
        )
        if file_path:
            # Ensure the file has .txt extension
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            self.output_edit.setText(file_path)
            self.output_text.append(f"Selected output location: {file_path}")

    def on_process_clicked(self):
        excel_path = self.excel_edit.text()
        output_path = self.output_edit.text()
        
        if not excel_path or not output_path:
            self.status_label.setText("Please provide both input and output file locations.")
            return

        if not os.path.exists(excel_path):
            self.status_label.setText("Input Excel file does not exist.")
            return

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.process_button.setEnabled(False)
        self.status_label.setText("Processing SCRA file format...")
        self.progress_bar.setValue(0)
        
        # Create worker and thread
        self.thread = QThread()
        self.worker = SCRAFormatWorker(excel_path, output_path)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.update_progress)
        self.worker.message.connect(self.update_output)
        self.worker.error.connect(self.show_error)
        self.thread.finished.connect(self.processing_finished)
        
        # Start the thread
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

    def processing_finished(self):
        self.process_button.setEnabled(True)
        self.status_label.setText("SCRA file formatting complete!")
        self.progress_bar.setValue(100)

    def show_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.output_text.append(f"Error: {error_message}")
        self.process_button.setEnabled(True)

class SCRAFormatWorker(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, excel_path, output_path):
        super().__init__()
        self.excel_path = excel_path
        self.output_path = output_path

    def run(self):
        try:
            self.message.emit("Starting SCRA file formatting...")
            self.progress.emit(20)

            # Create formatter instance
            formatter = SCRAMultiRequestFormatter(self.excel_path, self.output_path)
            
            # Process the Excel file
            self.progress.emit(50)
            success, message = formatter.process_excel()

            if success:
                self.message.emit("File processing completed successfully")
                self.message.emit(f"Output file created at: {self.output_path}")
                self.progress.emit(100)
            else:
                self.error.emit(message)
                
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()