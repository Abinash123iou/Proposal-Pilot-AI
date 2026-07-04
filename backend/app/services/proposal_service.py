import time
import threading
from datetime import datetime
from app.core.logger import logger
from app.schemas.request import ProposalRequest
from app.schemas.response import ProposalResponse
from app.services.proposal_manager import ProposalManager

# Thread-safe proposal sequence counter for formatting ID (e.g. PP-20260704-0001)
_proposal_counter = 0
_counter_lock = threading.Lock()

def _next_proposal_id() -> str:
    global _proposal_counter
    with _counter_lock:
        _proposal_counter += 1
        curr = _proposal_counter
    date_str = datetime.now().strftime("%Y%m%d")
    return f"PP-{date_str}-{curr:04d}"

class ProposalServiceError(Exception):
    """
    Custom exception raised for orchestrator and system errors inside the proposal service.
    """
    def __init__(self, message: str, error_code: str = "PROPOSAL_GENERATION_FAILED"):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

class ProposalService:
    """
    Service Layer wrapper handling client-side requests, measuring generation metrics,
    and classifying workflow/document errors.
    """
    def __init__(self, proposal_manager: ProposalManager):
        self.proposal_manager = proposal_manager

    async def generate_proposal(self, request_payload: ProposalRequest) -> ProposalResponse:
        logger.info("Request received for proposal generation")
        start_time = time.perf_counter()
        proposal_id = _next_proposal_id()
        
        try:
            logger.info(f"Assigned Proposal ID: {proposal_id}")
            result = await self.proposal_manager.execute_pipeline(request_payload)
            
            final_state = result["workflow_state"]
            document_result = result["document_result"]
            
            elapsed = time.perf_counter() - start_time
            execution_time_str = f"{elapsed:.1f} seconds"
            
            logger.info(f"Workflow completed successfully. Execution time: {execution_time_str}")
            logger.info(f"Document generated: {document_result['filename']} (Size: {document_result['file_size_bytes']} bytes)")
            
            tasks = [t.get("task", "") for t in final_state.get("execution_plan", [])]
            
            return ProposalResponse(
                success=True,
                message="Proposal generated successfully.",
                proposal_id=proposal_id,
                status="completed",
                quality_score=final_state.get("quality_score", 0),
                execution_time=execution_time_str,
                document_name=document_result["filename"],
                document_path=document_result["document_path"],
                execution_plan=tasks
            )
            
        except ValueError as e:
            err_msg = str(e)
            logger.error(f"Proposal ID {proposal_id} generation failed: {err_msg}")
            
            # Map sub-errors to allow the API to return exact class names and descriptions
            if "Workflow execution failed" in err_msg:
                error_code = "WORKFLOW_EXECUTION_FAILED"
            elif "Document generation failed" in err_msg:
                error_code = "DOCUMENT_GENERATION_FAILED"
            else:
                error_code = "PROPOSAL_PIPELINE_FAILED"
                
            raise ProposalServiceError(err_msg, error_code=error_code)
            
        except Exception as e:
            err_msg = f"Unexpected exception in proposal service: {str(e)}"
            logger.error(f"Proposal ID {proposal_id} generation failed: {err_msg}")
            raise ProposalServiceError(err_msg, error_code="UNEXPECTED_SYSTEM_FAILURE")
