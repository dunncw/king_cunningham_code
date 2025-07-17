# ui/components/api_config.py - API configuration widget
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
import os
import json


class APIConfigWidget(QGroupBox):
    """Widget for API token configuration and testing"""
    
    # Signals
    config_saved = pyqtSignal()
    test_requested = pyqtSignal(str)  # Emits API token for testing
    
    def __init__(self):
        super().__init__("API Configuration")
        self.config_file = os.path.join(os.path.expanduser("~"), ".simplifile_conf.json")
        self.config = {}
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """Initialize the widget UI"""
        layout = QVBoxLayout()
        
        # API Token input
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("API Token:"))
        
        self.api_token = QLineEdit()
        self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token.setPlaceholderText("Enter your Simplifile API token")
        token_layout.addWidget(self.api_token)
        
        layout.addLayout(token_layout)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("Save API Config")
        self.save_config_btn.clicked.connect(self.save_config)
        
        self.test_connection_btn = QPushButton("Test API Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        
        button_layout.addWidget(self.save_config_btn, 1)
        button_layout.addWidget(self.test_connection_btn, 1)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_api_token(self) -> str:
        """Get the current API token"""
        return self.api_token.text().strip()
    
    def set_api_token(self, token: str):
        """Set the API token"""
        self.api_token.setText(token)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {"api_token": ""}
        except Exception:
            self.config = {"api_token": ""}
        
        # Apply loaded config to UI
        if self.config.get("api_token"):
            self.set_api_token(self.config["api_token"])
    
    def save_config(self):
        """Save API configuration"""
        try:
            self.config["api_token"] = self.get_api_token()
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            QMessageBox.information(self, "Success", "API configuration saved.")
            self.config_saved.emit()
            
        except Exception as e:
            error_msg = f"Failed to save configuration: {str(e)}"
            QMessageBox.critical(self, "Error", error_msg)
    
    def test_connection(self):
        """Request API connection test"""
        api_token = self.get_api_token()
        
        if not api_token:
            QMessageBox.warning(self, "Error", "Please enter an API token.")
            return
        
        # Emit signal for parent to handle the actual test
        self.test_requested.emit(api_token)
    
    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return bool(self.get_api_token())