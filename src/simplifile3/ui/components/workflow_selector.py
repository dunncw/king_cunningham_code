# simplifile3/ui/components/workflow_selector.py - Simplified workflow selector (no county dropdown)
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any
from ...workflows.registry import workflow_registry


class WorkflowSelectorWidget(QGroupBox):
    """Widget for selecting workflow (no county selection needed)"""
    
    # Signals
    selection_changed = pyqtSignal(str, dict)  # workflow_id, workflow_config
    
    def __init__(self):
        super().__init__("Workflow Selection")
        self.current_workflow_config = {}
        self.init_ui()
        self.populate_workflows()
    
    def init_ui(self):
        """Initialize the widget UI"""
        layout = QVBoxLayout()
        
        # # Workflow selection
        workflow_layout = QHBoxLayout()
        
        self.workflow_combo = QComboBox()
        self.workflow_combo.currentTextChanged.connect(self.emit_selection_changed)
        workflow_layout.addWidget(self.workflow_combo)
        
        layout.addLayout(workflow_layout)
        
        # Workflow description as clickable link
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setOpenExternalLinks(True)  # Enable clickable links
        layout.addWidget(self.description_label)

        self.setLayout(layout)
    
    def populate_workflows(self):
        """Populate workflow dropdown from registry"""
        try:
            workflows = workflow_registry.get_all_workflows()
            
            for workflow_id, workflow_config in workflows.items():
                self.workflow_combo.addItem(workflow_config.name, workflow_id)
            
            # Initialize with first workflow if available
            if self.workflow_combo.count() > 0:
                self.workflow_combo.setCurrentIndex(0)
                self.emit_selection_changed()
                
        except Exception as e:
            print(f"Error loading workflows: {str(e)}")
    
    def emit_selection_changed(self):
        """Emit selection changed signal with workflow configuration"""
        workflow_id = self.workflow_combo.currentData()
        
        if workflow_id:
            try:
                workflow_config = workflow_registry.get_workflow(workflow_id)
                self.current_workflow_config = workflow_config.to_dict()
                
                # Update description
                self.description_label.setText(workflow_config.description)
                
                # Emit signal with config
                self.selection_changed.emit(workflow_id, self.current_workflow_config)
                
            except Exception as e:
                print(f"Error loading workflow config: {str(e)}")
                self.current_workflow_config = {}
                self.selection_changed.emit(workflow_id, {})
    
    def get_workflow_id(self) -> str:
        """Get selected workflow ID"""
        return self.workflow_combo.currentData() or ""
    
    def get_workflow_name(self) -> str:
        """Get selected workflow display name"""
        return self.workflow_combo.currentText()
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get current workflow configuration"""
        return self.current_workflow_config.copy()
    
    def is_selection_valid(self) -> bool:
        """Check if a workflow is selected"""
        return bool(self.get_workflow_id())