from app.llm import llm_service, PLANNER_SYSTEM_PROMPT, build_planner_prompt
from app.agents.state import AgentState
from app.core.logger import logger
from typing import Any, Dict

async def planner_node(state: AgentState) -> AgentState:
    """
    LangGraph node for planning proposal generation tasks.
    """
    logger.info("Planner Agent node execution started.")
    
    # Extract request elements
    request_str = state.get("request", "")
    metadata = state.get("metadata", {})
    client_name = metadata.get("client_name")
    company_name = metadata.get("company_name")
    project_name = metadata.get("project_name")
    document_type = metadata.get("document_type", "proposal")

    # Safeguard state lists/dicts
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []
    if "execution_plan" not in state or state["execution_plan"] is None:
        state["execution_plan"] = []

    # 1. Validation: Empty request prompt
    if not request_str or not request_str.strip():
        err_msg = "Planner Error: Initial request prompt is empty or contains only whitespace."
        logger.error(err_msg)
        state["errors"].append(err_msg)
        state["status"] = "failed"
        return state

    try:
        # 2. Build prompt
        prompt = build_planner_prompt(
            request=request_str,
            document_type=document_type,
            client_name=client_name,
            company_name=company_name,
            project_name=project_name
        )
        logger.info("Planner prompt built successfully.")

        # 3. Call LLM Service
        logger.info("Sending planning request to LLM Service.")
        response_dict = await llm_service.generate_json(
            prompt=prompt,
            system_instruction=PLANNER_SYSTEM_PROMPT
        )
        logger.info("Planner response received and parsed as JSON.")

        # 4. Extract and validate task list
        tasks = response_dict.get("tasks")
        if not tasks or not isinstance(tasks, list):
            # Fallback checks
            tasks = response_dict.get("execution_plan")
            if not tasks or not isinstance(tasks, list):
                raise ValueError("LLM response JSON is missing a valid 'tasks' or 'execution_plan' list.")

        # Clean/Format the execution plan
        execution_plan = []
        seen_tasks = set()
        for idx, task in enumerate(tasks):
            if isinstance(task, dict):
                task_name = task.get("task") or task.get("name")
            else:
                task_name = str(task)

            if not task_name or not task_name.strip():
                continue

            task_clean = task_name.strip()
            if task_clean.lower() in seen_tasks:
                logger.warning(f"Removing duplicate task from plan: '{task_clean}'")
                continue
            seen_tasks.add(task_clean.lower())

            execution_plan.append({
                "id": len(execution_plan) + 1,
                "task": task_clean,
                "status": "pending"
            })

        if not execution_plan:
            raise ValueError("No valid tasks could be extracted from LLM plan response.")

        # 5. Update shared state
        state["planner_output"] = response_dict
        state["execution_plan"] = execution_plan
        state["status"] = "planned"
        logger.info(f"Planner completed. Generated plan contains {len(execution_plan)} tasks.")

    except Exception as e:
        err_msg = f"Planner exception: {str(e)}"
        logger.exception(err_msg)
        state["errors"].append(err_msg)
        state["status"] = "failed"

    return state
