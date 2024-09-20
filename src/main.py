import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal
from ui.main_window import MainWindow
from ocr.processor import process_files

class OCRWorker(QThread):
    progress_update = pyqtSignal(int)
    output_update = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, input_path, output_dir, is_directory):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.is_directory = is_directory

    def run(self):
        try:
            process_files(self.input_path, self.output_dir, self.is_directory, self.progress_update.emit, self.output_update.emit)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class OCRApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainWindow()
        self.setCentralWidget(self.ui)
        self.ui.start_processing.connect(self.process_documents)

        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "app_icon.ico")
        self.setWindowIcon(QIcon(icon_path))

    def process_documents(self, input_path, output_dir, is_directory):
        self.worker = OCRWorker(input_path, output_dir, is_directory)
        self.worker.progress_update.connect(self.ui.update_progress)
        self.worker.output_update.connect(self.ui.update_output)
        self.worker.finished.connect(self.ui.processing_finished)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def handle_error(self, error_message):
        self.ui.show_error(error_message)
        self.ui.processing_finished()  # This will hide the spinner

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message: ", exc_value)
    print("error traceback: ", tb)
    QMessageBox.critical(None, "Error", f"An unexpected error occurred:\n\n{tb}")

def main():
    sys.excepthook = excepthook
    app = QApplication(sys.argv)

    # Set application icon for the entire application (Windows taskbar, macOS dock)
    icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "app_icon.ico")
    app.setWindowIcon(QIcon(icon_path))

    window = OCRApplication()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()