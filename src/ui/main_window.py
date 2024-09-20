# main_window.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QProgressBar, QTextEdit, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QMovie

class MainWindow(QWidget):
    start_processing = pyqtSignal(str, str, bool)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Processing type selection
        processing_type_layout = QVBoxLayout()
        processing_type_layout.addWidget(QLabel("Select processing type:"))
        self.input_type_group = QButtonGroup(self)
        self.file_radio = QRadioButton("Single File Processing")
        self.directory_radio = QRadioButton("Batch Processing (Directory)")
        self.directory_radio.setChecked(True)  # Default to batch processing
        self.input_type_group.addButton(self.file_radio)
        self.input_type_group.addButton(self.directory_radio)
        processing_type_layout.addWidget(self.file_radio)
        processing_type_layout.addWidget(self.directory_radio)
        layout.addLayout(processing_type_layout)

        # Input selection
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_button = QPushButton("Select Input")
        self.input_button.clicked.connect(self.select_input)
        input_layout.addWidget(QLabel("Input:"))
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_button)
        layout.addLayout(input_layout)

        # Output selection
        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        output_button = QPushButton("Select Output Directory")
        output_button.clicked.connect(self.select_output_dir)
        output_layout.addWidget(QLabel("Output Directory:"))
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(output_button)
        layout.addLayout(output_layout)

        self.process_button = QPushButton("Process Documents")
        self.process_button.clicked.connect(self.on_process_clicked)
        layout.addWidget(self.process_button)

        # Status layout with label and spinner
        status_layout = QHBoxLayout()
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)
        
        self.spinner_label = QLabel()
        self.spinner_movie = QMovie("resources/spinner.gif")
        self.spinner_size = 20
        self.spinner_movie.setScaledSize(QSize(self.spinner_size, self.spinner_size))
        self.spinner_label.setMovie(self.spinner_movie)
        self.spinner_label.hide()
        status_layout.addWidget(self.spinner_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Add save button
        self.save_button = QPushButton("Save Output")
        self.save_button.clicked.connect(self.save_output)
        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.setWindowTitle("Document Processor")

        # Connect radio buttons to update input button text
        self.file_radio.toggled.connect(self.update_input_button_text)
        self.directory_radio.toggled.connect(self.update_input_button_text)

    def update_input_button_text(self):
        if self.file_radio.isChecked():
            self.input_button.setText("Select File")
        else:
            self.input_button.setText("Select Directory")

    def select_input(self):
        if self.file_radio.isChecked():
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Input File", "", "PDF Files (*.pdf)"
            )
            if file_path:
                self.input_edit.setText(file_path)
        else:
            dir_path = QFileDialog.getExistingDirectory(self, "Select Input Directory")
            if dir_path:
                self.input_edit.setText(dir_path)

    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def on_process_clicked(self):
        input_path = self.input_edit.text()
        output_dir = self.output_dir_edit.text()
        is_directory = self.directory_radio.isChecked()
        if input_path and output_dir:
            self.start_processing.emit(input_path, output_dir, is_directory)
            self.process_button.setEnabled(False)
            self.status_label.setText("Processing...")
            self.spinner_label.show()
            self.spinner_movie.start()
        else:
            self.status_label.setText("Please select input and output paths.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_output(self, text):
        self.output_text.append(text)

    def processing_finished(self):
        self.process_button.setEnabled(True)
        self.status_label.setText("Processing complete!")
        self.spinner_movie.stop()
        self.spinner_label.hide()

    def show_error(self, error_message):
        self.spinner_movie.stop()
        self.spinner_label.hide()
        QMessageBox.critical(self, "Error", error_message)

    def save_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output", "", "Text Files (*.txt)"
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.output_text.toPlainText())
            QMessageBox.information(self, "Save Successful", f"Output saved to {file_path}")
