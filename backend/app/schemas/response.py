from pydantic import BaseModel, Field

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
