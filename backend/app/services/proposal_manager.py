from typing import Dict, Any
from app.workflow import ProposalWorkflow
from app.document import DocumentGenerator
from app.schemas.request import ProposalRequest
from app.core.logger import logger

class ProposalManager:
    """
    Orchestration coordinator encapsulating the pipeline flow:
    Init AgentState -> Run LangGraph Workflow -> Generate Document.
    """
    def __init__(self, document_generator: DocumentGenerator):
        self.document_generator = document_generator

    async def execute_pipeline(self, request_payload: ProposalRequest) -> Dict[str, Any]:
        """
        Coordinates state setup, graph workflow execution, and export formatting.
        """
        # 1. Initialize AgentState from request parameters
        state = {
            "request": request_payload.request,
            "client_name": request_payload.client_name,
            "company_name": request_payload.company_name,
            "project_name": request_payload.project_name,
            "document_type": request_payload.document_type,
            "priority": request_payload.priority.value,
            "language": request_payload.language,
            "output_format": request_payload.output_format.value,
            "include_budget": request_payload.include_budget,
            "include_timeline": request_payload.include_timeline,
            "include_risks": request_payload.include_risks,
            "include_assumptions": request_payload.include_assumptions,
            
            # Orchestration placeholders
            "errors": [],
            "execution_plan": [],
            "generated_sections": {},
            "review_status": "pending",
            "quality_score": 0,
            "status": "started",
            "planner_output": {},
            "executor_output": {},
            "reflection_result": {},
            "completed_tasks": [],
            "section_regeneration_count": {}
        }
        
        # 2. Invoke workflow manager
        logger.info(f"Invoking Workflow Manager for request: '{request_payload.request[:100]}'")
        workflow_state = await ProposalWorkflow.run(request_payload.request, initial_state=state)
        
        # 3. Validate workflow execution result
        if workflow_state.get("status") == "failed" or workflow_state.get("errors"):
            errors = workflow_state.get("errors", ["Unknown workflow error occurred."])
            err_msg = f"Workflow execution failed: {'; '.join(errors)}"
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        # 4. Invoke Document Generator
        logger.info("Invoking Document Generator")
        doc_result = await self.document_generator.generate(workflow_state)
        
        if not doc_result.get("success"):
            errors = doc_result.get("errors", ["Unknown document generation error occurred."])
            err_msg = f"Document generation failed: {'; '.join(errors)}"
            logger.error(err_msg)
            raise ValueError(err_msg)
            
        return {
            "workflow_state": workflow_state,
            "document_result": doc_result
        }
