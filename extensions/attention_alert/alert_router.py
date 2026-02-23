import logging
import threading
import time
from typing import List, Optional
from .models import AgentEvent, AgentState
from .backends import AlertBackend

logger = logging.getLogger(__name__)

class AlertRouter:
    """Routes an event to one or more notification backends based on config."""

    def __init__(self, backends: List[AlertBackend], config: dict = None, history = None):
        self._backends = backends
        self._config = config or {}
        self._history = history
        # Escalation rules are list of dicts: {"delay_seconds": X, "backend": Y}
        self._escalation_rules = self._config.get("escalation", [])
        
        # Track pending escalations so they can be canceled if the block resolves
        # Key: process_id or some unique block identifier
        # We use a simple global lock since there's typically only one block at a time
        self._escalation_lock = threading.Lock()
        self._pending_escalations = {}

    def dispatch(self, event: AgentEvent, state: AgentState):
        """Orchestrate dispatching to all configured backends based on escalation rules."""
        title = f"Agent {state.name.replace('_', ' ').title()}"
        message = f"Source: {event.source}\nType: {event.type}"
        
        event_id = None
        if self._history:
             event_id = self._history.record_event(event)
             
        # Find 0-delay base rules to dispatch immediately
        immediate_backends = [
            rule.get("backend") for rule in self._escalation_rules 
            if rule.get("delay_seconds", 0) == 0 and "backend" in rule
        ]

        if not immediate_backends:
            # If no escalation rules defined, just dispatch to all enabled backends
            for backend in self._backends:
               self._dispatch_to_backend(backend, title, message, event_id)
        else:
            # Dispatch to immediate backends
            for backend_name in immediate_backends:
                backend = self._get_backend_by_name(backend_name)
                if backend:
                     self._dispatch_to_backend(backend, title, message, event_id)
                     
        # Setup future escalations
        self._schedule_escalations(event, state, title, message, event_id)

    def resolve_block(self):
         """Called when the agent resumes running to cancel pending alarms."""
         with self._escalation_lock:
              for timer in self._pending_escalations.values():
                   timer.cancel()
              self._pending_escalations.clear()
              logger.debug("Cancelled all pending escalation timers.")

    def _schedule_escalations(self, event: AgentEvent, state: AgentState, title: str, message: str, event_id: Optional[int]):
         """Schedule delayed notifications based on config."""
         with self._escalation_lock:
              # Cancel any existing escalations first
              for timer in self._pending_escalations.values():
                   timer.cancel()
              self._pending_escalations.clear()

              delayed_rules = [
                  rule for rule in self._escalation_rules
                  if rule.get("delay_seconds", 0) > 0
              ]

              for i, rule in enumerate(delayed_rules):
                  delay = rule.get("delay_seconds")
                  
                  if "backend" in rule:
                      backend_name = rule.get("backend")
                      backend = self._get_backend_by_name(backend_name)
                      if backend:
                           # We must capture the arguments in default args to avoid late binding issues in loops
                           def trigger_backend(b=backend, t=title, m=message, e=event_id, idx=i):
                                logger.info(f"Triggering escalation rule {idx} (backend: {b.__class__.__name__})")
                                self._dispatch_to_backend(b, t, m, e)
                                # Remove self from pending tracking
                                with self._escalation_lock:
                                     self._pending_escalations.pop(idx, None)
                                     
                           timer = threading.Timer(delay, trigger_backend)
                           self._pending_escalations[i] = timer
                           timer.daemon = True
                           timer.start()
                  
                  elif "action" in rule and rule.get("action") == "auto_pause":
                       # Example of a non-notification escalation
                       def trigger_action(idx=i):
                            logger.critical(f"Escalation threshold reached. Triggering action: auto_pause")
                            # Integration point: call agent pause API here
                            # self._agent.pause()
                            
                            with self._escalation_lock:
                                 self._pending_escalations.pop(idx, None)
                                 
                       timer = threading.Timer(delay, trigger_action)
                       self._pending_escalations[i] = timer
                       timer.daemon = True
                       timer.start()

    def _get_backend_by_name(self, name: str) -> Optional[AlertBackend]:
         """Find a backend instance by its conventional name ('audio', 'desktop', 'webhook')."""
         target_class = f"{name.capitalize()}Backend"
         for backend in self._backends:
              if backend.__class__.__name__ == target_class:
                   return backend
         return None

    def _dispatch_to_backend(self, backend: AlertBackend, title: str, message: str, event_id: Optional[int]):
        """Helper to invoke a single backend and record the result."""
        try:
            status = "success" if backend.dispatch(title, message) else "suppressed"
            if self._history and event_id is not None:
                 self._history.record_dispatch(
                      event_id, 
                      backend.__class__.__name__, 
                      status, 
                      time.monotonic()
                 )
        except Exception as e:
            logger.error(f"Error dispatching to {backend.__class__.__name__}: {e}")
            if self._history and event_id is not None:
                 self._history.record_dispatch(
                      event_id, 
                      backend.__class__.__name__, 
                      "failed", 
                      time.monotonic(),
                      error_msg=str(e)
                 )
