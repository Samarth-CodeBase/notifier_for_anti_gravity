import threading
import time
import logging

logger = logging.getLogger(__name__)

class ExecutionWatchdog:
    """Monitors the execution thread and calls a callback if no heartbeat is received."""

    def __init__(self, timeout_seconds: int = 30, on_stall_callback = None):
        self._timeout = timeout_seconds
        self._on_stall_callback = on_stall_callback
        self._last_heartbeat = time.monotonic()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = None
        self._stalled = False

    def start(self):
        """Start the background watchdog thread in PAUSED state.
        
        The watchdog begins paused so it won't fire stall alerts
        until the agent calls pet_watchdog() for the first time.
        This prevents false alerts during server startup or reload.
        """
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._pause_event.set()  # Start PAUSED — wait for first pet_watchdog
            self._thread = threading.Thread(target=self._watch, daemon=True, name="ExecutionWatchdog")
            self._last_heartbeat = time.monotonic()
            self._stalled = False
            self._thread.start()
            logger.debug(f"Watchdog started PAUSED (timeout: {self._timeout}s)")

    def stop(self):
        """Stop the watchdog thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def heartbeat(self):
        """Reset the stall timer. Must be called repeatedly by the agent."""
        self._last_heartbeat = time.monotonic()
        
        # If we were previously stalled and just got a heartbeat, we've recovered
        if self._stalled:
            self._stalled = False
            logger.info("Watchdog detected execution recovery.")

    def pause(self):
        """Pause the watchdog timer."""
        self._pause_event.set()
        logger.debug("Watchdog paused.")

    def resume(self):
        """Resume the watchdog timer."""
        if self._pause_event.is_set():
            self._pause_event.clear()
            self._last_heartbeat = time.monotonic()
            logger.debug("Watchdog resumed.")

    def _watch(self):
        """Background loop that checks for heartbeats."""
        while not self._stop_event.is_set():
            # Sleep for a fraction of the timeout
            time.sleep(min(5.0, self._timeout / 2))
            
            if self._pause_event.is_set():
                continue
                
            elapsed = time.monotonic() - self._last_heartbeat
            if elapsed > self._timeout and not self._stalled:
                self._stalled = True
                logger.warning(f"Execution stalled! No heartbeat for {elapsed:.1f}s")
                if self._on_stall_callback:
                    try:
                        self._on_stall_callback()
                    except Exception as e:
                        logger.error(f"Error in stall callback: {e}")

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
