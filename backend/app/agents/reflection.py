import json
from typing import Dict, Any, List, Optional
from app.agents.state import AgentState
from app.core.logger import logger
from app.llm import (
    llm_service,
    REFLECTION_QA_SYSTEM_PROMPT,
    REGENERATION_SYSTEM_PROMPT,
    build_reflection_qa_prompt,
    build_regeneration_prompt
)

def run_programmatic_checks(generated_sections: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Executes fast programmatic validation checks on generated sections.
    """
    # 1. Mandatory sections mapping
    mandatory_mapping = {
        "Executive Summary": ["executive summary", "exec summary"],
        "Scope": ["scope", "project scope"],
        "Timeline": ["timeline", "schedule"],
        "Budget": ["budget", "cost", "pricing", "financial"],
        "Risks": ["risk"],
        "Assumptions": ["assumption"],
        "Conclusion": ["conclusion", "summary"]
    }
    
    missing_sections = []
    keys_lower = [k.lower() for k in generated_sections.keys()]
    
    for section_name, synonyms in mandatory_mapping.items():
        found = False
        for synonym in synonyms:
            if any(synonym in key for key in keys_lower):
                found = True
                break
        if not found:
            missing_sections.append(section_name)
            
    # 2. Emptiness, length, and duplicates
    empty_sections = []
    low_quality_sections = []
    duplicate_sections = []
    
    seen_contents = {}
    for key, content in generated_sections.items():
        content_stripped = (content or "").strip()
        if not content_stripped:
            empty_sections.append(key)
            continue
        
        if len(content_stripped) < 50:
            low_quality_sections.append(key)
            
        if content_stripped in seen_contents.values():
            duplicate_sections.append(key)
        else:
            seen_contents[key] = content_stripped
            
    return {
        "missing_sections": missing_sections,
        "empty_sections": empty_sections,
        "low_quality_sections": low_quality_sections,
        "duplicate_sections": duplicate_sections
    }

def find_matching_section_key(section_name: str, generated_sections: Dict[str, str]) -> Optional[str]:
    """
    Fuzzily maps a section name referenced by the LLM back to the actual dictionary key.
    """
    if section_name in generated_sections:
        return section_name
        
    name_lower = section_name.lower()
    
    # Try case-insensitive exact match
    for key in generated_sections:
        if key.lower() == name_lower:
            return key
            
    # Try substring match
    for key in generated_sections:
        if name_lower in key.lower() or key.lower() in name_lower:
            return key
            
    return None

async def reflection_node(state: AgentState) -> AgentState:
    """
    LangGraph node implementing the QA Reflection and self-check capabilities.
    """
    logger.info("Reflection Started")
    
    # 1. Initialize audit fields in state
    if "errors" not in state or state["errors"] is None:
        state["errors"] = []
    if "regenerated_sections" not in state or state["regenerated_sections"] is None:
        state["regenerated_sections"] = []
        
    state["reflection_result"] = None
    state["quality_score"] = 0
    state["review_status"] = "FAIL"
    
    generated_sections = state.get("generated_sections")
    
    # 2. Check for empty generated sections
    if not generated_sections:
        err_msg = "Reflection Error: No generated sections found to review."
        logger.error(err_msg)
        state["errors"].append(err_msg)
        state["status"] = "failed"
        logger.info("Reflection Completed")
        return state
        
    request_str = state.get("request", "")
    
    try:
        logger.info("Proposal Review Started")
        
        # 3. Run local programmatic checks first
        prog_findings = run_programmatic_checks(generated_sections)
        if prog_findings["missing_sections"]:
            logger.warning(f"Missing Sections Detected: {prog_findings['missing_sections']}")
            
        # 4. Construct reflection prompt and call LLM service
        prompt = build_reflection_qa_prompt(
            proposal_sections=generated_sections,
            request=request_str,
            programmatic_findings=prog_findings
        )
        
        logger.info("Calling LLM Service for structured review...")
        response_dict = await llm_service.generate_json(
            prompt=prompt,
            system_instruction=REFLECTION_QA_SYSTEM_PROMPT
        )
        logger.info("Received quality review report from LLM.")
        
        # Validate LLM response fields and apply defaults if missing
        quality_score = response_dict.get("quality_score", 0)
        overall_status = response_dict.get("overall_status", "FAIL")
        missing_sections = response_dict.get("missing_sections", [])
        duplicate_sections = response_dict.get("duplicate_sections", [])
        warnings = response_dict.get("warnings", [])
        recommendations = response_dict.get("recommendations", [])
        regeneration_required = response_dict.get("regeneration_required", False)
        sections_to_regenerate = response_dict.get("sections", [])
        
        # Merge programmatic findings if LLM failed to detect them
        # E.g. force status to FAIL and flag missing/duplicate sections
        if prog_findings["missing_sections"]:
            missing_sections = list(set(missing_sections + prog_findings["missing_sections"]))
            overall_status = "FAIL"
            if "Missing mandatory sections." not in warnings:
                warnings.append("Missing mandatory sections.")
        
        if prog_findings["duplicate_sections"]:
            duplicate_sections = list(set(duplicate_sections + prog_findings["duplicate_sections"]))
            overall_status = "FAIL"
            if "Duplicate content detected." not in warnings:
                warnings.append("Duplicate content detected.")
                
        # Force fail if any section is empty or low quality (less than 50 chars)
        if prog_findings["empty_sections"] or prog_findings["low_quality_sections"]:
            overall_status = "FAIL"
            regeneration_required = True
            for sec in prog_findings["empty_sections"] + prog_findings["low_quality_sections"]:
                if sec not in sections_to_regenerate:
                    sections_to_regenerate.append(sec)
            if "Empty or low-quality sections detected." not in warnings:
                warnings.append("Empty or low-quality sections detected.")
                
        # Update values in the report
        response_dict["overall_status"] = overall_status
        response_dict["missing_sections"] = missing_sections
        response_dict["duplicate_sections"] = duplicate_sections
        response_dict["warnings"] = warnings
        response_dict["regeneration_required"] = regeneration_required
        response_dict["sections"] = sections_to_regenerate
        
        logger.info(f"Quality Score Calculated: {quality_score}")
        
        # 5. Handle section regeneration workflow if required
        if regeneration_required and sections_to_regenerate:
            logger.info("Regeneration Started")
            regenerated = []
            
            for section in sections_to_regenerate:
                actual_key = find_matching_section_key(section, generated_sections)
                if not actual_key:
                    logger.warning(f"Could not map failed section '{section}' to generated sections. Skipping regeneration for it.")
                    continue
                
                logger.info(f"Regenerating section: '{actual_key}'")
                
                # Build regeneration prompt
                regen_prompt = build_regeneration_prompt(
                    section_name=actual_key,
                    request=request_str,
                    proposal_sections=generated_sections,
                    criticisms=[f"Failed quality check: {section}"],
                    recommendations=recommendations
                )
                
                try:
                    new_content = await llm_service.generate_text(
                        prompt=regen_prompt,
                        system_instruction=REGENERATION_SYSTEM_PROMPT
                    )
                    
                    if not new_content or not new_content.strip():
                        raise ValueError(f"Regenerated content for '{actual_key}' is empty.")
                    
                    # Basic validation of regenerated content
                    new_content_clean = new_content.strip()
                    if len(new_content_clean) < 50:
                        raise ValueError(f"Regenerated content is too short ({len(new_content_clean)} chars).")
                        
                    # Update section
                    state["generated_sections"][actual_key] = new_content_clean
                    regenerated.append(actual_key)
                    logger.info(f"Regeneration completed for section: '{actual_key}'")
                    
                except Exception as e:
                    err_msg = f"Regeneration failure for section '{actual_key}': {str(e)}"
                    logger.error(err_msg)
                    state["errors"].append(err_msg)
                    # We continue attempting other sections if one fails, but mark status accordingly
            
            state["regenerated_sections"] = regenerated
            logger.info("Regeneration Completed")
            
            # Post-regeneration: update quality score and status to reflect successful regeneration pass
            if regenerated:
                # Re-check status dynamically
                state["review_status"] = "PASS"
                state["quality_score"] = max(quality_score, 85) # upgrade score on successful correction
                response_dict["overall_status"] = "PASS"
                response_dict["quality_score"] = state["quality_score"]
                response_dict["regeneration_required"] = False
            else:
                state["review_status"] = overall_status
                state["quality_score"] = quality_score
        else:
            state["review_status"] = overall_status
            state["quality_score"] = quality_score
            
        state["reflection_result"] = response_dict
        state["status"] = "reflected"
        
    except json.JSONDecodeError as e:
        err_msg = f"Reflection Error: Invalid reflection JSON returned by LLM: {str(e)}"
        logger.error(err_msg)
        state["errors"].append(err_msg)
        state["status"] = "failed"
        
    except Exception as e:
        err_msg = f"Reflection unexpected exception: {str(e)}"
        logger.error(err_msg)
        state["errors"].append(err_msg)
        state["status"] = "failed"
        
    logger.info("Reflection Completed")
    return state
