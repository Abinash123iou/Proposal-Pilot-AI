from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    Shared state representation passed between LangGraph agent nodes.
    """
    request: str
    planner_output: Optional[Dict[str, Any]]
    execution_plan: List[Dict[str, Any]]
    current_task: Optional[str]
    completed_tasks: List[str]
    generated_sections: Dict[str, str]
    reflection_result: Optional[Dict[str, Any]]
    document_path: Optional[str]
    status: str
    metadata: Dict[str, Any]
    errors: List[str]
