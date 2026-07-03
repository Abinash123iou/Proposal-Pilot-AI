from groq import AsyncGroq
from app.core.config import settings
from app.core.logger import logger

class GroqClientManager:
    """
    Manages the initialization and lifecycle of the AsyncGroq client.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL
        self._client = None

    def get_client(self) -> AsyncGroq:
        """
        Lazily instantiates and returns the AsyncGroq client.
        """
        if not self.api_key:
            logger.error("Attempted to initialize Groq client without an API Key.")
            raise ValueError("GROQ_API_KEY is missing from configurations.")
            
        if self._client is None:
            logger.info(f"Initializing AsyncGroq client for model: {self.model}")
            self._client = AsyncGroq(api_key=self.api_key)
            
        return self._client

# Singleton client manager instance
groq_client_manager = GroqClientManager()
