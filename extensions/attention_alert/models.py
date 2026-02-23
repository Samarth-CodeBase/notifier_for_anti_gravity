from dataclasses import dataclass, field
from enum import Enum
import time

class AgentState(Enum):
    """Canonical states representing the execution context of the agent."""
    RUNNING = "running"
    WAITING_FOR_CONFIRMATION = "waiting_for_confirmation"
    WAITING_FOR_STDIN = "waiting_for_stdin"
    WAITING_FOR_PERMISSION = "waiting_for_permission"
    WAITING_FOR_EXTERNAL_INPUT = "waiting_for_external_input"
    STALLED = "stalled"
    COMPLETED = "completed"
    FAILED = "failed"

# States that should trigger an alert
ALERT_STATES = {
    AgentState.WAITING_FOR_CONFIRMATION,
    AgentState.WAITING_FOR_STDIN,
    AgentState.WAITING_FOR_PERMISSION,
    AgentState.WAITING_FOR_EXTERNAL_INPUT,
    AgentState.STALLED,
}

@dataclass
class AgentEvent:
    """Represents a state change or significant event in the agent lifecycle."""
    type: str          # e.g., "awaiting_confirmation", "stdin_request"
    source: str        # e.g., "tool_dispatcher", "subprocess", "watchdog"
    payload: dict      # Contextual data
    severity: str = "info"  # "info", "warning", "critical"
    timestamp: float = field(default_factory=time.monotonic)
