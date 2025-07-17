# ui/components/county_workflow.py - County and workflow selector widget
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import pyqtSignal


class CountyWorkflowWidget(QGroupBox):
    """Widget for selecting county and workflow"""
    
    # Signals
    selection_changed = pyqtSignal(str, str)  # county_id, workflow_id
    
    def __init__(self):
        super().__init__("County - Workflow")
        self.init_ui()
        self.populate_counties()
    
    def init_ui(self):
        """Initialize the widget UI"""
        layout = QVBoxLayout()
        
        # County selection
        county_layout = QHBoxLayout()
        county_layout.addWidget(QLabel("County:"))
        
        self.county_combo = QComboBox()
        self.county_combo.currentTextChanged.connect(self.update_workflow_options)
        county_layout.addWidget(self.county_combo)
        
        layout.addLayout(county_layout)
        
        # Workflow selection
        workflow_layout = QHBoxLayout()
        workflow_layout.addWidget(QLabel("Workflow:"))
        
        self.workflow_combo = QComboBox()
        self.workflow_combo.currentTextChanged.connect(self.emit_selection_changed)
        workflow_layout.addWidget(self.workflow_combo)
        
        layout.addLayout(workflow_layout)
        self.setLayout(layout)
    
    def populate_counties(self):
        """Populate county dropdown from county config"""
        try:
            from ...core.county_config import get_available_counties
            
            counties = get_available_counties()
            
            for county_id, county_name in counties.items():
                self.county_combo.addItem(county_name, county_id)
            
            # Initialize workflows for first county
            if self.county_combo.count() > 0:
                self.update_workflow_options()
                
        except Exception as e:
            print(f"Error loading counties: {str(e)}")
    
    def update_workflow_options(self):
        """Update workflow dropdown based on selected county"""
        self.workflow_combo.clear()
        
        county_id = self.county_combo.currentData()
        if not county_id:
            return
        
        try:
            from ...workflows.fulton_fcl import FultonFCLWorkflow
            from ...core.county_config import get_county_config
            
            # For now, hardcode FCL workflow for Fulton County
            # TODO: Make this dynamic when we have more workflows
            if county_id == "GAC3TH":  # Fulton County
                self.workflow_combo.addItem("Foreclosure (FCL)", "fcl")
            
            # Emit selection changed after updating workflows
            self.emit_selection_changed()
                
        except Exception as e:
            print(f"Error loading workflows for {county_id}: {str(e)}")
    
    def emit_selection_changed(self):
        """Emit selection changed signal"""
        county_id = self.county_combo.currentData()
        workflow_id = self.workflow_combo.currentData()
        
        if county_id and workflow_id:
            self.selection_changed.emit(county_id, workflow_id)
    
    def get_county_id(self) -> str:
        """Get selected county ID"""
        return self.county_combo.currentData() or ""
    
    def get_workflow_id(self) -> str:
        """Get selected workflow ID"""
        return self.workflow_combo.currentData() or ""
    
    def get_county_name(self) -> str:
        """Get selected county display name"""
        return self.county_combo.currentText()
    
    def get_workflow_name(self) -> str:
        """Get selected workflow display name"""
        return self.workflow_combo.currentText()
    
    def is_selection_valid(self) -> bool:
        """Check if both county and workflow are selected"""
        return bool(self.get_county_id() and self.get_workflow_id())