import threading
import logging
from . import AlertBackend

logger = logging.getLogger(__name__)

class DesktopBackend(AlertBackend):
    """Displays an OS-level desktop notification popup."""

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._enabled = self._config.get("enabled", True)
        
        try:
             import plyer
             self._plyer = plyer
        except ImportError:
             logger.warning("plyer not installed, desktop notifications will be disabled.")
             self._enabled = False

    def dispatch(self, title: str, message: str) -> bool:
        if not self._enabled:
            return False

        # Run in a daemon thread because plyer notifications can sometimes block
        # the calling thread on certain platforms
        threading.Thread(
            target=self._show_notification,
            args=(title, message),
            daemon=True
        ).start()
        return True

    def _show_notification(self, title: str, message: str):
        try:
            self._plyer.notification.notify(
                title=title,
                message=message,
                app_name="AntiGravity Agent",
                # The icon path must be absolute to an .ico or .png depending on OS
                # Omitted for simplicity/portability in base implementation
                timeout=10, # Disappear after 10 seconds
            )
        except Exception as e:
            logger.error(f"Failed to display desktop notification: {e}")
