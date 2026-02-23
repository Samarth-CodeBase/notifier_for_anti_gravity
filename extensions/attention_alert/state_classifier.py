import logging
from typing import Optional
from .models import AgentEvent, AgentState

logger = logging.getLogger(__name__)

class StateClassifier:
    """Classifies raw AgentEvents into canonical AgentState enums based on event type."""
    
    _MAP = {
        "awaiting_confirmation": AgentState.WAITING_FOR_CONFIRMATION,
        "awaiting_user_input": AgentState.WAITING_FOR_EXTERNAL_INPUT,
        "stdin_request": AgentState.WAITING_FOR_STDIN,
        "permission_request": AgentState.WAITING_FOR_PERMISSION,
        "execution_stalled": AgentState.STALLED,
        "execution_completed": AgentState.COMPLETED,
        "execution_failed": AgentState.FAILED,
        "execution_running": AgentState.RUNNING,
    }

    def classify(self, event: AgentEvent) -> Optional[AgentState]:
        """Convert a raw event into an AgentState enum."""
        state = self._MAP.get(event.type)
        if not state:
            logger.debug(f"Event type '{event.type}' fell back to UNKNOWN or None mappings.")
            return None
        return state
