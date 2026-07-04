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

def build_reflection_qa_prompt(
    proposal_sections: dict[str, str],
    request: str,
    programmatic_findings: Optional[dict] = None
) -> str:
    """
    Dynamically constructs the reflection prompt for the QA Reflection Agent.
    """
    prompt = (
        "Review the complete draft proposal generated to fulfill the user's request.\n\n"
        f"Original User Request: {request}\n\n"
        "Draft Proposal Content:\n"
    )
    for section_name, section_content in proposal_sections.items():
        prompt += f"--- Section: {section_name} ---\n{section_content}\n\n"

    if programmatic_findings:
        prompt += "Programmatic Check Findings (Verify and incorporate these into your final report):\n"
        if programmatic_findings.get("missing_sections"):
            prompt += f"- Missing Mandatory Sections: {', '.join(programmatic_findings['missing_sections'])}\n"
        if programmatic_findings.get("duplicate_sections"):
            prompt += f"- Duplicate/Repeated Sections: {', '.join(programmatic_findings['duplicate_sections'])}\n"
        if programmatic_findings.get("empty_sections"):
            prompt += f"- Empty Sections: {', '.join(programmatic_findings['empty_sections'])}\n"
        if programmatic_findings.get("low_quality_sections"):
            prompt += f"- Low Quality/Short Sections: {', '.join(programmatic_findings['low_quality_sections'])}\n"
        prompt += "\n"

    prompt += (
        "Critically evaluate this content. Ensure all requirements from the original request are addressed, "
        "estimates are logical, there are no formatting bugs, and there are no placeholders. "
        "Strictly output only the expected JSON structure."
    )
    return prompt

def build_regeneration_prompt(
    section_name: str,
    request: str,
    proposal_sections: dict[str, str],
    criticisms: list[str],
    recommendations: list[str]
) -> str:
    """
    Constructs the prompt to regenerate a specific failed proposal section.
    """
    prompt = (
        f"You need to regenerate and rewrite the proposal section: '{section_name}'\n\n"
        f"Original User Request: {request}\n\n"
        "Previously Generated Sections (For consistency context):\n"
    )
    for name, content in proposal_sections.items():
        if name != section_name:
            prompt += f"--- Section: {name} ---\n{content}\n\n"
            
    prompt += f"--- Section to Rewrite: {section_name} ---\n{proposal_sections.get(section_name, '[Empty]')}\n\n"
    
    prompt += "Quality Review Feedback:\n"
    for criticism in criticisms:
        prompt += f"- Criticism: {criticism}\n"
    for rec in recommendations:
        prompt += f"- Recommendation: {rec}\n"
        
    prompt += (
        f"\nRewrite the section '{section_name}' now to correct the issues above. "
        "Ensure it fits perfectly in tone and style with the other sections. "
        "Return ONLY the plain text content. Do not add markdown labels."
    )
    return prompt

