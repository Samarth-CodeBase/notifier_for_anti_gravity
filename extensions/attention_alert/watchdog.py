import threading
import time
import logging
from .models import AgentEvent
from .event_bus import get_global_bus

logger = logging.getLogger(__name__)

class ExecutionWatchdog:
    """Monitors the execution thread and fires a stall event if no heartbeat is received."""

    def __init__(self, timeout_seconds: int = 30):
        self._timeout = timeout_seconds
        self._last_heartbeat = time.monotonic()
        self._stop_event = threading.Event()
        self._thread = None
        self._bus = get_global_bus()
        self._stalled = False

    def start(self):
        """Start the background watchdog thread."""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._watch, daemon=True, name="ExecutionWatchdog")
            self._last_heartbeat = time.monotonic()
            self._stalled = False
            self._thread.start()
            logger.debug(f"Watchdog started (timeout: {self._timeout}s)")

    def stop(self):
        """Stop the watchdog thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def heartbeat(self):
        """Reset the stall timer. Must be called repeatedly by the main execution loop."""
        self._last_heartbeat = time.monotonic()
        
        # If we were previously stalled and just got a heartbeat, we've recovered
        if self._stalled:
            self._stalled = False
            logger.info("Watchdog detected execution recovery.")
            # Emit recovery event if needed, but for now we just log it
            self._bus.publish(AgentEvent(
                type="execution_running",
                source="watchdog",
                payload={},
                severity="info"
            ))

    def _watch(self):
        """Background loop that checks for heartbeats."""
        while not self._stop_event.is_set():
            # Sleep for a fraction of the timeout
            time.sleep(min(5.0, self._timeout / 2))
            
            elapsed = time.monotonic() - self._last_heartbeat
            if elapsed > self._timeout and not self._stalled:
                self._stalled = True
                logger.warning(f"Execution stalled! No heartbeat for {elapsed:.1f}s")
                self._bus.publish(AgentEvent(
                    type="execution_stalled",
                    source="watchdog",
                    payload={"elapsed_seconds": elapsed, "timeout": self._timeout},
                    severity="warning"
                ))

# Global watchdog instance
_watchdog = None

def get_watchdog(timeout_seconds: int = 30) -> ExecutionWatchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = ExecutionWatchdog(timeout_seconds=timeout_seconds)
    else:
        # Update timeout if requested and different
        if _watchdog._timeout != timeout_seconds:
             _watchdog._timeout = timeout_seconds
    return _watchdog
