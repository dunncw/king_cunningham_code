from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QHBoxLayout, QLabel,
    QMenuBar, QMenu, QStatusBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QAction
from .crg_automation_ui import CRGAutomationUI
from .document_processor_ui import DocumentProcessorUI
from .web_automation_ui import WebAutomationUI
from web_automation.automation import run_web_automation_thread
from document_processor.processor import OCRWorker
from .scra_automation_ui import SCRAAutomationUI
from .pacer_automation_ui import PACERAutomationUI

class MainWindow(QMainWindow):
    check_for_updates = pyqtSignal()
    start_web_automation = pyqtSignal(str, str, str)
    start_crg_automation = pyqtSignal()

    def __init__(self, version):
        super().__init__()
        self.version = version
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("King & Cunningham Software Suite")
        
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Main menu
        self.main_menu = QWidget()
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("King & Cunningham App Suite")
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
        def create_button(text, icon_path, click_handler):
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
            button.clicked.connect(click_handler)
            return button

        doc_process_button = create_button("Document Processing", "path/to/doc_icon.png", self.show_document_processor)
        buttons_layout.addWidget(doc_process_button)

        web_auto_button = create_button("PT61 Form", "path/to/web_icon.png", self.show_web_automation)
        buttons_layout.addWidget(web_auto_button)

        crg_auto_button = create_button("CRG Automation", "path/to/crg_icon.png", self.show_crg_automation)
        buttons_layout.addWidget(crg_auto_button)

        scra_auto_button = create_button("SCRA Automation", "path/to/scra_icon.png", self.show_scra_automation)
        buttons_layout.addWidget(scra_auto_button)

        pacer_auto_button = create_button("PACER Automation", "path/to/pacer_icon.png", self.show_pacer_automation)
        buttons_layout.addWidget(pacer_auto_button)

        buttons_widget.setLayout(buttons_layout)
        main_layout.addWidget(buttons_widget)

        self.main_menu.setLayout(main_layout)

        # Document Processor
        self.doc_processor = DocumentProcessorUI()
        self.doc_processor.start_processing.connect(self.start_document_processing)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.doc_processor.layout().addWidget(back_button)

        # Web Automation
        self.web_automation = WebAutomationUI()
        self.web_automation.start_automation.connect(self.start_web_automation)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.web_automation.layout().addWidget(back_button)

        # CRG Automation
        self.crg_automation = CRGAutomationUI()
        self.crg_automation.start_automation.connect(self.start_crg_automation)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.crg_automation.layout().addWidget(back_button)

        # SCRA Automation
        self.scra_automation = SCRAAutomationUI()
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.scra_automation.layout().addWidget(back_button)

        # PACER Automation
        self.pacer_automation = PACERAutomationUI()
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.pacer_automation.layout().addWidget(back_button)

        # Add widgets to stacked widget
        self.central_widget.addWidget(self.main_menu)
        self.central_widget.addWidget(self.doc_processor)
        self.central_widget.addWidget(self.web_automation)
        self.central_widget.addWidget(self.crg_automation)
        self.central_widget.addWidget(self.scra_automation)
        self.central_widget.addWidget(self.pacer_automation)

        self.show_main_menu()

    def show_pacer_automation(self):
        self.central_widget.setCurrentWidget(self.pacer_automation)
        self.resize(800, 600)  # Set fixed size for PACER automation

    def show_scra_automation(self):
        self.central_widget.setCurrentWidget(self.scra_automation)
        self.resize(800, 600)  # Set fixed size for SCRA automation

    def show_crg_automation(self):
        self.central_widget.setCurrentWidget(self.crg_automation)
        self.resize(800, 600)  # Set fixed size for CRG automation

    def start_document_processing(self, input_path, output_dir, is_directory):
        self.ocr_worker = OCRWorker(input_path, output_dir, is_directory)
        self.ocr_worker.progress_update.connect(self.doc_processor.update_progress)
        self.ocr_worker.output_update.connect(self.doc_processor.update_output)
        self.ocr_worker.finished.connect(self.on_document_processing_finished)
        self.ocr_worker.error.connect(self.on_document_processing_error)
        
        self.doc_processor.process_button.setEnabled(False)
        self.doc_processor.update_output("Starting document processing with OCR...")
        self.ocr_worker.start()

    def on_document_processing_finished(self):
        self.doc_processor.processing_finished()
        self.doc_processor.process_button.setEnabled(True)
        self.doc_processor.update_output("Document processing with OCR completed.")

    def on_document_processing_error(self, error_message):
        self.doc_processor.show_error(error_message)
        self.doc_processor.process_button.setEnabled(True)

    def start_web_automation(self, excel_path, browser, username, password, save_location):
        self.thread, self.worker = run_web_automation_thread(excel_path, browser, username, password, save_location)
        
        self.worker.status.connect(self.web_automation.update_output)
        self.worker.progress.connect(self.web_automation.update_progress)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.web_automation_finished)

        self.web_automation.start_button.setEnabled(False)
        self.thread.start()

    def web_automation_finished(self):
        self.web_automation.start_button.setEnabled(True)
        self.web_automation.update_output("Web automation completed.")

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # Single menu called "Menu"
        menu = menubar.addMenu('Menu')
        
        # Add "Check for Updates" action
        update_action = QAction('Check for Updates', self)
        update_action.triggered.connect(self.check_for_updates.emit)
        menu.addAction(update_action)
        
        # Add version information
        version_action = QAction(f'Version: {self.version}', self)
        version_action.setEnabled(False)  # Make it non-clickable
        menu.addAction(version_action)

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
        self.statusBar.showMessage(status, 5000)  # Show message for 5 seconds

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
        self.statusBar.showMessage("You are using the latest version.", 5000)

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)