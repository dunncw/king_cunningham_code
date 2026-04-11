from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QHBoxLayout, QLabel,
    QStatusBar, QGridLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
import os
import sys
from .crg_automation_ui import CRGAutomationUI
from .document_processor_ui import DocumentProcessorUI
from .web_automation_ui import WebAutomationUI
from web_automation.automation import run_web_automation_thread
from document_processor.processor import OCRWorker
from .scra_automation_ui import SCRAAutomationUI
from .pacer_automation_ui import PACERAutomationUI
from simplifile3.ui.window import SimplifileWindow


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


THEME = """
QMainWindow {
    background-color: #191919;
}
QWidget {
    background-color: #191919;
    color: #e8e4e0;
    font-family: 'Styrene B';
}
QLabel {
    background-color: transparent;
}
QLineEdit {
    background-color: #242424;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 8px 12px;
    color: #e8e4e0;
}
QLineEdit:focus {
    border-color: #5a8dd6;
}
QComboBox {
    background-color: #242424;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px 12px;
    color: #e8e4e0;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #242424;
    color: #e8e4e0;
    border: 1px solid #333;
    selection-background-color: #333;
}
QPushButton {
    background-color: #2a2a2a;
    color: #e8e4e0;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: #333;
}
QPushButton:pressed {
    background-color: #222;
}
QPushButton:disabled {
    color: #555;
    border-color: #2a2a2a;
    background-color: #1e1e1e;
}
QProgressBar {
    background-color: #242424;
    border: none;
    border-radius: 4px;
}
QProgressBar::chunk {
    background-color: #5a8dd6;
    border-radius: 4px;
}
QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    color: #ccc;
    padding: 8px;
}
QGroupBox {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: bold;
    color: #9a9590;
}
QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 8px;
}
QCheckBox, QRadioButton {
    color: #e8e4e0;
    spacing: 8px;
}
QStatusBar {
    background-color: #191919;
    color: #555;
    border: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
}
QScrollBar::handle:vertical {
    background-color: #3a3a3a;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QFrame {
    border: none;
}
"""


class ClickableCard(QFrame):
    clicked = pyqtSignal()

    _NORMAL = "ClickableCard { background-color: #242424; border-radius: 12px; border: 1px solid transparent; }"
    _HOVER = "ClickableCard { background-color: #2c2c2c; border-radius: 12px; border: 1px solid #3a3a3a; }"

    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._NORMAL)
        self.setFixedHeight(110)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setFont(QFont("Styrene B", 14, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #e8e4e0;")
        layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Styrene B", 10))
        desc_label.setStyleSheet("color: #7a7570;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        self.setLayout(layout)

    def enterEvent(self, event):
        self.setStyleSheet(self._HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._NORMAL)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    start_web_automation = pyqtSignal(str, str, str, str, str, str, bool)
    start_crg_automation = pyqtSignal()

    def __init__(self, version):
        super().__init__()
        self.version = version
        self._pages = {}
        self.setStyleSheet(THEME)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("KC Automation Suite")

        self.setMinimumWidth(940)

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        self.setStatusBar(QStatusBar())

        self._build_main_menu()
        self._build_modules()
        self.show_main_menu()

    def _build_main_menu(self):
        self.main_menu = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 50, 60, 40)
        layout.setSpacing(0)

        title = QLabel("King & Cunningham")
        title.setFont(QFont("Styrene B", 22, QFont.Weight.DemiBold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(4)

        version = QLabel(f"v{self.version}")
        version.setFont(QFont("Styrene B", 9))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #4a4a4a;")
        layout.addWidget(version)

        layout.addSpacing(40)

        modules = [
            ("Simplifile", "Bulk document recording", self.show_simplifile),
            ("PT-61 Forms", "Bulk form generation", self.show_web_automation),
            ("Document Processing", "OCR and conversion", self.show_document_processor),
            ("Court Records CRG", "Automated records gathering", self.show_crg_automation),
            ("SCRA Lookup", "Service member verification", self.show_scra_automation),
            ("PACER Access", "Federal court documents", self.show_pacer_automation),
        ]

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        for i, (name, desc, handler) in enumerate(modules):
            card = ClickableCard(name, desc)
            card.clicked.connect(handler)
            grid.addWidget(card, i // 2, i % 2)

        grid_wrapper = QWidget()
        grid_wrapper.setLayout(grid)
        grid_wrapper.setFixedWidth(816)

        center = QHBoxLayout()
        center.addStretch()
        center.addWidget(grid_wrapper)
        center.addStretch()
        layout.addLayout(center)

        layout.addStretch()
        self.main_menu.setLayout(layout)
        self.central_widget.addWidget(self.main_menu)

    def _build_modules(self):
        self.doc_processor = DocumentProcessorUI()
        self.doc_processor.start_processing.connect(self.start_document_processing)

        self.web_automation = WebAutomationUI()
        self.web_automation.start_automation.connect(self.start_web_automation)

        self.crg_automation = CRGAutomationUI()
        self.crg_automation.start_automation.connect(self.start_crg_automation)

        self.scra_automation = SCRAAutomationUI()
        self.pacer_automation = PACERAutomationUI()
        self.simplifile_ui = SimplifileWindow()

        for widget in [
            self.doc_processor, self.web_automation, self.crg_automation,
            self.scra_automation, self.pacer_automation, self.simplifile_ui,
        ]:
            page = self._make_page(widget)
            self._pages[widget] = page
            self.central_widget.addWidget(page)

    def _make_page(self, widget):
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(60, 16, 60, 20)

        back_row = QHBoxLayout()
        back_row.addWidget(self._make_back_button())
        back_row.addStretch()
        layout.addLayout(back_row)

        layout.addSpacing(8)

        widget.setFixedWidth(816)
        center = QHBoxLayout()
        center.addStretch()
        center.addWidget(widget)
        center.addStretch()
        layout.addLayout(center, 1)

        page.setLayout(layout)
        return page

    def _make_back_button(self):
        btn = QPushButton("< Back")
        btn.setMaximumWidth(80)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #7a7570;
                font-size: 12px;
                padding: 4px 0;
                text-align: left;
            }
            QPushButton:hover {
                color: #e8e4e0;
            }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self.show_main_menu)
        return btn

    def show_main_menu(self):
        self.central_widget.setCurrentWidget(self.main_menu)

    def show_document_processor(self):
        self.central_widget.setCurrentWidget(self._pages[self.doc_processor])

    def show_web_automation(self):
        self.central_widget.setCurrentWidget(self._pages[self.web_automation])

    def show_crg_automation(self):
        self.central_widget.setCurrentWidget(self._pages[self.crg_automation])

    def show_scra_automation(self):
        self.central_widget.setCurrentWidget(self._pages[self.scra_automation])

    def show_pacer_automation(self):
        self.central_widget.setCurrentWidget(self._pages[self.pacer_automation])

    def show_simplifile(self):
        self.central_widget.setCurrentWidget(self._pages[self.simplifile_ui])

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
        self.thread, self.worker = run_web_automation_thread(
            excel_path, browser, username, password, save_location, version, document_stacking
        )
        self.worker.status.connect(self.web_automation.update_status)
        self.worker.progress.connect(self.web_automation.update_progress)
        self.worker.error.connect(self.web_automation.show_error)
        self.worker.finished.connect(self.web_automation.automation_finished)
        self.worker.error.connect(self.show_error)
        self.thread.start()

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
