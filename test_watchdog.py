import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extensions.attention_alert.watchdog import get_watchdog
from extensions.attention_alert.server import trigger_notification

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")

stall_triggered = False

def alert_callback():
    global stall_triggered
    stall_triggered = True
    print("[TEST] Watchdog stalled! Callback fired.")
    trigger_notification("Test watchdog timeout! Click Acknowledge.", "critical")

print("Initializing watchdog with 3s timeout for testing...")
wd = get_watchdog(timeout_seconds=3)
wd._on_stall_callback = alert_callback
wd.start()

print("1. Letting watchdog run with heartbeats for 4 seconds...")
for i in range(4):
    wd.heartbeat()
    time.sleep(1)

if stall_triggered:
    print("FAILED: Watchdog triggered during active heartbeats!")
    sys.exit(1)
print("SUCCESS: Watchdog did not trigger during heartbeats.")

print("2. Pausing watchdog for 5 seconds (longer than timeout)...")
wd.pause()
time.sleep(5)

if stall_triggered:
    print("FAILED: Watchdog triggered while paused!")
    sys.exit(1)
print("SUCCESS: Watchdog did not trigger while paused.")

print("3. Resuming watchdog and waiting for stall (6s)...")
wd.resume()
for i in range(6):
    print(f"   waiting... {i+1}s")
    time.sleep(1)

if not stall_triggered:
    print("FAILED: Watchdog did NOT trigger after stall time elapsed!")
    print(f"Watchdog state: stalled={wd._stalled} timeout={wd._timeout} elapsed={time.monotonic() - wd._last_heartbeat:.1f}s")
    sys.exit(1)
print("SUCCESS: Watchdog triggered properly after resume and delay.")

wd.stop()
print("All watchdog tests PASSED.")
