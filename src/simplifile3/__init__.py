# simplifile3/__init__.py - Simplifile3 package initialization
"""
Simplifile3: Workflow-first electronic document recording system

Key differences from simplifile2:
- Workflows are first-class citizens, not nested under counties
- Counties serve as reference data for document types and requirements
- Multi-county workflows supported within single workflow implementations
- Simplified UI with workflow selection driving configuration
"""

__version__ = "0.1.0"
__author__ = "King & Cunningham"

# Core components
from .core.processor import Simplifile3Processor
from .core.validator import Simplifile3Validator
from .workflows.registry import WorkflowRegistry

__all__ = [
    "Simplifile3Processor",
    "Simplifile3Validator", 
    "WorkflowRegistry"
]