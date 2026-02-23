from typing import Protocol

class AlertBackend(Protocol):
    """Protocol for various notification delivery mechanisms."""

    def dispatch(self, title: str, message: str) -> bool:
        """Dispatch the alert asynchronously.
        
        Args:
            title: The short alert title (e.g., "Agent Waiting")
            message: The detailed description of the alert state
            
        Returns:
            bool: True if dispatch was successfully triggered/queued, False otherwise.
        """
        ...
