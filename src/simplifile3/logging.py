"""Simplified logging for Simplifile3."""

from typing import Optional, Callable


class Logger:
    """Simple logger that outputs messages directly without timestamps or levels."""
    
    def __init__(self, ui_callback: Optional[Callable[[str], None]] = None):
        self.ui_callback = ui_callback
    
    def _log(self, message: str):
        """Internal logging method - just output the message."""
        if self.ui_callback:
            self.ui_callback(message)
        else:
            print(message)
    
    def info(self, message: str):
        """Log info message."""
        self._log(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self._log(message)
    
    def error(self, message: str):
        """Log error message."""
        self._log(message)