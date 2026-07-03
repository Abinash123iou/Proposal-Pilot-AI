import abc
import json
import time
import asyncio
from typing import Any, Optional, Union
from groq import AsyncGroq, APIError, APITimeoutError, RateLimitError
from app.core.config import settings
from app.core.logger import logger
from app.llm.groq_client import groq_client_manager

class LLMException(Exception):
    """Base exception for LLM operations."""
    pass

class LLMConfigException(LLMException):
    """Raised when LLM configuration is missing or invalid."""
    pass

class LLMTimeoutException(LLMException):
    """Raised when LLM request times out."""
    pass

class LLMRateLimitException(LLMException):
    """Raised when LLM service is rate limited."""
    pass

class LLMApiException(LLMException):
    """Raised when LLM returns an API error."""
    pass

class BaseLLMService(abc.ABC):
    """
    Abstract base class for all LLM service providers to support dependency inversion.
    """
    @abc.abstractmethod
    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generates a plain text response for the given prompt.
        """
        pass

    @abc.abstractmethod
    async def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> dict[str, Any]:
        """
        Generates a validated JSON object response for the given prompt.
        """
        pass

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """
        Verifies provider connection availability.
        """
        pass

class GroqLLMService(BaseLLMService):
    """
    LLM Service implementation for the Groq API provider.
    """
    def __init__(self, client_manager=groq_client_manager):
        self.client_manager = client_manager
        self.model = settings.GROQ_MODEL
        self.max_retries = settings.MAX_RETRIES
        self.timeout = settings.REQUEST_TIMEOUT

    async def _call_with_retry(
        self,
        system_instruction: Optional[str],
        prompt: str,
        response_format: Optional[dict[str, str]] = None
    ) -> str:
        """
        Executes completions API call with exponential backoff on transient errors.
        """
        if not prompt or not prompt.strip():
            raise LLMException("Prompt cannot be empty or contain only whitespace.")

        try:
            client = self.client_manager.get_client()
        except ValueError as e:
            raise LLMConfigException(str(e)) from e

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "timeout": self.timeout
        }
        if response_format:
            kwargs["response_format"] = response_format

        retry_count = 0
        backoff_factor = 2.0

        while True:
            try:
                logger.info(f"LLM request started. Model: {self.model}. Attempt: {retry_count + 1}")
                start_time = time.perf_counter()
                
                response = await client.chat.completions.create(**kwargs)
                
                duration = time.perf_counter() - start_time
                logger.info(f"LLM response completed in {duration:.2f} seconds.")
                
                if response.usage:
                    logger.info(
                        f"Tokens used - Prompt: {response.usage.prompt_tokens}, "
                        f"Completion: {response.usage.completion_tokens}, "
                        f"Total: {response.usage.total_tokens}"
                    )
                
                content = response.choices[0].message.content
                if content is None:
                    raise LLMApiException("Groq API returned an empty completion content.")
                return content

            except APITimeoutError as e:
                logger.warning(f"Timeout calling Groq API (Attempt {retry_count + 1}/{self.max_retries + 1}): {str(e)}")
                if retry_count >= self.max_retries:
                    raise LLMTimeoutException("Groq API request timed out after retries.") from e
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit on Groq API (Attempt {retry_count + 1}/{self.max_retries + 1}): {str(e)}")
                if retry_count >= self.max_retries:
                    raise LLMRateLimitException("Groq API rate limit exceeded after retries.") from e
                
            except APIError as e:
                status_code = getattr(e, "status_code", 500)
                logger.warning(f"Groq API error (Attempt {retry_count + 1}/{self.max_retries + 1}): Code {status_code}. Message: {str(e)}")
                # Retrying only transient 5xx errors
                if status_code >= 500:
                    if retry_count >= self.max_retries:
                        raise LLMApiException(f"Groq API server error: {str(e)}") from e
                else:
                    raise LLMApiException(f"Groq API client error: {str(e)}") from e
                    
            except Exception as e:
                logger.exception(f"Unexpected exception during LLM call: {str(e)}")
                raise LLMException(f"Unexpected LLM error: {str(e)}") from e

            # Wait and exponential backoff
            sleep_time = backoff_factor ** retry_count
            retry_count += 1
            logger.info(f"Retrying LLM call in {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)

    async def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generates a plain text response for the given prompt.
        """
        return await self._call_with_retry(system_instruction, prompt)

    async def generate_json(self, prompt: str, system_instruction: Optional[str] = None) -> dict[str, Any]:
        """
        Generates a validated JSON object response for the given prompt.
        """
        raw_text = await self._call_with_retry(
            system_instruction, 
            prompt, 
            response_format={"type": "json_object"}
        )
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {raw_text}")
            raise LLMException("Failed to decode LLM response as JSON.") from e

    async def health_check(self) -> bool:
        """
        Quick check to verify connection availability.
        """
        try:
            await self._call_with_retry(
                system_instruction="You are a health check system. Respond with pong.",
                prompt="ping"
            )
            return True
        except Exception as e:
            logger.error(f"LLM Service health check failed: {str(e)}")
            return False
