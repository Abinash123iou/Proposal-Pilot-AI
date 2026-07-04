from app.llm.groq_client import groq_client_manager
from app.llm.llm_service import (
    BaseLLMService,
    GroqLLMService,
    LLMException,
    LLMConfigException,
    LLMTimeoutException,
    LLMRateLimitException,
    LLMApiException
)
from app.llm.prompts import (
    PLANNER_SYSTEM_PROMPT,
    EXECUTOR_SYSTEM_PROMPT,
    REFLECTION_SYSTEM_PROMPT,
    REFLECTION_QA_SYSTEM_PROMPT,
    REGENERATION_SYSTEM_PROMPT,
    TONE,
    WRITING_GUIDELINES
)
from app.llm.prompt_builder import (
    build_planner_prompt,
    build_executor_prompt,
    build_reflection_prompt,
    build_reflection_qa_prompt,
    build_regeneration_prompt
)

# Shared singleton instance of the LLM Service
llm_service = GroqLLMService(client_manager=groq_client_manager)
