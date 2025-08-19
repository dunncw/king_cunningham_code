from typing import Optional, Callable


class Logger:
    """Simple logger with optional UI callback."""
    
    def __init__(self, ui_callback: Optional[Callable[[str], None]] = None):
        self.ui_callback = ui_callback
    
    def _log(self, level: str, message: str):
        """Internal logging method."""
        # Only output the message, no timestamp or level
        if self.ui_callback:
            self.ui_callback(message)
        else:
            print(message)
    
    def info(self, message: str):
        """Log info message."""
        self._log("INFO", message)
    
    def warning(self, message: str):
        """Log warning message."""
        self._log("WARN", message)
    
    def error(self, message: str):
        """Log error message."""
        self._log("ERROR", message)
    
    def debug(self, message: str):
        """Log debug message."""
        self._log("DEBUG", message)