import logging
from typing import Optional

from .event_bus import get_global_bus
from .state_classifier import StateClassifier
from .deduplicator import Deduplicator
from .alert_router import AlertRouter
from .history import NotificationHistory
from .config import get_config
from .models import AgentEvent, AgentState

# Backends
from .backends.audio import AudioBackend
from .backends.desktop import DesktopBackend
from .backends.webhook import WebhookBackend

logger = logging.getLogger(__name__)

class AttentionObserver:
    """Subscribes to all agent events, classifies them, and routes alerts."""

    def __init__(self, 
                 bus=None, 
                 classifier: Optional[StateClassifier] = None,
                 deduplicator: Optional[Deduplicator] = None,
                 router: Optional[AlertRouter] = None):
                 
        self._bus = bus or get_global_bus()
        self._config = get_config()
        self._classifier = classifier or StateClassifier()
        self._deduplicator = deduplicator or Deduplicator(
            cooldown_seconds=self._config.cooldown_seconds
        )
        
        # If no router provided, build the default one from config
        if router is None:
            backends = []
            if self._config.backends.get("audio", {}).get("enabled", True):
                 backends.append(AudioBackend(self._config.backends.get("audio")))
            if self._config.backends.get("desktop", {}).get("enabled", True):
                 backends.append(DesktopBackend(self._config.backends.get("desktop")))
            if self._config.backends.get("webhook", {}).get("enabled", False):
                 backends.append(WebhookBackend(self._config.backends.get("webhook")))
                 
            history = None
            if self._config.history.get("enabled", True):
                 history = NotificationHistory(self._config.history.get("db_path", "notifications.db"))
                 
            self._router = AlertRouter(
                 backends=backends, 
                 config=self._config._data, # Pass raw dict for escalation rules
                 history=history
            )
        else:
            self._router = router

    def start(self):
        """Start listening to the event bus."""
        self._bus.subscribe(self.on_event)
        logger.info("Attention Observer started.")

    def stop(self):
        """Stop listening to the event bus."""
        self._bus.unsubscribe(self.on_event)
        logger.info("Attention Observer stopped.")

    def on_event(self, event: AgentEvent):
        """Callback for all published events."""
        # 1. Classify raw event -> canonical State
        state = self._classifier.classify(event)
        if not state:
            return

        # If we transition back to running, resolve any pending escalations and cooldowns
        if state == AgentState.RUNNING:
             logger.debug(f"Agent recovered to {state.name}. Resolving blocks.")
             self._router.resolve_block()
             
             # Reset cooldowns for all alert states since we recovered
             from .models import ALERT_STATES
             for alert_state in ALERT_STATES:
                  self._deduplicator.reset(alert_state)
             return

        # 2. Check if state warrants an alert
        from .models import ALERT_STATES
        if state not in ALERT_STATES:
             return

        # 3. Suppress duplicates (spam filter)
        if not self._deduplicator.should_alert(event, state):
             return

        # 4. Route to alerting backends
        logger.info(f"Attention required! Routing alert for state: {state.name}")
        self._router.dispatch(event, state)
