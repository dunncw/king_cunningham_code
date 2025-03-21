from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QHBoxLayout, QLabel,
    QMenuBar, QMenu, QStatusBar, QGridLayout, QFrame,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QAction
import os
import sys
from .crg_automation_ui import CRGAutomationUI
from .document_processor_ui import DocumentProcessorUI
from .web_automation_ui import WebAutomationUI
from web_automation.automation import run_web_automation_thread
from document_processor.processor import OCRWorker
from .scra_automation_ui import SCRAAutomationUI
from .pacer_automation_ui import PACERAutomationUI
from .simplifile_ui import SimplifileUI
from simplifile.api import run_simplifile_thread
from simplifile.batch_processor import run_simplifile_batch_thread

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    check_for_updates = pyqtSignal()
    start_web_automation = pyqtSignal(str, str, str)
    start_crg_automation = pyqtSignal()
    start_simplifile_batch_upload = pyqtSignal(str, str, str, str, str, str)

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
        self.statusBar.setStyleSheet("background-color: #2c2c2c; color: #e0e0e0;")
        self.setStatusBar(self.statusBar)

        # Main menu - Dark theme
        self.main_menu = QWidget()
        self.main_menu.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1f6aa5;
            }
            QFrame {
                background-color: #2c2c2c;
                border-radius: 6px;
                border: 1px solid #3c3c3c;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Company logo
        logo_container = QFrame()
        logo_container.setStyleSheet("background-color: transparent; border: none;")
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_label = QLabel()
        logo_path = get_resource_path(os.path.join("resources", "app_icon.ico"))
        if os.path.exists(logo_path):
            logo_label.setPixmap(QIcon(logo_path).pixmap(100, 100))
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel("King & Cunningham App Suite")
        title_font = QFont("Segoe UI", 24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #e0e0e0;")
        logo_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Legal Automation Tools")
        subtitle_font = QFont("Segoe UI", 14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #a0a0a0;")
        logo_layout.addWidget(subtitle_label)
        
        logo_container.setLayout(logo_layout)
        main_layout.addWidget(logo_container)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #3c3c3c; max-height: 1px; border: none;")
        main_layout.addWidget(separator)
        
        # Grid for buttons
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: transparent;")
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(20)
        
        # Define our modules with icons and descriptions
        modules = [
            {
                "name": "Document Processing",
                "icon": "resources/doc_icon.png",
                "description": "OCR and document processing tools",
                "action": self.show_document_processor
            },
            {
                "name": "PT61 Form",
                "icon": "resources/web_icon.png",
                "description": "Web form automation",
                "action": self.show_web_automation
            },
            {
                "name": "CRG Automation",
                "icon": "resources/crg_icon.png",
                "description": "Court records gathering",
                "action": self.show_crg_automation
            },
            {
                "name": "SCRA Automation",
                "icon": "resources/scra_icon.png",
                "description": "Service members lookup",
                "action": self.show_scra_automation
            },
            {
                "name": "PACER Automation",
                "icon": "resources/pacer_icon.png",
                "description": "Federal court documents",
                "action": self.show_pacer_automation
            },
            {
                "name": "Simplifile",
                "icon": "resources/simplifile_icon.png",
                "description": "Electronic recording",
                "action": self.show_simplifile
            }
        ]
        
        # Create module cards
        row, col = 0, 0
        for module in modules:
            card = self.create_module_card(
                module["name"],
                module["icon"],
                module["description"],
                module["action"]
            )
            buttons_grid.addWidget(card, row, col)
            col += 1
            if col > 1:  # Two columns layout
                col = 0
                row += 1
        
        buttons_widget.setLayout(buttons_grid)
        main_layout.addWidget(buttons_widget)
        
        # Version info at bottom
        version_label = QLabel(f"Version {self.version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        version_label.setStyleSheet("color: #707070; font-size: 10px; background-color: transparent;")
        main_layout.addWidget(version_label)
        
        self.main_menu.setLayout(main_layout)

        # Document Processor - don't modify
        self.doc_processor = DocumentProcessorUI()
        self.doc_processor.start_processing.connect(self.start_document_processing)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.doc_processor.layout().addWidget(back_button)

        # Web Automation - don't modify
        self.web_automation = WebAutomationUI()
        self.web_automation.start_automation.connect(self.start_web_automation)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.web_automation.layout().addWidget(back_button)

        # CRG Automation - don't modify
        self.crg_automation = CRGAutomationUI()
        self.crg_automation.start_automation.connect(self.start_crg_automation)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.crg_automation.layout().addWidget(back_button)

        # SCRA Automation - don't modify
        self.scra_automation = SCRAAutomationUI()
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.scra_automation.layout().addWidget(back_button)

        # PACER Automation - don't modify
        self.pacer_automation = PACERAutomationUI()
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.pacer_automation.layout().addWidget(back_button)

        # Simplifile UI - don't modify
        self.simplifile_ui = SimplifileUI()
        self.simplifile_ui.start_simplifile_upload.connect(self.start_simplifile_upload)
        self.simplifile_ui.start_simplifile_batch_upload.connect(self.start_simplifile_batch_process)
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.simplifile_ui.layout().addWidget(back_button)

        # Add widgets to stacked widget
        self.central_widget.addWidget(self.main_menu)
        self.central_widget.addWidget(self.doc_processor)
        self.central_widget.addWidget(self.web_automation)
        self.central_widget.addWidget(self.crg_automation)
        self.central_widget.addWidget(self.scra_automation)
        self.central_widget.addWidget(self.pacer_automation)
        self.central_widget.addWidget(self.simplifile_ui)

        self.show_main_menu()
    
    def create_module_card(self, title, icon_path, description, click_handler):
        """Create a modern card widget for a module with dark theme and non-interactive text"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border-radius: 6px;
                border: 1px solid #3c3c3c;
            }
            QFrame:hover {
                border: 1px solid #3498db;
                background-color: #353535;
            }
        """)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setMinimumSize(300, 160)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 15, 20, 15)
        
        # Header with icon and title - make this a non-interactive label
        header_layout = QHBoxLayout()
        
        # Create a container for the header that won't have hover effects
        header_container = QLabel()
        header_container.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                color: #e0e0e0;
            }
        """)
        
        # Icon if available
        header_text = ""
        if os.path.exists(icon_path):
            # We'll add the icon in the header_container if needed
            # For now, just use text
            pass
        
        # Title - made part of the label
        title_font = QFont("Segoe UI", 12)
        title_font.setBold(True)
        header_text = title
        
        header_container.setText(header_text)
        header_container.setFont(title_font)
        header_layout.addWidget(header_container)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # Description - non-interactive label
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("""
            QLabel {
                color: #a0a0a0; 
                background-color: transparent;
                border: none;
            }
        """)
        card_layout.addWidget(description_label)
        
        # Spacer
        card_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Launch button
        launch_button = QPushButton("Launch")
        launch_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1f6aa5;
            }
        """)
        launch_button.clicked.connect(click_handler)
        card_layout.addWidget(launch_button)
        
        card.setLayout(card_layout)
        
        # Make the whole card clickable except for text
        # This is tricky - we can't easily make only parts of the card clickable
        # Instead, we'll make the launch button the primary interaction point
        
        return card
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QMenuBar::item {
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #2c2c2c;
            }
            QMenu {
                background-color: #2c2c2c;
                color: #e0e0e0;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
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
        self.resize(800, 700)  # Set a fixed size for main menu

    # The rest of the methods are kept as-is for downstream pages
    def show_document_processor(self):
        self.central_widget.setCurrentWidget(self.doc_processor)
        self.resize(800, 600)  # Set fixed size for document processor

    def show_web_automation(self):
        self.central_widget.setCurrentWidget(self.web_automation)
        self.resize(800, 600)  # Set fixed size for web automation

    def show_crg_automation(self):
        self.central_widget.setCurrentWidget(self.crg_automation)
        self.resize(800, 600)  # Set fixed size for CRG automation

    def show_scra_automation(self):
        self.central_widget.setCurrentWidget(self.scra_automation)
        self.resize(800, 600)  # Set fixed size for SCRA automation

    def show_pacer_automation(self):
        self.central_widget.setCurrentWidget(self.pacer_automation)
        self.resize(800, 600)  # Set fixed size for PACER automation
    
    def show_simplifile(self):
        """Show the Simplifile UI"""
        self.central_widget.setCurrentWidget(self.simplifile_ui)
        self.resize(900, 800)  # Set appropriate size for Simplifile UI
    
    def start_simplifile_upload(self, api_token, submitter_id, recipient_id, package_data, document_files):
        """Start Simplifile upload process"""
        self.simplifile_thread, self.simplifile_worker = run_simplifile_thread(
            api_token, submitter_id, recipient_id, package_data, document_files
        )
        
        # Connect signals
        self.simplifile_worker.status.connect(self.simplifile_ui.update_status)
        self.simplifile_worker.progress.connect(self.simplifile_ui.update_progress)
        self.simplifile_worker.error.connect(self.simplifile_ui.show_error)
        self.simplifile_worker.finished.connect(self.simplifile_ui.upload_finished)
        
        # Start thread
        self.simplifile_thread.start()
    
    def start_simplifile_batch_process(self, excel_path, deeds_path, mortgage_path):
        """Start Simplifile batch processing with API support"""
        # Get API credentials
        api_token = self.simplifile_ui.api_token.text()
        submitter_id = self.simplifile_ui.submitter_id.text()
        recipient_id = self.simplifile_ui.recipient_combo.currentData()
        
        # Determine if this is preview mode (default to True for safety)
        preview_mode = True  # This could be passed from the UI if we had a checkbox
        
        self.batch_thread, self.batch_worker = run_simplifile_batch_thread(
            excel_path, 
            deeds_path, 
            mortgage_path,
            api_token,
            submitter_id,
            recipient_id,
            preview_mode
        )
        
        # Connect signals
        self.batch_worker.status.connect(self.simplifile_ui.update_status)
        self.batch_worker.progress.connect(self.simplifile_ui.update_progress)
        self.batch_worker.error.connect(self.simplifile_ui.show_error)
        self.batch_worker.finished.connect(self.simplifile_ui.batch_process_finished)
        
        # Start thread
        self.batch_thread.start()
    
    def show_simplifile_error(self, error_message):
        """Show error message from Simplifile process"""
        self.simplifile_ui.update_output(f"Error: {error_message}")
        QMessageBox.critical(self, "Simplifile Error", error_message)
    
    def simplifile_upload_finished(self):
        """Called when Simplifile upload process finishes"""
        self.simplifile_ui.update_output("Simplifile upload process completed.")
        self.simplifile_ui.progress_bar.setValue(100)

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