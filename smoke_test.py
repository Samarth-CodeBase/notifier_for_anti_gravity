import time
import sys
import logging
from extensions.attention_alert.event_bus import get_global_bus
from extensions.attention_alert.models import AgentEvent
from extensions.attention_alert import init

logging.basicConfig(level=logging.DEBUG)

def run_smoke_test():
    print("Initializing Attention Alert Extention...")
    init()
    
    bus = get_global_bus()
    
    print("\n--- Sending 'awaiting_confirmation' event ---")
    bus.publish(AgentEvent(
        type="awaiting_confirmation",
        source="smoke_test",
        payload={"msg": "User approval needed"},
        timestamp=time.monotonic(),
        severity="warning"
    ))
    
    print("\nSleeping for 2 seconds to allow audio/desktop backends to fire...")
    time.sleep(2)
    
    print("\n--- Sending 'awaiting_confirmation' event AGAIN (should suppress) ---")
    # This should be suppressed by the Deduplicator
    bus.publish(AgentEvent(
        type="awaiting_confirmation",
        source="smoke_test",
        payload={"msg": "User approval needed"},
        timestamp=time.monotonic(),
        severity="warning"
    ))
    
    print("\nSleeping for 2 seconds...")
    time.sleep(2)

    print("\n--- Sending 'execution_running' event (should reset deduplicator) ---")
    bus.publish(AgentEvent(
        type="execution_running",
        source="smoke_test",
        payload={"msg": "User approved, running."},
        timestamp=time.monotonic(),
        severity="info"
    ))

    print("\n--- Sending 'awaiting_confirmation' event AFTER recovery (should FIRE) ---")
    bus.publish(AgentEvent(
        type="awaiting_confirmation",
        source="smoke_test",
        payload={"msg": "User approval needed"},
        timestamp=time.monotonic(),
        severity="warning"
    ))

    print("\nSleeping for 2 seconds to allow audio/desktop backends to fire...")
    time.sleep(2)
    
    print("\nSmoke test complete. Check console output, audible beep, and desktop notification.")

if __name__ == "__main__":
    run_smoke_test()
