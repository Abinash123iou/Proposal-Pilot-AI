from app.llm import llm_service, EXECUTOR_SYSTEM_PROMPT, build_executor_prompt
from app.agents.state import AgentState
from app.core.logger import logger
from typing import Dict, Any, Optional

async def executor_node(state: AgentState) -> AgentState:
    """
    LangGraph node for executing a single pending task in the proposal generation plan.
    """
    logger.info("Executor Agent node execution started.")

    # Safeguard state elements
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []
    if "completed_tasks" not in state or state["completed_tasks"] is None:
        state["completed_tasks"] = []
    if "generated_sections" not in state or state["generated_sections"] is None:
        state["generated_sections"] = {}
    if "execution_plan" not in state or not state["execution_plan"]:
        err_msg = "Executor Error: No execution plan found in the shared state."
        logger.error(err_msg)
        state["errors"].append(err_msg)
        state["status"] = "failed"
        return state

    # 1. Identify the next pending task
    next_task = None
    for task in state["execution_plan"]:
        if task.get("status") == "pending":
            next_task = task
            break

    # 2. If no pending tasks remain, set status to executed and exit
    if not next_task:
        logger.info("No pending tasks remaining in execution plan.")
        state["status"] = "executed"
        state["current_task"] = None
        return state

    task_name = next_task["task"]
    logger.info(f"Processing task {next_task['id']}: '{task_name}'")
    
    # Update current task and status to in_progress
    state["current_task"] = task_name
    next_task["status"] = "in_progress"

    # Extract metadata context
    request_str = state.get("request", "")
    metadata = state.get("metadata", {})
    client_name = metadata.get("client_name")
    company_name = metadata.get("company_name")
    project_name = metadata.get("project_name")

    # 3. Build prompt
    prompt = build_executor_prompt(
        task=task_name,
        request=request_str,
        client_name=client_name,
        company_name=company_name,
        project_name=project_name,
        previously_generated=state["generated_sections"]
    )
    logger.info(f"Executor prompt built successfully for task: '{task_name}'")

    # 4. Generate content with retries on validation errors
    max_section_retries = 2
    attempt = 0
    content = ""
    validation_passed = False

    while attempt <= max_section_retries and not validation_passed:
        attempt += 1
        try:
            logger.info(f"Sending content generation request (Attempt {attempt}/{max_section_retries + 1}) for task: '{task_name}'")
            content = await llm_service.generate_text(
                prompt=prompt,
                system_instruction=EXECUTOR_SYSTEM_PROMPT
            )
            
            # 5. Validate content
            if not content or not content.strip():
                raise ValueError("Generated section content is empty.")
            
            content_clean = content.strip()
            if len(content_clean) < 50:
                raise ValueError(f"Generated content is too short ({len(content_clean)} chars). Minimum length is 50.")

            # Check if this content is identical to any already generated section (duplicate check)
            is_duplicate = False
            for prev_section, prev_content in state["generated_sections"].items():
                if prev_content.strip() == content_clean:
                    is_duplicate = True
                    break
            if is_duplicate:
                raise ValueError("Generated content is a duplicate of a previously generated section.")

            # Validation passed
            validation_passed = True
            content = content_clean
            logger.info(f"Section content validated successfully on attempt {attempt}.")

        except Exception as e:
            logger.warning(f"Validation failure or LLM error on attempt {attempt} for task '{task_name}': {str(e)}")
            if attempt > max_section_retries:
                err_msg = f"Executor failed for task '{task_name}' after {attempt} attempts. Last error: {str(e)}"
                logger.error(err_msg)
                state["errors"].append(err_msg)
                next_task["status"] = "failed"
                state["status"] = "failed"
                return state

    # 6. Store output and update task status
    state["generated_sections"][task_name] = content
    state["completed_tasks"].append(task_name)
    next_task["status"] = "completed"
    logger.info(f"Task completed successfully: '{task_name}'")

    # Check if there are any remaining pending tasks
    has_more_pending = any(t.get("status") == "pending" for t in state["execution_plan"])
    if not has_more_pending:
        state["status"] = "executed"
        state["current_task"] = None
        logger.info("All execution plan tasks are now completed.")

    return state
