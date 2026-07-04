import time
from app.core.logger import logger
from app.agents import planner_node, executor_node, reflection_node
from app.agents.state import AgentState

def validate_state(state: AgentState) -> None:
    """
    Validates that the incoming state matches requirements.
    """
    if not isinstance(state, dict):
        raise ValueError("Invalid shared state: AgentState must be a dictionary.")

async def wrapped_planner_node(state: AgentState) -> AgentState:
    """
    Wrapped Planner Node with execution timing, logging, and error boundaries.
    """
    validate_state(state)
    
    if state.get("status") == "failed":
        logger.warning("Workflow in failed state. Skipping Planner Node.")
        return state
        
    start_time = time.perf_counter()
    try:
        state = await planner_node(state)
        duration = time.perf_counter() - start_time
        logger.info(f"Planner Executed in {duration:.2f} seconds.")
    except Exception as e:
        duration = time.perf_counter() - start_time
        err_msg = f"Planner Node Exception: {str(e)}"
        logger.error(err_msg)
        if "errors" not in state or state["errors"] is None:
            state["errors"] = []
        state["errors"].append(err_msg)
        state["status"] = "failed"
        
    return state

async def wrapped_executor_node(state: AgentState) -> AgentState:
    """
    Wrapped Executor Node with execution timing, logging, and error boundaries.
    """
    validate_state(state)
    
    if state.get("status") == "failed":
        logger.warning("Workflow in failed state. Skipping Executor Node.")
        return state
        
    start_time = time.perf_counter()
    try:
        state = await executor_node(state)
        duration = time.perf_counter() - start_time
        logger.info(f"Executor Executed in {duration:.2f} seconds.")
    except Exception as e:
        duration = time.perf_counter() - start_time
        err_msg = f"Executor Node Exception: {str(e)}"
        logger.error(err_msg)
        if "errors" not in state or state["errors"] is None:
            state["errors"] = []
        state["errors"].append(err_msg)
        state["status"] = "failed"
        
    return state

async def wrapped_reflection_node(state: AgentState) -> AgentState:
    """
    Wrapped Reflection Node with execution timing, logging, and error boundaries.
    """
    validate_state(state)
    
    if state.get("status") == "failed":
        logger.warning("Workflow in failed state. Skipping Reflection Node.")
        return state
        
    start_time = time.perf_counter()
    try:
        state = await reflection_node(state)
        duration = time.perf_counter() - start_time
        logger.info(f"Reflection Executed in {duration:.2f} seconds.")
    except Exception as e:
        duration = time.perf_counter() - start_time
        err_msg = f"Reflection Node Exception: {str(e)}"
        logger.error(err_msg)
        if "errors" not in state or state["errors"] is None:
            state["errors"] = []
        state["errors"].append(err_msg)
        state["status"] = "failed"
        
    return state
