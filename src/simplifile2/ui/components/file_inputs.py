# ui/components/file_inputs.py - Dynamic file input widgets that adapt to workflow
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFileDialog
)
from PyQt6.QtCore import pyqtSignal
import os
from typing import Dict, List, Any


class FileInputWidget(QHBoxLayout):
    """Single file input widget with label, path display, and browse button"""
    
    file_changed = pyqtSignal(str)  # Emits file path when changed
    
    def __init__(self, file_config: Dict[str, Any]):
        super().__init__()
        self.file_config = file_config
        
        # Label
        self.addWidget(QLabel(f"{file_config['label']}:"))
        
        # Path display
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(file_config['placeholder'])
        self.path_edit.setReadOnly(True)
        self.path_edit.textChanged.connect(self.file_changed.emit)
        self.addWidget(self.path_edit)
        
        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        self.addWidget(browse_btn)
    
    def browse_file(self):
        """Open file or directory browser based on input type"""
        if self.file_config['type'] == 'directory':
            # Directory selection
            directory_path = QFileDialog.getExistingDirectory(
                None, f"Select {self.file_config['label']}", ""
            )
            if directory_path:
                self.path_edit.setText(directory_path)
        else:
            # File selection
            file_path, _ = QFileDialog.getOpenFileName(
                None, f"Select {self.file_config['label']}", "", self.file_config['filter']
            )
            if file_path:
                self.path_edit.setText(file_path)
    
    def get_path(self) -> str:
        """Get current file/directory path"""
        return self.path_edit.text().strip()
    
    def set_path(self, path: str):
        """Set file/directory path"""
        self.path_edit.setText(path)
    
    def is_valid(self) -> bool:
        """Check if file/directory path is valid"""
        path = self.get_path()
        if not path or not os.path.exists(path):
            return False
        
        if self.file_config['type'] == 'directory':
            return os.path.isdir(path)
        else:
            return os.path.isfile(path)


class FileInputsWidget(QGroupBox):
    """Widget containing all file inputs for the workflow - dynamically adapts to workflow"""
    
    # Signals
    files_changed = pyqtSignal()  # Emitted when any file changes
    
    def __init__(self):
        super().__init__("Input Files")
        self.file_widgets = {}
        self.current_workflow_config = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the widget UI with empty layout"""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Placeholder message
        self.placeholder_label = QLabel("Select a county and workflow to configure file inputs")
        self.placeholder_label.setStyleSheet("color: #a0a0a0; font-style: italic; text-align: center; padding: 20px;")
        self.layout.addWidget(self.placeholder_label)
    
    def update_for_workflow(self, workflow_config: Dict[str, Any]):
        """Update file inputs based on workflow configuration"""
        self.current_workflow_config = workflow_config
        self.file_widgets.clear()
        
        # Clear existing layout
        self.clear_layout()
        
        if not workflow_config or 'required_files' not in workflow_config:
            # Show placeholder
            self.placeholder_label = QLabel("Invalid workflow configuration")
            self.placeholder_label.setStyleSheet("color: #ff6b6b; font-style: italic; text-align: center; padding: 20px;")
            self.layout.addWidget(self.placeholder_label)
            return
        
        # Create file input widgets based on workflow config
        required_files = workflow_config['required_files']
        
        for file_config in required_files:
            file_widget = FileInputWidget(file_config)
            file_widget.file_changed.connect(self.files_changed.emit)
            
            self.layout.addLayout(file_widget)
            self.file_widgets[file_config['key']] = file_widget
        
        # Emit files changed to trigger validation update
        self.files_changed.emit()
    
    def clear_layout(self):
        """Clear all widgets from layout"""
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_sublayout(child.layout())
    
    def clear_sublayout(self, layout):
        """Recursively clear a sublayout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_sublayout(child.layout())
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get all file paths as dictionary"""
        file_paths = {}
        for key, widget in self.file_widgets.items():
            file_paths[key] = widget.get_path()
        return file_paths
    
    def validate_files(self) -> List[str]:
        """Validate all file inputs and return list of errors"""
        errors = []
        
        if not self.current_workflow_config:
            errors.append("No workflow selected")
            return errors
        
        required_files = self.current_workflow_config.get('required_files', [])
        file_paths = self.get_file_paths()
        
        for file_config in required_files:
            key = file_config['key']
            label = file_config['label']
            path = file_paths.get(key, "")
            
            if not path:
                errors.append(f"{label} is required")
            elif not os.path.exists(path):
                errors.append(f"{label} does not exist: {path}")
            elif file_config['type'] == 'directory' and not os.path.isdir(path):
                errors.append(f"{label} is not a directory: {path}")
            elif file_config['type'] == 'file' and not os.path.isfile(path):
                errors.append(f"{label} is not a file: {path}")
        
        return errors
    
    def are_all_files_selected(self) -> bool:
        """Check if all required files are selected and valid"""
        return len(self.validate_files()) == 0
    
    def clear_all(self):
        """Clear all file paths"""
        for widget in self.file_widgets.values():
            widget.set_path("")
    
    def get_workflow_type(self) -> str:
        """Get the input type for current workflow"""
        return self.current_workflow_config.get('input_type', '')