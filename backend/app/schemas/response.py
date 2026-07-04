from datetime import datetime, timezone
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field

def get_utc_timestamp() -> str:
    """
    Generate the current UTC timestamp in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()

class HealthResponse(BaseModel):
    """
    Schema for Health Check API response.
    """
    status: str = Field(..., description="Application health status", json_schema_extra={"example": "healthy"})
    service: str = Field(..., description="Name of the service", json_schema_extra={"example": "ProposalPilot AI"})
    version: str = Field(..., description="Service version", json_schema_extra={"example": "1.0.0"})
    environment: str = Field(..., description="Deployment environment", json_schema_extra={"example": "development"})
    timestamp: str = Field(..., description="Current UTC timestamp in ISO 8601 format", json_schema_extra={"example": "2026-07-03T17:15:37Z"})
    uptime: str = Field(..., description="Service uptime since startup", json_schema_extra={"example": "0 days, 0 hours, 5 minutes"})
    message: str = Field(..., description="General health message", json_schema_extra={"example": "Application is running successfully."})

class BaseResponse(BaseModel):
    """
    Common fields returned in all API responses.
    """
    success: bool = Field(..., description="Indicates if the operation succeeded", json_schema_extra={"example": True})
    message: str = Field(..., description="A human-readable descriptive response message", json_schema_extra={"example": "Operation succeeded."})
    timestamp: str = Field(
        default_factory=get_utc_timestamp,
        description="ISO 8601 UTC timestamp of the response transaction"
    )

class ProposalResponse(BaseResponse):
    """
    Response returned on successful autonomous proposal generation.
    """
    proposal_id: str = Field(..., description="Unique generated proposal identifier", json_schema_extra={"example": "PP-20260703-0001"})
    document_name: str = Field(..., description="Name of the generated Word document file", json_schema_extra={"example": "Hospital_Proposal.docx"})
    document_path: str = Field(..., description="Path to the generated document file on the server", json_schema_extra={"example": "generated_docs/Hospital_Proposal.docx"})
    execution_plan: List[str] = Field(
        ...,
        description="List of autonomous planner tasks executed",
        json_schema_extra={
            "example": [
                "Analyze requirements",
                "Generate executive summary",
                "Generate project scope",
                "Generate timeline",
                "Generate budget",
                "Generate risks",
                "Generate DOCX"
            ]
        }
    )
    execution_time: str = Field(..., description="Time duration taken to run agents and export proposal", json_schema_extra={"example": "8.4 seconds"})
    status: str = Field(default="completed", description="Execution status", json_schema_extra={"example": "completed"})
    quality_score: Optional[int] = Field(default=None, description="The QA quality score evaluated for this proposal", json_schema_extra={"example": 95})

class ErrorResponse(BaseResponse):
    """
    Standard response payload returned for runtime, network, or server failures.
    """
    success: bool = Field(default=False, description="Always False for error responses", json_schema_extra={"example": False})
    error_code: str = Field(..., description="Specific application-level error classification code", json_schema_extra={"example": "GROQ_TIMEOUT"})
    error_type: str = Field(..., description="Underlying exception class name", json_schema_extra={"example": "TimeoutException"})
    details: Optional[Union[List[Any], dict[str, Any]]] = Field(default=None, description="Detailed contextual debugger messages")

class ValidationErrorResponse(BaseResponse):
    """
    Specialized response structure returned for HTTP 422 request validation errors.
    """
    success: bool = Field(default=False, description="Always False for validation errors", json_schema_extra={"example": False})
    validation_errors: List[dict[str, Any]] = Field(
        ...,
        description="List of Pydantic validation failure points",
        json_schema_extra={
            "example": [
                {
                    "loc": ["body", "request"],
                    "msg": "Field required",
                    "type": "value_error.missing"
                }
            ]
        }
    )
