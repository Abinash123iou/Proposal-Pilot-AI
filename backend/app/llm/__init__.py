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

# Shared singleton instance of the LLM Service
llm_service = GroqLLMService(client_manager=groq_client_manager)
