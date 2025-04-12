# File: src/main.py

import sys
import os
import traceback
from selenium.webdriver.chrome.options import Options as ChromeOptions
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import QTimer, Qt, QSize, QRect
from ui.main_window import MainWindow
from utils.updater import UpdateChecker

__version__ = "0.0.5"

# TODO: need to build updater application to push updates so users only have to downlaod the app once https://www.pyupdater.org/ 

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CustomSplashScreen(QSplashScreen):
    def __init__(self, pixmap):
        # Create a transparent pixmap of the original size
        self.original_pixmap = pixmap
        
        # Create a larger background to accommodate the message below the logo
        extra_height = 60  # Extra space for message
        self.background_pixmap = QPixmap(pixmap.width(), pixmap.height() + extra_height)
        self.background_pixmap.fill(Qt.GlobalColor.transparent)
        
        # Initialize with transparent pixmap
        super().__init__(self.background_pixmap)
        
        # Store message for drawing
        self.message = ""
        
    def drawContents(self, painter):
        # Draw black background for the entire area
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # Draw the original logo pixmap at the top
        painter.drawPixmap(
            (self.width() - self.original_pixmap.width()) // 2,
            10,  # Adjust top position as needed
            self.original_pixmap
        )
        
        # Draw message if present - positioned below the logo
        if self.message:
            painter.setPen(Qt.GlobalColor.white)
            font = QFont("Segoe UI", 12)
            font.setBold(True)
            painter.setFont(font)
            
            # Position text below the image
            text_y = 20 + self.original_pixmap.height()
            
            painter.drawText(
                QRect(0, text_y, self.width(), 30),
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
                self.message
            )
    
    def showMessage(self, message, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, color=Qt.GlobalColor.white):
        self.message = message
        self.repaint()

class KingCunninghamApp(QApplication):
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
        # Load the original splash image
        splash_image_path = get_resource_path(os.path.join("resources", "splash_image.png"))
        original_pixmap = QPixmap(splash_image_path)
        
        # Create the custom splash screen with original size plus padding for black background
        self.splash = CustomSplashScreen(original_pixmap)
        
        # Center on screen
        screen_geometry = self.primaryScreen().geometry()
        splash_geometry = self.splash.geometry()
        self.splash.move(
            (screen_geometry.width() - splash_geometry.width()) // 2,
            (screen_geometry.height() - splash_geometry.height()) // 2
        )
        
        self.splash.show()

    def initialize_application(self):
        self.main_window = MainWindow(__version__)
        self.main_window.check_for_updates.connect(self.check_for_updates)
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
                message,
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                Qt.GlobalColor.white
            )
            self.splash.show()
            self.processEvents()
            QTimer.singleShot(1000 * i, lambda m=message: self.update_splash(m))

    def update_splash(self, message):
        if self.splash:
            self.splash.showMessage(
                message,
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

    def on_error(self, error_message):
        self.main_window.update_check_status(f"Error: {error_message}")
        QMessageBox.critical(self.main_window, "Error", error_message)

    def start_update(self, download_url):
        # Implement update process here
        pass

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("Error caught!")
    print("Error message:", exc_value)
    print("Error traceback:", tb)
    QMessageBox.critical(None, "Error", f"An unexpected error occurred:\n\n{tb}")

def main():
    sys.excepthook = excepthook
    app = KingCunninghamApp(sys.argv)
    app.run()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()