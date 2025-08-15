# simplifile3/utils/logging.py - Centralized logging utilities (copied from simplifile2)
from typing import Callable, Optional
from datetime import datetime


class Logger:
    """Centralized logger that can emit to UI or console"""
    
    def __init__(self, ui_callback: Optional[Callable[[str], None]] = None):
        self.ui_callback = ui_callback
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Send to UI if callback provided
        if self.ui_callback:
            self.ui_callback(formatted_message)
        else:
            # Fallback to console
            print(formatted_message)
    
    def info(self, message: str):
        """Log info message"""
        self.log(message, "INFO")
    
    def warning(self, message: str):
        """Log warning message"""
        self.log(f"WARNING: {message}", "WARNING")
    
    def error(self, message: str):
        """Log error message"""
        self.log(f"ERROR: {message}", "ERROR")
    
    def header(self, title: str, char: str = "=", width: int = 60):
        """Log a header section"""
        self.log(char * width)
        self.log(title)
        self.log(char * width)
    
    def separator(self, char: str = "-", width: int = 60):
        """Log a separator line"""
        self.log(char * width)


class StepLogger:
    """Logger for step-by-step processes"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.current_step = 0
    
    def start_step(self, step_name: str):
        """Start a new step"""
        self.current_step += 1
        self.logger.log(f"Step {self.current_step}: {step_name}...")
    
    def step_success(self, message: str = ""):
        """Mark current step as successful"""
        if message:
            self.logger.log(f"   {message}")
    
    def step_warning(self, message: str):
        """Log a warning for current step"""
        self.logger.log(f"   WARNING: {message}")
    
    def step_error(self, message: str):
        """Log an error for current step"""
        self.logger.log(f"   ERROR: {message}")
    
    def reset(self):
        """Reset step counter"""
        self.current_step = 0