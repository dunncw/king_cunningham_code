# File: src/main.py

import os
import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow, get_resource_path

__version__ = "0.0.14"


class KingCunninghamApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.main_window = None

    def run(self):
        self.setWindowIcon(QIcon(get_resource_path(os.path.join("resources", "app_icon.ico"))))
        self.main_window = MainWindow(__version__)
        self.main_window.setWindowIcon(self.windowIcon())
        self.main_window.showMaximized()
        self.main_window.raise_()
        self.main_window.activateWindow()


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
