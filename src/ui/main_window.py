from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QHBoxLayout, QLabel,
    QStatusBar, QGridLayout, QFrame,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon
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
from simplifile.batch_processor import run_simplifile_batch_thread

def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    check_for_updates = pyqtSignal()
    start_web_automation = pyqtSignal(str, str, str, str, str, str, bool)
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

        # NO MENU BAR - Removed completely
        
        # Clean status bar (minimal)
        self.statusBar = QStatusBar()
        self.statusBar.setStyleSheet("background-color: #2c2c2c; color: #e0e0e0;")
        self.setStatusBar(self.statusBar)

        # Main menu - Clean, focused design
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
                padding: 15px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1f6aa5;
            }
            QFrame {
                background-color: #2c2c2c;
                border-radius: 8px;
                border: 1px solid #3c3c3c;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Clean header section
        header_container = QFrame()
        header_container.setStyleSheet("background-color: transparent; border: none;")
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        # Company logo (smaller, cleaner)
        logo_label = QLabel()
        logo_path = get_resource_path(os.path.join("resources", "app_icon.ico"))
        if os.path.exists(logo_path):
            logo_label.setPixmap(QIcon(logo_path).pixmap(80, 80))  # Smaller logo
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(logo_label)
        
        # Title (simplified)
        title_label = QLabel("King & Cunningham")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #e0e0e0;")
        header_layout.addWidget(title_label)
        
        # Subtitle (simplified)
        subtitle_label = QLabel("Legal Automation Suite")
        subtitle_font = QFont("Segoe UI", 12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #a0a0a0;")
        header_layout.addWidget(subtitle_label)
        
        header_container.setLayout(header_layout)
        main_layout.addWidget(header_container)
        
        # Clean separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("background-color: #3c3c3c; max-height: 1px; border: none;")
        main_layout.addWidget(separator)
        
        # Grid for application buttons (cleaner, more focused)
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background-color: transparent;")
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(20)
        
        # Define modules (streamlined list)
        modules = [
            {
                "name": "PT-61 Forms",
                "description": "Automated PT-61 form processing",
                "action": self.show_web_automation
            },
            {
                "name": "Document Processing", 
                "description": "OCR and document conversion",
                "action": self.show_document_processor
            },
            {
                "name": "Court Records",
                "description": "Automated records gathering",
                "action": self.show_crg_automation
            },
            {
                "name": "SCRA Lookup",
                "description": "Service member verification",
                "action": self.show_scra_automation
            },
            {
                "name": "PACER Access",
                "description": "Federal court documents",
                "action": self.show_pacer_automation
            },
            {
                "name": "Simplifile",
                "description": "Electronic document recording",
                "action": self.show_simplifile
            }
        ]
        
        # Create clean module cards (2x3 grid)
        row, col = 0, 0
        for module in modules:
            card = self.create_clean_module_card(
                module["name"],
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
        
        # Add bottom spacing
        main_layout.addStretch()
        
        self.main_menu.setLayout(main_layout)

        # All existing automation UIs (unchanged)
        self.doc_processor = DocumentProcessorUI()
        self.doc_processor.start_processing.connect(self.start_document_processing)
        back_button = QPushButton("← Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.doc_processor.layout().addWidget(back_button)

        self.web_automation = WebAutomationUI()
        self.web_automation.start_automation.connect(self.start_web_automation)
        back_button = QPushButton("← Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.web_automation.layout().addWidget(back_button)

        self.crg_automation = CRGAutomationUI()
        self.crg_automation.start_automation.connect(self.start_crg_automation)
        back_button = QPushButton("← Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.crg_automation.layout().addWidget(back_button)

        self.scra_automation = SCRAAutomationUI()
        back_button = QPushButton("← Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.scra_automation.layout().addWidget(back_button)

        self.pacer_automation = PACERAutomationUI()
        back_button = QPushButton("← Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        self.pacer_automation.layout().addWidget(back_button)

        # Updated Simplifile UI - no single upload signal connection needed
        self.simplifile_ui = SimplifileUI()
        self.simplifile_ui.start_simplifile_batch_upload.connect(self.start_simplifile_batch_process)
        back_button = QPushButton("← Back to Main Menu")
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
    
    def create_clean_module_card(self, title, description, click_handler):
        """Create a clean, minimal card widget for each module"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border-radius: 8px;
                border: 1px solid #3c3c3c;
                padding: 0px;
            }
            QFrame:hover {
                border: 1px solid #3498db;
                background-color: #353535;
            }
        """)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card.setMinimumSize(280, 120)
        card.setMaximumSize(320, 140)
        
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e0e0e0; background: transparent; border: none;")
        card_layout.addWidget(title_label)
        
        # Description
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #a0a0a0; background: transparent; border: none;")
        card_layout.addWidget(description_label)
        
        # Spacer
        card_layout.addStretch()
        
        # Launch button (smaller, integrated)
        launch_button = QPushButton("Launch")
        launch_button.setMaximumHeight(35)
        launch_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
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
        return card

    def show_main_menu(self):
        self.central_widget.setCurrentWidget(self.main_menu)
        self.resize(900, 650)  # Clean, appropriate size

    # All existing navigation methods (unchanged)
    def show_document_processor(self):
        self.central_widget.setCurrentWidget(self.doc_processor)
        self.resize(800, 600)

    def show_web_automation(self):
        self.central_widget.setCurrentWidget(self.web_automation)
        self.resize(800, 600)

    def show_crg_automation(self):
        self.central_widget.setCurrentWidget(self.crg_automation)
        self.resize(800, 600)

    def show_scra_automation(self):
        self.central_widget.setCurrentWidget(self.scra_automation)
        self.resize(800, 600)

    def show_pacer_automation(self):
        self.central_widget.setCurrentWidget(self.pacer_automation)
        self.resize(800, 600)
    
    def show_simplifile(self):
        self.central_widget.setCurrentWidget(self.simplifile_ui)
        self.resize(900, 800)

    def start_simplifile_batch_process(self, excel_path, deeds_path, mortgage_path):
        api_token = self.simplifile_ui.api_token.text()
        submitter_id = "SCTP3G"  # Hardcoded submitter ID
        recipient_id = self.simplifile_ui.recipient_combo.currentData()
        
        affidavits_path = self.simplifile_ui.affidavits_file_path.text() if hasattr(self.simplifile_ui, 'affidavits_file_path') else None
        
        self.batch_thread, self.batch_worker = run_simplifile_batch_thread(
            api_token, 
            submitter_id,
            recipient_id,
            excel_path, 
            deeds_path, 
            mortgage_path,
            affidavits_path
        )
        
        self.batch_worker.status.connect(self.simplifile_ui.update_status)
        self.batch_worker.progress.connect(self.simplifile_ui.update_progress)
        self.batch_worker.error.connect(self.simplifile_ui.show_error)
        self.batch_worker.finished.connect(self.simplifile_ui.batch_process_finished)
        
        self.batch_thread.start()

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

    def start_web_automation(self, excel_path, browser, username, password, save_location, version, document_stacking):
        """Start web automation with proper signal connections"""
        
        self.thread, self.worker = run_web_automation_thread(
            excel_path, browser, username, password, save_location, version, document_stacking
        )
        
        # Connect ALL worker signals to UI methods
        self.worker.status.connect(self.web_automation.update_status)
        self.worker.progress.connect(self.web_automation.update_progress)
        self.worker.error.connect(self.web_automation.show_error)
        self.worker.finished.connect(self.web_automation.automation_finished)
        
        # Also connect error to main window for fallback
        self.worker.error.connect(self.show_error)

        # Log start
        print(f"Starting automation with version: {version}")
        if document_stacking:
            print("Document stacking ENABLED - PDFs will be combined")
        else:
            print("Document stacking DISABLED - Individual PDFs will be saved")
            
        self.thread.start()

    def web_automation_finished(self):
        self.web_automation.start_button.setEnabled(True)
        self.web_automation.update_output("Web automation completed.")

    def update_check_status(self, status):
        self.statusBar.showMessage(status, 5000)

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