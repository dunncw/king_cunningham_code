# ui/components/file_inputs.py - File input widgets
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog
)
from PyQt6.QtCore import pyqtSignal
import os
from typing import Dict


class FileInputWidget(QHBoxLayout):
    """Single file input widget with label, path display, and browse button"""
    
    file_changed = pyqtSignal(str)  # Emits file path when changed
    
    def __init__(self, label_text: str, placeholder: str, file_filter: str):
        super().__init__()
        self.file_filter = file_filter
        
        # Label
        self.addWidget(QLabel(f"{label_text}:"))
        
        # Path display
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(placeholder)
        self.path_edit.setReadOnly(True)
        self.path_edit.textChanged.connect(self.file_changed.emit)
        self.addWidget(self.path_edit)
        
        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        self.addWidget(browse_btn)
    
    def browse_file(self):
        """Open file browser"""
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select File", "", self.file_filter
        )
        if file_path:
            self.path_edit.setText(file_path)
    
    def get_path(self) -> str:
        """Get current file path"""
        return self.path_edit.text().strip()
    
    def set_path(self, path: str):
        """Set file path"""
        self.path_edit.setText(path)
    
    def is_valid(self) -> bool:
        """Check if file path is valid"""
        path = self.get_path()
        return bool(path and os.path.exists(path) and os.path.isfile(path))


class FileInputsWidget(QGroupBox):
    """Widget containing all file inputs for the workflow"""
    
    # Signals
    files_changed = pyqtSignal()  # Emitted when any file changes
    
    def __init__(self):
        super().__init__("Input Files")
        self.file_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the widget UI"""
        layout = QVBoxLayout()
        
        # Define file inputs
        file_configs = [
            {
                "key": "excel",
                "label": "Excel File",
                "placeholder": "Select Excel file with package data",
                "filter": "Excel Files (*.xlsx *.xls)"
            },
            {
                "key": "deed",
                "label": "Deed Stack PDF",
                "placeholder": "Select deed stack PDF (3 pages per document)",
                "filter": "PDF Files (*.pdf)"
            },
            {
                "key": "pt61",
                "label": "PT-61 Stack PDF",
                "placeholder": "Select PT-61 stack PDF (1 page per document)",
                "filter": "PDF Files (*.pdf)"
            },
            {
                "key": "mortgage",
                "label": "Mortgage Satisfaction Stack PDF",
                "placeholder": "Select mortgage satisfaction stack PDF (1 page per document)",
                "filter": "PDF Files (*.pdf)"
            }
        ]
        
        # Create file input widgets
        for config in file_configs:
            file_widget = FileInputWidget(
                config["label"],
                config["placeholder"],
                config["filter"]
            )
            file_widget.file_changed.connect(self.files_changed.emit)
            
            layout.addLayout(file_widget)
            self.file_widgets[config["key"]] = file_widget
        
        self.setLayout(layout)
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get all file paths as dictionary"""
        return {
            "excel_path": self.file_widgets["excel"].get_path(),
            "deed_path": self.file_widgets["deed"].get_path(),
            "pt61_path": self.file_widgets["pt61"].get_path(),
            "mortgage_path": self.file_widgets["mortgage"].get_path()
        }
    
    def validate_files(self) -> list[str]:
        """Validate all file inputs and return list of errors"""
        errors = []
        file_paths = self.get_file_paths()
        
        file_names = {
            "excel_path": "Excel file",
            "deed_path": "Deed Stack PDF",
            "pt61_path": "PT-61 Stack PDF",
            "mortgage_path": "Mortgage Satisfaction Stack PDF"
        }
        
        for key, path in file_paths.items():
            file_name = file_names[key]
            
            if not path:
                errors.append(f"{file_name} is required")
            elif not os.path.exists(path):
                errors.append(f"{file_name} does not exist: {path}")
            elif not os.path.isfile(path):
                errors.append(f"{file_name} is not a file: {path}")
        
        return errors
    
    def are_all_files_selected(self) -> bool:
        """Check if all required files are selected and valid"""
        return len(self.validate_files()) == 0
    
    def clear_all(self):
        """Clear all file paths"""
        for widget in self.file_widgets.values():
            widget.set_path("")