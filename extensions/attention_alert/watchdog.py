import threading
import time
import logging

logger = logging.getLogger(__name__)

class ExecutionWatchdog:
    """Monitors the execution thread and calls a callback if no heartbeat is received.
    
    Fires REPEATEDLY every timeout_seconds while stalled, not just once.
    Any MCP tool call should act as a heartbeat via the server wrapper.
    """

    def __init__(self, timeout_seconds: int = 5, on_stall_callback=None, repeat_interval_seconds: int = 60):
        self._timeout = timeout_seconds
        self._repeat_interval = repeat_interval_seconds
        self._on_stall_callback = on_stall_callback
        self._last_heartbeat = time.monotonic()
        self._last_alert_time = 0.0  # Track when we last fired an alert
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread = None

    def start(self):
        """Start the background watchdog thread in ACTIVE state.
        
        The watchdog begins active so it can fire stall alerts
        even before the agent calls any tool for the first time.
        """
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._pause_event.set()  # Start PAUSED — only activate after first tool call
            self._thread = threading.Thread(target=self._watch, daemon=True, name="ExecutionWatchdog")
            self._last_heartbeat = time.monotonic()
            self._last_alert_time = 0.0
            self._thread.start()
            logger.info(f"Watchdog started PAUSED (timeout: {self._timeout}s, waiting for first tool call)")

    def stop(self):
        """Stop the watchdog thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def heartbeat(self):
        """Reset the stall timer. Called automatically on every MCP tool invocation.
        Also unpauses the watchdog if it was paused (e.g. on startup).
        """
        self._last_heartbeat = time.monotonic()
        self._last_alert_time = 0.0  # Reset alert throttle so next stall fires immediately
        # Unpause if paused — agent is active, start monitoring
        if self._pause_event.is_set():
            self._pause_event.clear()
            logger.info("Watchdog activated by tool call.")
        logger.debug("Watchdog heartbeat received.")

    def pause(self):
        """Pause the watchdog timer."""
        self._pause_event.set()
        logger.debug("Watchdog paused.")

    def resume(self):
        """Resume the watchdog timer and reset the heartbeat."""
        if self._pause_event.is_set():
            self._pause_event.clear()
            self._last_heartbeat = time.monotonic()
            self._last_alert_time = 0.0
            logger.debug("Watchdog resumed.")

    def _watch(self):
        """Background loop that checks for heartbeats and fires REPEATED alerts."""
        # Use a shorter sleep for snappier detection
        poll_interval = min(2.0, self._timeout / 3)
        
        while not self._stop_event.is_set():
            time.sleep(poll_interval)
            
            if self._pause_event.is_set():
                continue
                
            elapsed_since_heartbeat = time.monotonic() - self._last_heartbeat
            elapsed_since_alert = time.monotonic() - self._last_alert_time
            
            # First alert: after timeout_seconds. Subsequent alerts: every repeat_interval_seconds
            is_first_alert = self._last_alert_time == 0.0
            throttle = self._timeout if is_first_alert else self._repeat_interval
            if elapsed_since_heartbeat > self._timeout and elapsed_since_alert > throttle:
                logger.warning(f"Stall detected! No heartbeat for {elapsed_since_heartbeat:.1f}s")
                self._last_alert_time = time.monotonic()
                if self._on_stall_callback:
                    try:
                        self._on_stall_callback()
                    except Exception as e:
                        logger.error(f"Error in stall callback: {e}")


# Global watchdog instance
_watchdog = None

def get_watchdog(timeout_seconds: int = 5) -> ExecutionWatchdog:
    global _watchdog
    if _watchdog is None:
        _watchdog = ExecutionWatchdog(timeout_seconds=timeout_seconds)
    else:
        if _watchdog._timeout != timeout_seconds:
             _watchdog._timeout = timeout_seconds
    return _watchdog
