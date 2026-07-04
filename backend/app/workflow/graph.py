from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.workflow.constants import PLANNER_NODE, EXECUTOR_NODE, REFLECTION_NODE
from app.workflow.nodes import wrapped_planner_node, wrapped_executor_node, wrapped_reflection_node

def should_continue(state: AgentState) -> str:
    """
    Determines if the executor has remaining tasks or if it should proceed to reflection.
    """
    if state.get("status") == "failed":
        return REFLECTION_NODE
        
    has_more_pending = any(t.get("status") == "pending" for t in state.get("execution_plan", []))
    if has_more_pending:
        return EXECUTOR_NODE
    return REFLECTION_NODE

# Construct the LangGraph StateGraph
builder = StateGraph(AgentState)

# Register workflow nodes
builder.add_node(PLANNER_NODE, wrapped_planner_node)
builder.add_node(EXECUTOR_NODE, wrapped_executor_node)
builder.add_node(REFLECTION_NODE, wrapped_reflection_node)

# Set the flow edges
builder.add_edge(START, PLANNER_NODE)
builder.add_edge(PLANNER_NODE, EXECUTOR_NODE)

# Add conditional task execution loop
builder.add_conditional_edges(
    EXECUTOR_NODE,
    should_continue,
    {
        EXECUTOR_NODE: EXECUTOR_NODE,
        REFLECTION_NODE: REFLECTION_NODE
    }
)

builder.add_edge(REFLECTION_NODE, END)

# Compile graph
compiled_workflow = builder.compile()
