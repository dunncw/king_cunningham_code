from .bea_hor_deedback import BeaHorDeedbackWorkflow
from .horry_mtg_fcl import HorryMTGFCLWorkflow
from .beaufort_mtg_fcl import BeaufortMTGFCLWorkflow
from .horry_hoa_fcl import HorryHOAFCLWorkflow
from .fulton_deedbacks import FultonDeedbacksWorkflow
from .fulton_mtg_fcl import FultonMTGFCLWorkflow

# Registry of all workflows
WORKFLOWS = {
    "BEA_HOR_DEEDBACK": BeaHorDeedbackWorkflow,
    "HORRY_MTG_FCL": HorryMTGFCLWorkflow,
    "BEAUFORT_MTG_FCL": BeaufortMTGFCLWorkflow,
    "HORRY_HOA_FCL": HorryHOAFCLWorkflow,
    "FULTON_DEEDBACKS": FultonDeedbacksWorkflow,
    "FULTON_MTG_FCL": FultonMTGFCLWorkflow,
}

def get_workflow(workflow_id: str):
    """Get workflow class by ID."""
    if workflow_id not in WORKFLOWS:
        raise ValueError(f"Unknown workflow: {workflow_id}")
    return WORKFLOWS[workflow_id]

def get_all_workflows():
    """Get all available workflows with docs URLs."""
    return {
        workflow_id: {
            "name": workflow_id,  # Use ID as display name
            "docs_url": cls.docs_url if hasattr(cls, 'docs_url') else ""
        }
        for workflow_id, cls in WORKFLOWS.items()
    }