from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QHBoxLayout, QLabel
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon
from .document_processor_ui import DocumentProcessorUI

class MainWindow(QMainWindow):
    check_for_updates = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Multi-Task Application")
        
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Main menu
        self.main_menu = QWidget()
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Multi-Task Application")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Buttons container
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout()
        
        # Function to create styled buttons
        def create_button(text, icon_path):
            button = QPushButton(text)
            button.setIcon(QIcon(icon_path))
            button.setIconSize(button.sizeHint())
            button.setMinimumSize(200, 100)
            button_font = QFont()
            button_font.setPointSize(12)
            button.setFont(button_font)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            return button

        update_button = create_button("Check for Updates", "path/to/update_icon.png")
        update_button.clicked.connect(self.check_for_updates.emit)
        buttons_layout.addWidget(update_button)

        doc_process_button = create_button("Document Processing", "path/to/doc_icon.png")
        doc_process_button.clicked.connect(self.show_document_processor)
        buttons_layout.addWidget(doc_process_button)

        web_auto_button = create_button("Web Automation", "path/to/web_icon.png")
        web_auto_button.clicked.connect(self.show_web_automation)
        buttons_layout.addWidget(web_auto_button)

        buttons_widget.setLayout(buttons_layout)
        main_layout.addWidget(buttons_widget)

        self.main_menu.setLayout(main_layout)

        # Document Processor
        self.doc_processor = DocumentProcessorUI()
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.doc_processor.layout().addWidget(back_button)

        # Web Automation (placeholder)
        self.web_automation = QWidget()
        web_layout = QVBoxLayout()
        web_layout.addWidget(QLabel("Web Automation Placeholder"))
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        web_layout.addWidget(back_button)
        self.web_automation.setLayout(web_layout)

        # Add widgets to stacked widget
        self.central_widget.addWidget(self.main_menu)
        self.central_widget.addWidget(self.doc_processor)
        self.central_widget.addWidget(self.web_automation)

        self.show_main_menu()

    def show_main_menu(self):
        self.central_widget.setCurrentWidget(self.main_menu)
        self.adjustSize()  # Adjust size to fit content

    def show_document_processor(self):
        self.central_widget.setCurrentWidget(self.doc_processor)
        self.resize(800, 600)  # Set fixed size for document processor

    def show_web_automation(self):
        self.central_widget.setCurrentWidget(self.web_automation)
        self.resize(800, 600)  # Set fixed size for web automation

    def update_check_status(self, status):
        QMessageBox.information(self, "Update Status", status)

    def show_update_available(self, new_version):
        reply = QMessageBox.question(
            self,
            "Update Available",
            f"A new version (v{new_version}) is available. Do you want to update?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def show_no_update(self):
        QMessageBox.information(self, "No Update Available", "You are using the latest version.")

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)