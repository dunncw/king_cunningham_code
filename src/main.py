import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from ui.main_window import MainWindow
from document_processor.processor import process_files
from utils.updater import UpdateChecker, Updater, restart_with_updated_exe

__version__ = "0.0.2"

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
            process_files(
                self.input_path,
                self.output_dir,
                self.is_directory,
                self.progress_update.emit,
                self.output_update.emit
            )
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class MultiTaskApplication(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.main_window = None
        self.splash = None
        self.splash_timer = None
        self.update_checker = UpdateChecker(__version__)
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.no_update.connect(self.on_no_update)
        self.update_checker.error_occurred.connect(self.on_error)

    def run(self):
        self.setWindowIcon(QIcon(self.get_icon_path()))
        self.show_splash_screen()
        self.initialize_application()
        self.splash_timer = QTimer(self)
        self.splash_timer.timeout.connect(self.show_main_window)
        self.splash_timer.start(5000)

    def get_icon_path(self):
        return get_resource_path(os.path.join("resources", "app_icon.ico"))

    def show_splash_screen(self):
        splash_pixmap = QPixmap(get_resource_path(os.path.join("resources", "splash_image.png")))
        self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.splash.show()

    def initialize_application(self):
        self.main_window = MainWindow()
        self.main_window.check_for_updates.connect(self.check_for_updates)
        self.main_window.doc_processor.start_processing.connect(self.process_documents)
        self.main_window.setWindowIcon(self.windowIcon())

        steps = [
            "Loading engines...",
            "Initializing UI...",
            "Loading templates...",
            "Finalizing..."
        ]
        for i, message in enumerate(steps):
            progress = (i + 1) * 25
            self.splash.showMessage(
                f"<h3>{message}</h3>",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                Qt.GlobalColor.white
            )
            self.splash.show()
            self.processEvents()
            QTimer.singleShot(1000 * i, lambda m=message: self.update_splash(m))

    def update_splash(self, message):
        if self.splash:
            self.splash.showMessage(
                f"<h3>{message}</h3>",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                Qt.GlobalColor.white
            )

    def show_main_window(self):
        if self.splash:
            self.splash.finish(self.main_window)
        self.main_window.show()
        self.splash_timer.stop()

    def check_for_updates(self):
        self.main_window.update_check_status("Checking for updates...")
        self.update_checker.check_for_updates()

    def on_update_available(self, new_version, download_url):
        self.main_window.update_check_status(f"Update available: v{new_version}")
        if self.main_window.show_update_available(new_version):
            self.start_update(download_url)
        else:
            self.main_window.update_check_status("Update cancelled by user.")

    def on_no_update(self):
        self.main_window.show_no_update()

    def start_update(self, download_url):
        self.updater = Updater(download_url)
        self.updater.update_progress.connect(self.main_window.doc_processor.update_progress)
        self.updater.update_completed.connect(self.finish_update)
        self.updater.error_occurred.connect(self.on_error)
        self.updater.start()

    def finish_update(self, new_exe_path):
        reply = QMessageBox.question(
            self.main_window,
            "Update Complete",
            "The update has been downloaded. Do you want to restart the application now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            restart_with_updated_exe(new_exe_path)
        else:
            self.main_window.update_check_status("Update will be applied on next restart.")

    def on_error(self, error_message):
        self.main_window.update_check_status(f"Error: {error_message}")
        QMessageBox.critical(self.main_window, "Error", error_message)

    def process_documents(self, input_path, output_dir, is_directory):
        self.worker = OCRWorker(input_path, output_dir, is_directory)
        self.worker.progress_update.connect(self.main_window.doc_processor.update_progress)
        self.worker.output_update.connect(self.main_window.doc_processor.update_output)
        self.worker.finished.connect(self.main_window.doc_processor.processing_finished)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def handle_error(self, error_message):
        self.main_window.show_error(error_message)
        self.main_window.doc_processor.processing_finished()

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Error caught!")
    print("Error message:", exc_value)
    print("Error traceback:", tb)
    QMessageBox.critical(None, "Error", f"An unexpected error occurred:\n\n{tb}")

def main():
    sys.excepthook = excepthook
    app = MultiTaskApplication(sys.argv)
    app.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()