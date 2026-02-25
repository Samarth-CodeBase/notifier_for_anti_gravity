import logging
import sys
import os
from mcp.server.fastmcp import FastMCP
from .backends.desktop import DesktopBackend
from .backends.audio import AudioBackend
from .config import get_config
from .watchdog import ExecutionWatchdog

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("AttentionAlertServer")

# Initialize Server
mcp = FastMCP("AttentionAlertServer")

# Initialize Configuration and Notification Backends
config = get_config()
desktop_backend = DesktopBackend(config=config._data.get("backends", {}).get("desktop"))
audio_backend = AudioBackend(config=config._data.get("backends", {}).get("audio"))

def trigger_notification(message: str, urgency_level: str = "warning"):
    """
    Triggers both audio and desktop notifications.
    """
    title = f"AntiGravity Alert ({urgency_level.upper()})"
    audio_ok = audio_backend.dispatch(title, message)
    desktop_ok = desktop_backend.dispatch(title, message, urgency=urgency_level)
    logger.info(f"Notification dispatched: audio={audio_ok}, desktop={desktop_ok}")
    return f"Notification sent: {message} (Urgency: {urgency_level})"

def on_watchdog_stalled():
    """
    Callback triggered when the watchdog detects a stall.
    """
    logger.warning("Watchdog stall detected. Triggering alert.")
    trigger_notification("I am waiting for your input!", "stalled")

# Initialize the Watchdog
watchdog = ExecutionWatchdog(
    timeout_seconds=config.stall_timeout_seconds,
    on_stall_callback=on_watchdog_stalled
)

@mcp.tool()
def notify_user(message: str, urgency_level: str = "info") -> str:
    """
    Send a desktop and audio notification to the user.
    Use this when you explicitly need the user's attention.
    
    Args:
        message: The alert message to display to the user.
        urgency_level: The urgency of the alert (e.g., info, warning, critical).
    """
    # Every tool call is a heartbeat — agent is alive and working
    watchdog.heartbeat()
    return trigger_notification(message, urgency_level)

@mcp.tool()
def pet_watchdog() -> str:
    """
    Reset the stall timer.
    Call this tool regularly during long-running tasks to signal that you are not stalled.
    """
    watchdog.heartbeat()
    return "Watchdog timer reset."

def main():
    # Start the background watchdog thread before running the server
    watchdog.start()
    try:
        mcp.run()
    finally:
        # Cleanly stop the watchdog thread so the process can exit
        watchdog.stop()

if __name__ == "__main__":
    main()
