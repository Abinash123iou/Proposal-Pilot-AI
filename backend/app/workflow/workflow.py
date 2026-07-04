from typing import Dict, Any, Optional
from app.core.logger import logger
from app.agents.state import AgentState
from app.workflow.graph import compiled_workflow

class ProposalWorkflow:
    """
    Reusable interface to orchestrate and execute the proposal generation workflow.
    """
    
    @staticmethod
    async def run(request_text: str, initial_state: Optional[Dict[str, Any]] = None) -> AgentState:
        """
        Runs the compiled LangGraph workflow graph asynchronously.
        """
        logger.info("Workflow Started")
        
        # Initialize default state structure
        state: AgentState = {
            "request": request_text,
            "planner_output": {},
            "execution_plan": [],
            "current_task": None,
            "completed_tasks": [],
            "generated_sections": {},
            "reflection_result": None,
            "document_path": None,
            "status": "started",
            "metadata": {},
            "errors": [],
            "quality_score": 0,
            "review_status": "FAIL",
            "regenerated_sections": []
        }
        
        # Apply initial overrides if present
        if initial_state:
            state.update(initial_state)
            
        # Programmatic check for empty request
        if not request_text or not request_text.strip():
            err_msg = "Workflow Failed: Request text cannot be empty."
            logger.error(err_msg)
            state["errors"].append(err_msg)
            state["status"] = "failed"
            logger.info("Workflow Failed")
            return state
            
        try:
            # Execute compiled graph
            final_state = await compiled_workflow.ainvoke(state)
            
            # Check final status to report success/failure
            if final_state.get("status") == "failed" or final_state.get("errors"):
                logger.error("Workflow completed with errors.")
                logger.info("Workflow Failed")
            else:
                logger.info("Workflow Completed")
                
            return final_state
            
        except Exception as e:
            err_msg = f"Workflow Execution crashed: {str(e)}"
            logger.error(err_msg)
            state["errors"].append(err_msg)
            state["status"] = "failed"
            logger.info("Workflow Failed")
            return state
