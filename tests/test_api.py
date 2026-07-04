import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from app.main import app
from app.api.proposal import get_proposal_service
from app.services.proposal_service import ProposalServiceError
from app.schemas.response import ProposalResponse

# Initialize FastAPI TestClient
client = TestClient(app)

@pytest.fixture
def mock_proposal_service():
    """
    Override the ProposalService FastAPI dependency with an AsyncMock.
    """
    mock_service = AsyncMock()
    app.dependency_overrides[get_proposal_service] = lambda: mock_service
    yield mock_service
    # Clear overrides after test run
    app.dependency_overrides.clear()

def test_api_success(mock_proposal_service):
    """
    1. Successful proposal generation.
    Verifies HTTP 200, schema match, and correct response fields.
    """
    expected_response = ProposalResponse(
        success=True,
        message="Proposal generated successfully.",
        proposal_id="PP-20260704-0001",
        status="completed",
        quality_score=95,
        execution_time="5.4 seconds",
        document_name="Proposal_20260704_153000.docx",
        document_path="generated_docs/Proposal_20260704_153000.docx",
        execution_plan=["Analyze requirements", "Generate Executive Summary", "Generate DOCX"]
    )
    mock_proposal_service.generate_proposal.return_value = expected_response
    
    payload = {
        "request": "Create a proposal for a Hospital Management System with a budget under ₹30 lakhs.",
        "client_name": "City Hospital",
        "company_name": "Pilot Tech"
    }
    
    response = client.post("/api/v1/proposals", json=payload)
    
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["proposal_id"] == "PP-20260704-0001"
    assert json_data["quality_score"] == 95
    assert json_data["execution_time"] == "5.4 seconds"
    assert json_data["document_name"] == "Proposal_20260704_153000.docx"
    assert "Analyze requirements" in json_data["execution_plan"]
    mock_proposal_service.generate_proposal.assert_called_once()

def test_api_invalid_payload():
    """
    2. Invalid request payload.
    Verifies that fields violating Pydantic validations (too short, empty) raise HTTP 422.
    """
    # Request text too short (less than 10 chars)
    payload = {"request": "Too short"}
    response = client.post("/api/v1/proposals", json=payload)
    assert response.status_code == 422
    
    # Request text contains only whitespace
    payload = {"request": "       "}
    response = client.post("/api/v1/proposals", json=payload)
    assert response.status_code == 422

def test_api_planner_failure(mock_proposal_service):
    """
    3. Planner failure.
    Verifies that a service exception in the planner node maps to HTTP 500 and ErrorResponse.
    """
    mock_proposal_service.generate_proposal.side_effect = ProposalServiceError(
        message="Workflow execution failed: Planner Node Exception: Rate limit exceeded",
        error_code="WORKFLOW_EXECUTION_FAILED"
    )
    
    payload = {"request": "Create a proposal for Hospital Software."}
    response = client.post("/api/v1/proposals", json=payload)
    
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "WORKFLOW_EXECUTION_FAILED"
    assert json_data["error_type"] == "ProposalServiceError"
    assert "Planner Node Exception" in json_data["message"]

def test_api_executor_failure(mock_proposal_service):
    """
    4. Executor failure.
    Verifies that a service exception in the executor node maps to HTTP 500 and ErrorResponse.
    """
    mock_proposal_service.generate_proposal.side_effect = ProposalServiceError(
        message="Workflow execution failed: Executor Node Exception: Service Timeout",
        error_code="WORKFLOW_EXECUTION_FAILED"
    )
    
    payload = {"request": "Create a proposal for Hospital Software."}
    response = client.post("/api/v1/proposals", json=payload)
    
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "WORKFLOW_EXECUTION_FAILED"
    assert "Executor Node Exception" in json_data["message"]

def test_api_reflection_failure(mock_proposal_service):
    """
    5. Reflection failure.
    Verifies that a service exception in the reflection node maps to HTTP 500 and ErrorResponse.
    """
    mock_proposal_service.generate_proposal.side_effect = ProposalServiceError(
        message="Workflow execution failed: Reflection Node Exception: JSON parse error",
        error_code="WORKFLOW_EXECUTION_FAILED"
    )
    
    payload = {"request": "Create a proposal for Hospital Software."}
    response = client.post("/api/v1/proposals", json=payload)
    
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "WORKFLOW_EXECUTION_FAILED"
    assert "Reflection Node Exception" in json_data["message"]

def test_api_docx_failure(mock_proposal_service):
    """
    6. Document generation failure.
    Verifies that a file write or format exception maps to HTTP 500 and ErrorResponse.
    """
    mock_proposal_service.generate_proposal.side_effect = ProposalServiceError(
        message="Document generation failed: Permission denied to write file",
        error_code="DOCUMENT_GENERATION_FAILED"
    )
    
    payload = {"request": "Create a proposal for Hospital Software."}
    response = client.post("/api/v1/proposals", json=payload)
    
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "DOCUMENT_GENERATION_FAILED"
    assert "Document generation failed" in json_data["message"]

def test_api_unexpected_exception(mock_proposal_service):
    """
    7. Unexpected exception.
    Verifies that unhandled runtime exceptions are safely caught and return HTTP 500.
    """
    mock_proposal_service.generate_proposal.side_effect = Exception("Fatal database disconnection error")
    
    payload = {"request": "Create a proposal for Hospital Software."}
    response = client.post("/api/v1/proposals", json=payload)
    
    assert response.status_code == 500
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error_code"] == "UNEXPECTED_SYSTEM_FAILURE"
    assert json_data["error_type"] == "Exception"
    assert "unexpected system failure" in json_data["message"]
