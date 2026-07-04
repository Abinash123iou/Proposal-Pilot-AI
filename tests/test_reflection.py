import pytest
from unittest.mock import AsyncMock, patch
from app.agents.state import AgentState
from app.agents.reflection import reflection_node
from app.llm.llm_service import LLMTimeoutException

@pytest.fixture
def base_state() -> AgentState:
    """
    Returns a valid AgentState with a complete proposal.
    """
    return {
        "request": "Create a proposal for a Hospital Management System with a budget under ₹30 lakhs.",
        "planner_output": {},
        "execution_plan": [],
        "current_task": None,
        "completed_tasks": [],
        "generated_sections": {
            "Executive Summary": "This is a comprehensive executive summary for the Hospital Management System. It describes the goals, background, and provider expertise.",
            "Scope": "The scope of the project includes patient management, doctor scheduling, billing, and pharmacy modules. All features will be web-based.",
            "Timeline": "The project will be completed in 6 months, split into requirements analysis, development, testing, and deployment phases.",
            "Budget": "The total estimated budget for the project is ₹25 lakhs, covering development, deployment, support, and licenses.",
            "Risks": "Key risks include data security breaches, system integration delays, and change management challenges. Mitigations are planned.",
            "Assumptions": "Assumptions include client team availability, continuous server power supply, and standard browser support.",
            "Conclusion": "In conclusion, this project will modernise the hospital's operations, improve efficiency, and reduce overall billing errors."
        },
        "reflection_result": None,
        "document_path": None,
        "status": "executed",
        "metadata": {},
        "errors": [],
        "quality_score": 0,
        "review_status": "FAIL",
        "regenerated_sections": []
    }

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_pass(mock_llm, base_state):
    """
    1. Complete proposal (PASS scenario).
    Verifies that a valid and complete proposal receives a PASS status and high score.
    """
    mock_llm.generate_json = AsyncMock(return_value={
        "quality_score": 95,
        "overall_status": "PASS",
        "missing_sections": [],
        "duplicate_sections": [],
        "warnings": [],
        "recommendations": [],
        "regeneration_required": False,
        "sections": []
    })

    result_state = await reflection_node(base_state)
    
    assert result_state["status"] == "reflected"
    assert result_state["review_status"] == "PASS"
    assert result_state["quality_score"] == 95
    assert len(result_state["errors"]) == 0
    assert result_state["reflection_result"]["overall_status"] == "PASS"
    mock_llm.generate_json.assert_called_once()

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_missing_section(mock_llm, base_state):
    """
    2. Missing section scenario.
    Verifies that a proposal missing a mandatory section (e.g. Risks) is marked as FAIL.
    """
    # Remove Risks from generated sections
    del base_state["generated_sections"]["Risks"]

    mock_llm.generate_json = AsyncMock(return_value={
        "quality_score": 60,
        "overall_status": "FAIL",
        "missing_sections": ["Risks"],
        "duplicate_sections": [],
        "warnings": ["Risks section is missing."],
        "recommendations": ["Generate the Risks section."],
        "regeneration_required": False,
        "sections": []
    })

    result_state = await reflection_node(base_state)
    
    assert result_state["review_status"] == "FAIL"
    assert "Risks" in result_state["reflection_result"]["missing_sections"]
    assert len(result_state["errors"]) == 0

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_duplicate_content(mock_llm, base_state):
    """
    3. Duplicate content scenario.
    Verifies that duplicate content between sections is detected and fails validation.
    """
    # Make Scope and Assumptions identical
    duplicate_text = "This is a duplicate text shared across multiple sections of the proposal document."
    base_state["generated_sections"]["Scope"] = duplicate_text
    base_state["generated_sections"]["Assumptions"] = duplicate_text

    mock_llm.generate_json = AsyncMock(return_value={
        "quality_score": 50,
        "overall_status": "FAIL",
        "missing_sections": [],
        "duplicate_sections": ["Scope", "Assumptions"],
        "warnings": ["Duplicate content detected between Scope and Assumptions."],
        "recommendations": ["Make the Scope and Assumptions sections unique."],
        "regeneration_required": False,
        "sections": []
    })

    result_state = await reflection_node(base_state)
    
    assert result_state["review_status"] == "FAIL"
    assert "Scope" in result_state["reflection_result"]["duplicate_sections"]
    assert len(result_state["errors"]) == 0

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_empty_section(mock_llm, base_state):
    """
    4. Empty section scenario.
    Verifies that an empty section is caught by programmatic checks and triggers regeneration.
    """
    base_state["generated_sections"]["Budget"] = ""

    mock_llm.generate_json = AsyncMock(return_value={
        "quality_score": 70,
        "overall_status": "FAIL",
        "missing_sections": [],
        "duplicate_sections": [],
        "warnings": ["Budget section is empty."],
        "recommendations": ["Regenerate Budget section."],
        "regeneration_required": True,
        "sections": ["Budget"]
    })
    
    regenerated_text = "This is the newly regenerated Budget section text that satisfies the requirements and exceeds fifty characters."
    mock_llm.generate_text = AsyncMock(return_value=regenerated_text)

    result_state = await reflection_node(base_state)
    
    assert result_state["generated_sections"]["Budget"] == regenerated_text
    assert "Budget" in result_state["regenerated_sections"]
    assert result_state["review_status"] == "PASS" # upgraded after regeneration
    assert result_state["quality_score"] >= 85

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_low_quality_section(mock_llm, base_state):
    """
    5. Low-quality section scenario.
    Verifies that a too-short section (<50 chars) is programmatically detected and regenerated.
    """
    base_state["generated_sections"]["Timeline"] = "Too short."

    mock_llm.generate_json = AsyncMock(return_value={
        "quality_score": 75,
        "overall_status": "FAIL",
        "missing_sections": [],
        "duplicate_sections": [],
        "warnings": ["Timeline section is too short."],
        "recommendations": ["Provide detailed timeline."],
        "regeneration_required": True,
        "sections": ["Timeline"]
    })
    
    regenerated_text = "This is the newly regenerated Timeline section text which is now very detailed, clear, and exceeds the minimum length."
    mock_llm.generate_text = AsyncMock(return_value=regenerated_text)

    result_state = await reflection_node(base_state)
    
    assert result_state["generated_sections"]["Timeline"] == regenerated_text
    assert "Timeline" in result_state["regenerated_sections"]
    assert result_state["review_status"] == "PASS"

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_regeneration_workflow(mock_llm, base_state):
    """
    6. Regeneration workflow scenario.
    Verifies that multiple sections needing regeneration are updated properly.
    """
    mock_llm.generate_json = AsyncMock(return_value={
        "quality_score": 55,
        "overall_status": "FAIL",
        "missing_sections": [],
        "duplicate_sections": [],
        "warnings": ["Budget is unrealistic.", "Timeline lacks detail."],
        "recommendations": ["Rewrite budget and timeline."],
        "regeneration_required": True,
        "sections": ["Budget", "Timeline"]
    })
    
    def generate_text_side_effect(prompt, system_instruction):
        if "proposal section: 'Budget'" in prompt:
            return "This is the new regenerated Budget section content that is realistic and well estimated."
        else:
            return "This is the new regenerated Timeline section content with a fully detailed schedule breakdown."
            
    mock_llm.generate_text = AsyncMock(side_effect=generate_text_side_effect)

    result_state = await reflection_node(base_state)
    
    assert "Budget" in result_state["regenerated_sections"]
    assert "Timeline" in result_state["regenerated_sections"]
    assert "realistic" in result_state["generated_sections"]["Budget"]
    assert "fully detailed" in result_state["generated_sections"]["Timeline"]
    assert result_state["review_status"] == "PASS"

@pytest.mark.anyio
@patch("app.agents.reflection.llm_service")
async def test_reflection_llm_timeout(mock_llm, base_state):
    """
    7. LLM timeout handling scenario.
    Verifies that LLM timeouts are caught, logged, and registered in state without crashing.
    """
    mock_llm.generate_json = AsyncMock(side_effect=LLMTimeoutException("Groq API request timed out after retries."))

    result_state = await reflection_node(base_state)
    
    assert result_state["status"] == "failed"
    assert len(result_state["errors"]) > 0
    assert "timed out" in result_state["errors"][0]
