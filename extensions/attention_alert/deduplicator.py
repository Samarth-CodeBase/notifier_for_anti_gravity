import logging
from .models import AgentEvent, AgentState

logger = logging.getLogger(__name__)

class Deduplicator:
    """Suppresses duplicate events of the same AgentState within a cooldown window.
    
    Prevents alert spam when an agent is stuck in a loop emitting the same
    retry or stall event continuously.
    """

    def __init__(self, cooldown_seconds: int = 10):
        self._cooldown_seconds = cooldown_seconds
        # Maps state to the timestamp of the last time it ALERTS
        self._last_alerted = {}
        # Maps state to the timestamp of the last time it was SEEN
        self._last_seen = {}

    def should_alert(self, event: AgentEvent, state: AgentState) -> bool:
        """Determines if an alert should be fired for this event.
        
        Returns:
            bool: True if alert should proceed, False if suppressed.
        """
        now = event.timestamp
        last_alerted = self._last_alerted.get(state, 0)
        
        self._last_seen[state] = now

        if now - last_alerted < self._cooldown_seconds:
             logger.debug(f"Suppressed duplicate alert for {state.name} (cooldown: {now - last_alerted:.1f}s < {self._cooldown_seconds}s)")
             return False

        # Reached here, cooldown expired or never alerted before
        self._last_alerted[state] = now
        logger.debug(f"Allowed alert for {state.name} (time since last: {now - last_alerted:.1f}s)")
        return True
        
    def reset(self, state: AgentState):
        """Force reset the cooldown for a specific state, usually called when 
        we transition back to RUNNING.
        """
        if state in self._last_alerted:
            del self._last_alerted[state]
            logger.debug(f"Reset cooldown for {state.name}")
