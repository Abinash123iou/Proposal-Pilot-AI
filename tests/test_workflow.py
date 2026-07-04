import pytest
from unittest.mock import AsyncMock, patch
from app.workflow import ProposalWorkflow, compiled_workflow

@pytest.mark.anyio
@patch("app.workflow.nodes.planner_node")
@patch("app.workflow.nodes.executor_node")
@patch("app.workflow.nodes.reflection_node")
async def test_workflow_success(mock_reflection, mock_executor, mock_planner):
    """
    1. Successful workflow execution (full run).
    Verifies that the state passes through all nodes on a normal run.
    """
    # Configure mock planner
    async def mock_planner_side_effect(state):
        state["execution_plan"] = [{"task": "Draft Introduction", "status": "pending"}]
        state["planner_output"] = {"plan_id": 123}
        state["status"] = "planned"
        return state
    mock_planner.side_effect = mock_planner_side_effect

    # Configure mock executor (it will run once and complete the task)
    async def mock_executor_side_effect(state):
        state["generated_sections"] = {"Introduction": "This is a detailed intro section."}
        state["completed_tasks"] = ["Draft Introduction"]
        state["execution_plan"][0]["status"] = "completed"
        state["status"] = "executed"
        return state
    mock_executor.side_effect = mock_executor_side_effect

    # Configure mock reflection
    async def mock_reflection_side_effect(state):
        state["quality_score"] = 92
        state["reflection_result"] = {"overall_status": "PASS"}
        state["review_status"] = "PASS"
        state["status"] = "reflected"
        return state
    mock_reflection.side_effect = mock_reflection_side_effect

    # Run the workflow
    result = await ProposalWorkflow.run("Create a new software project proposal.")

    # Asserts
    assert result["status"] == "reflected"
    assert result["review_status"] == "PASS"
    assert result["quality_score"] == 92
    assert "Introduction" in result["generated_sections"]
    assert len(result["errors"]) == 0
    mock_planner.assert_called_once()
    mock_executor.assert_called_once()
    mock_reflection.assert_called_once()

@pytest.mark.anyio
@patch("app.workflow.nodes.planner_node")
@patch("app.workflow.nodes.executor_node")
@patch("app.workflow.nodes.reflection_node")
async def test_workflow_planner_failure(mock_reflection, mock_executor, mock_planner):
    """
    2. Planner failure scenario.
    Verifies that if the planner throws an exception, the exception is caught,
    the workflow is marked failed, and subsequent nodes are skipped.
    """
    mock_planner.side_effect = Exception("Planner LLM API Outage")

    result = await ProposalWorkflow.run("Create proposal.")

    # Asserts
    assert result["status"] == "failed"
    assert len(result["errors"]) > 0
    assert "Planner Node Exception: Planner LLM API Outage" in result["errors"][0]
    
    # Executor and Reflection should either not be called or skipped
    mock_executor.assert_not_called()
    mock_reflection.assert_not_called()

@pytest.mark.anyio
@patch("app.workflow.nodes.planner_node")
@patch("app.workflow.nodes.executor_node")
@patch("app.workflow.nodes.reflection_node")
async def test_workflow_executor_failure(mock_reflection, mock_executor, mock_planner):
    """
    3. Executor failure scenario.
    Verifies that if the executor fails, reflection skips execution and errors are registered.
    """
    # Planner succeeds
    async def mock_planner_side_effect(state):
        state["execution_plan"] = [{"task": "Task 1", "status": "pending"}]
        return state
    mock_planner.side_effect = mock_planner_side_effect

    # Executor raises exception
    mock_executor.side_effect = Exception("Executor Timeout")

    result = await ProposalWorkflow.run("Create proposal.")

    # Asserts
    assert result["status"] == "failed"
    assert len(result["errors"]) > 0
    assert "Executor Node Exception: Executor Timeout" in result["errors"][0]
    
    # Reflection should not run because status is failed
    mock_reflection.assert_not_called()

@pytest.mark.anyio
@patch("app.workflow.nodes.planner_node")
@patch("app.workflow.nodes.executor_node")
@patch("app.workflow.nodes.reflection_node")
async def test_workflow_reflection_failure(mock_reflection, mock_executor, mock_planner):
    """
    4. Reflection failure scenario.
    Verifies that reflection errors are caught and recorded.
    """
    # Planner succeeds
    async def mock_planner_side_effect(state):
        state["execution_plan"] = []
        return state
    mock_planner.side_effect = mock_planner_side_effect

    # Executor succeeds
    async def mock_executor_side_effect(state):
        return state
    mock_executor.side_effect = mock_executor_side_effect

    # Reflection fails
    mock_reflection.side_effect = Exception("Reflection JSON Invalid")

    result = await ProposalWorkflow.run("Create proposal.")

    # Asserts
    assert result["status"] == "failed"
    assert len(result["errors"]) > 0
    assert "Reflection Node Exception: Reflection JSON Invalid" in result["errors"][0]

@pytest.mark.anyio
async def test_workflow_empty_request():
    """
    5. Empty request scenario.
    Verifies that an empty or whitespace-only request is blocked instantly.
    """
    result = await ProposalWorkflow.run("   ")
    assert result["status"] == "failed"
    assert "Request text cannot be empty" in result["errors"][0]

@pytest.mark.anyio
async def test_workflow_invalid_agent_state():
    """
    6. Invalid AgentState scenario.
    Verifies that passing a state of type other than dict to compiled_workflow raises an Exception.
    """
    with pytest.raises(Exception):
        await compiled_workflow.ainvoke("not a dictionary")
