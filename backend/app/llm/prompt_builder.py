from typing import Optional

def build_planner_prompt(
    request: str,
    document_type: str = "proposal",
    client_name: Optional[str] = None,
    company_name: Optional[str] = None,
    project_name: Optional[str] = None
) -> str:
    """
    Dynamically constructs the prompt for the Planner Agent.
    """
    prompt = (
        "Analyze the following proposal generation request and return a structured plan.\n\n"
        f"Initial Request: {request}\n"
        f"Document Type: {document_type}\n"
    )
    if client_name:
        prompt += f"Target Client: {client_name}\n"
    if company_name:
        prompt += f"Service Provider: {company_name}\n"
    if project_name:
        prompt += f"Project Name: {project_name}\n"

    prompt += (
        "\nProduce a logical sequence of drafting tasks to satisfy the request. "
        "Strictly output only the expected JSON structure."
    )
    return prompt

def build_executor_prompt(
    task: str,
    request: str,
    client_name: Optional[str] = None,
    company_name: Optional[str] = None,
    project_name: Optional[str] = None,
    previously_generated: Optional[dict[str, str]] = None
) -> str:
    """
    Dynamically constructs the prompt for the Executor Agent to draft a specific section.
    """
    prompt = (
        f"Your Task: Write the section content for: '{task}'\n\n"
        f"Initial Proposal Request: {request}\n"
    )
    
    # Add metadata if available
    metadata_lines = []
    if client_name:
        metadata_lines.append(f"Target Client: {client_name}")
    if company_name:
        metadata_lines.append(f"Service Provider: {company_name}")
    if project_name:
        metadata_lines.append(f"Project Name: {project_name}")
    if metadata_lines:
        prompt += "Metadata Context:\n" + "\n".join(metadata_lines) + "\n\n"

    # Add previously generated context for consistency
    if previously_generated:
        prompt += "Previously Generated Sections (Maintain consistency with these):\n"
        for section_name, section_content in previously_generated.items():
            prompt += f"--- Section: {section_name} ---\n{section_content}\n\n"

    prompt += (
        f"Draft the proposal section for '{task}' now. "
        "Return ONLY the plain text content. Do not add markdown labels."
    )
    return prompt

def build_reflection_prompt(
    proposal_sections: dict[str, str],
    request: str
) -> str:
    """
    Dynamically constructs the review/criticism prompt for the Reflection Agent.
    """
    prompt = (
        "Review the complete draft proposal generated to fulfill the user's request.\n\n"
        f"Original User Request: {request}\n\n"
        "Draft Proposal Content:\n"
    )
    for section_name, section_content in proposal_sections.items():
        prompt += f"--- Section: {section_name} ---\n{section_content}\n\n"

    prompt += (
        "Critically evaluate this content. Ensure all requirements from the original request are addressed, "
        "estimates are logical, there are no formatting bugs, and there are no placeholders. "
        "Strictly output only the expected JSON structure."
    )
    return prompt
