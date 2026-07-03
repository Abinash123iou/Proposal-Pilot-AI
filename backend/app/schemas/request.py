from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class PriorityEnum(str, Enum):
    """
    Priority levels for proposal generation tasks.
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class OutputFormatEnum(str, Enum):
    """
    Supported export formats for generated documents.
    """
    DOCX = "docx"

class ProposalRequest(BaseModel):
    """
    Schema validating the input payload for generating a business proposal.
    """
    request: str = Field(
        ...,
        description="The natural language business request detailing requirements",
        json_schema_extra={
            "example": "Create a proposal for a Hospital Management System with a budget under ₹30 lakhs."
        }
    )
    document_type: str = Field(
        default="proposal",
        description="The type of document to generate (e.g. proposal, tender)",
        json_schema_extra={"example": "proposal"}
    )
    client_name: Optional[str] = Field(
        default=None,
        description="Name of the client receiving the proposal",
        json_schema_extra={"example": "ABC Hospitals"}
    )
    company_name: Optional[str] = Field(
        default=None,
        description="Name of the service provider generating the proposal",
        json_schema_extra={"example": "ProposalPilot AI"}
    )
    project_name: Optional[str] = Field(
        default=None,
        description="The name of the target project",
        json_schema_extra={"example": "Hospital Management System"}
    )
    priority: PriorityEnum = Field(
        default=PriorityEnum.MEDIUM,
        description="Priority level of the proposal generation request"
    )
    language: str = Field(
        default="English",
        description="Target language for the generated proposal text",
        json_schema_extra={"example": "English"}
    )
    output_format: OutputFormatEnum = Field(
        default=OutputFormatEnum.DOCX,
        description="Export format file extension"
    )
    include_budget: bool = Field(
        default=True,
        description="Whether to include budget estimations in the proposal"
    )
    include_timeline: bool = Field(
        default=True,
        description="Whether to include project timeline and schedules"
    )
    include_risks: bool = Field(
        default=True,
        description="Whether to include project risk assessments"
    )
    include_assumptions: bool = Field(
        default=True,
        description="Whether to include proposal project assumptions"
    )

    @field_validator("request", mode="before")
    @classmethod
    def validate_request_field(cls, value: str) -> str:
        """
        Ensures the request string is a valid string, trims leading/trailing
        whitespace, and validates that it remains within bounds.
        """
        if not isinstance(value, str):
            raise ValueError("request must be a string")
        
        stripped = value.strip()
        
        if not stripped:
            raise ValueError("request cannot be empty or contain only whitespace")
            
        if len(stripped) < 10:
            raise ValueError("request must be at least 10 characters long")
            
        if len(stripped) > 5000:
            raise ValueError("request must be at most 5000 characters long")
            
        return stripped

    @field_validator("client_name", "company_name", "project_name", "document_type", "language", mode="before")
    @classmethod
    def strip_string_fields(cls, value: Optional[str]) -> Optional[str]:
        """
        Automatically strips leading and trailing whitespace from string fields if provided.
        """
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Field must be a string")
        stripped = value.strip()
        return stripped if stripped else None
