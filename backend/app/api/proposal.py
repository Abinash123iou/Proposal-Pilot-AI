from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.schemas.request import ProposalRequest
from app.schemas.response import ProposalResponse, ErrorResponse
from app.document import DocxDocumentGenerator
from app.services import ProposalManager, ProposalService, ProposalServiceError

router = APIRouter(prefix="/api/v1", tags=["Proposals"])

def get_proposal_service() -> ProposalService:
    """
    Dependency injection factory that builds the complete business layer stack.
    """
    document_generator = DocxDocumentGenerator()
    proposal_manager = ProposalManager(document_generator=document_generator)
    return ProposalService(proposal_manager=proposal_manager)

@router.post(
    "/proposals",
    response_model=ProposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Autonomous Proposal",
    description=(
        "Triggers the full multi-agent orchestration pipeline: "
        "Planner -> Executor -> Reflection -> DOCX exporter. "
        "Returns generated proposal metadata and server document location."
    ),
    responses={
        200: {"model": ProposalResponse, "description": "Proposal generated and saved successfully"},
        500: {"model": ErrorResponse, "description": "Generation pipeline, LLM, or filesystem error"}
    }
)
async def generate_proposal(
    payload: ProposalRequest,
    service: ProposalService = Depends(get_proposal_service)
):
    """
    FastAPI endpoint exposing REST API for proposal generation.
    """
    try:
        response = await service.generate_proposal(payload)
        return response
    except ProposalServiceError as e:
        error_content = {
            "success": False,
            "message": f"Proposal generation failed: {e.message}",
            "error_code": e.error_code,
            "error_type": type(e).__name__,
            "details": None
        }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_content
        )
    except Exception as e:
        error_content = {
            "success": False,
            "message": f"An unexpected system failure occurred: {str(e)}",
            "error_code": "UNEXPECTED_SYSTEM_FAILURE",
            "error_type": type(e).__name__,
            "details": None
        }
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_content
        )
