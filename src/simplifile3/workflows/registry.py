# simplifile3/workflows/registry.py - Workflow registry for simplifile3
from typing import Dict, Any, List, Type
from abc import ABC


class WorkflowConfig:
    """Configuration for a single workflow"""
    
    def __init__(self, workflow_id: str, name: str, description: str, 
                 input_type: str, required_files: List[Dict[str, str]],
                 supported_counties: List[str], workflow_class: Type = None):
        self.workflow_id = workflow_id
        self.name = name
        self.description = description
        self.input_type = input_type  # "pdf_stacks", "directory", "variable_pdf"
        self.required_files = required_files
        self.supported_counties = supported_counties
        self.workflow_class = workflow_class
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI consumption"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "input_type": self.input_type,
            "required_files": self.required_files,
            "supported_counties": self.supported_counties
        }


class WorkflowRegistry:
    """Central registry for all available workflows"""
    
    def __init__(self):
        self._workflows: Dict[str, WorkflowConfig] = {}
        self._initialize_workflows()
    
    def _initialize_workflows(self):
        """Initialize all available workflows"""
        
        # BEA-HOR-COUNTYS-DEEDBACK workflow
        self.register_workflow(WorkflowConfig(
            workflow_id="BEA-HOR-COUNTYS-DEEDBACK",
            name="BEA-HOR-COUNTYS-DEEDBACK",
            description='<a href="https://github.com/dunncw/king_cunningham_code/blob/dev/task/simplifile/workflows/BEA-HOR-COUNTYS-DEEDBACK/BEA-HOR-COUNTYS-DEEDBACK-workflow-spec.md">BEA-HOR-COUNTYS-DEEDBACK SPEC</a>',
            input_type="variable_pdf",
            required_files=[
                {
                    "key": "excel",
                    "label": "Excel File",
                    "filter": "Excel Files (*.xlsx *.xls)",
                    "type": "file"
                },
                {
                    "key": "deed_stack",
                    "label": "Deed Stack PDF", 
                    "filter": "PDF Files (*.pdf)",
                    "type": "file"
                }
            ],
            supported_counties=["SCCP49", "SCCY4G"],  # Horry and Beaufort
            workflow_class=None  # Will be loaded dynamically
        ))
        
        # Future workflows will be added here as we migrate from simplifile2
    
    def register_workflow(self, workflow_config: WorkflowConfig):
        """Register a new workflow"""
        self._workflows[workflow_config.workflow_id] = workflow_config
    
    def get_workflow(self, workflow_id: str) -> WorkflowConfig:
        """Get workflow configuration by ID"""
        if workflow_id not in self._workflows:
            raise ValueError(f"Unknown workflow: {workflow_id}")
        return self._workflows[workflow_id]
    
    def get_all_workflows(self) -> Dict[str, WorkflowConfig]:
        """Get all available workflows"""
        return self._workflows.copy()
    
    def get_workflows_for_county(self, county_id: str) -> Dict[str, WorkflowConfig]:
        """Get workflows that support a specific county"""
        return {
            wf_id: config for wf_id, config in self._workflows.items()
            if county_id in config.supported_counties
        }
    
    def is_workflow_supported(self, workflow_id: str) -> bool:
        """Check if a workflow is supported"""
        return workflow_id in self._workflows
    
    def get_workflow_display_name(self, workflow_id: str) -> str:
        """Get display name for a workflow"""
        if workflow_id in self._workflows:
            return self._workflows[workflow_id].name
        return f"Unknown Workflow ({workflow_id})"


# Global registry instance
workflow_registry = WorkflowRegistry()