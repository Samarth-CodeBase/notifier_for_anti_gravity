import queue
import logging
from typing import Callable, List
from .models import AgentEvent

logger = logging.getLogger(__name__)

class EventBus:
    """Thread-safe event bus for publishing and subscribing to AgentEvents."""

    def __init__(self, maxsize: int = 100):
        # Bounded queue to prevent unbounded memory growth if consumers are slow
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._subscribers: List[Callable[[AgentEvent], None]] = []

    def subscribe(self, callback: Callable[[AgentEvent], None]):
        """Register a callback to receive events."""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AgentEvent], None]):
        """Remove a previously registered callback."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, event: AgentEvent):
        """Publish an event to all subscribers sequentially.
        
        This executes the callbacks synchronously on the publishing thread.
        For true asynchronous decoupling, subscribers should hand off work
        to their own threads.
        """
        try:
            # We don't actually put it in the queue for processing by a worker 
            # thread in this simple design so that the bus is just a router.
            # If we wanted full async decoupling, we'd have a worker thread loop.
            # For this extension, we dispatch immediately to handlers, which are 
            # expected to be fast (mostly writing to DB or spawning threads).
            for subscriber in self._subscribers:
                try:
                    subscriber(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber {subscriber.__name__}: {e}", exc_info=True)
        except queue.Full:
             # This branch is unused in the sync-dispatch version but kept for
             # architectural parity with the bounded queue concept.
             logger.warning("Event bus queue full, dropping event")

# Global singleton instance
_global_bus = None

def get_global_bus() -> EventBus:
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus
