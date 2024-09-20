import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplashScreen
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
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

class OCRApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.main_window = None
        self.splash = None
        self.splash_timer = None

    def run(self):
        # Set the application icon
        self.setWindowIcon(QIcon(self.get_icon_path()))

        # Create and show splash screen
        self.show_splash_screen()

        # Start initialization process
        self.initialize_application()

        # Set timer to close splash screen after 5 seconds
        self.splash_timer = QTimer(self)
        self.splash_timer.timeout.connect(self.show_main_window)
        self.splash_timer.start(5000)  # 5000 milliseconds = 5 seconds

    def get_icon_path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "resources", "app_icon.ico"))

    def show_splash_screen(self):
        splash_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "splash_image.png"))
        self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.splash.show()

    def initialize_application(self):
        # Perform any initialization tasks here
        self.main_window = MainWindow()
        self.main_window.start_processing.connect(self.process_documents)
        self.main_window.setWindowIcon(self.windowIcon())

        # Update splash screen with progress messages
        steps = [
            "Loading OCR engine...",
            "Initializing UI...",
            "Loading document templates...",
            "Finalizing..."
        ]
        
        for i, message in enumerate(steps):
            progress = (i + 1) * 25  # 25, 50, 75, 100
            self.splash.showMessage(f"<h3>{message}</h3>", 
                                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, 
                                    Qt.GlobalColor.white)
            self.splash.show()
            self.processEvents()
            # Simulate work being done
            QTimer.singleShot(1000 * i, lambda m=message: self.update_splash(m))

    def update_splash(self, message):
        if self.splash:
            self.splash.showMessage(f"<h3>{message}</h3>", 
                                    Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, 
                                    Qt.GlobalColor.white)

    def show_main_window(self):
        if self.splash:
            self.splash.finish(self.main_window)
        self.main_window.show()
        self.splash_timer.stop()

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
    print("Error caught!")
    print("Error message: ", exc_value)
    print("Error traceback: ", tb)
    QMessageBox.critical(None, "Error", f"An unexpected error occurred:\n\n{tb}")

def main():
    sys.excepthook = excepthook
    app = OCRApplication(sys.argv)
    app.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()