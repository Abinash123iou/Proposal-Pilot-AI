from abc import ABC, abstractmethod
from typing import Dict, Any

class DocumentGenerator(ABC):
    """
    Abstract base class defining the contract for document generation exporters.
    """
    @abstractmethod
    async def generate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes validated proposal data and generates a document.

        Args:
            state (Dict[str, Any]): Validated AgentState dictionary.

        Returns:
            Dict[str, Any]: Generation metadata dictionary.
        """
        pass
