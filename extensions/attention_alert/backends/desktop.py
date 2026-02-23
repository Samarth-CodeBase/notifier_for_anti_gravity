import platform
import threading
import logging
from . import AlertBackend

logger = logging.getLogger(__name__)

class DesktopBackend(AlertBackend):
    """Displays a desktop notification popup."""

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._enabled = self._config.get("enabled", True)
        self._windows_toasts = None
        self._plyer = None
        
        sys_platform = platform.system()
        
        if sys_platform == "Windows":
            try:
                import windows_toasts
                self._windows_toasts = windows_toasts
            except ImportError:
                logger.warning("windows-toasts not installed, falling back to plyer on Windows.")
                self._fallback_to_plyer()
        else:
            self._fallback_to_plyer()

    def _fallback_to_plyer(self):
        try:
             import plyer
             self._plyer = plyer
        except ImportError:
             logger.warning("plyer not installed, desktop notifications will be disabled.")
             self._enabled = False

    def dispatch(self, title: str, message: str) -> bool:
        if not self._enabled:
            return False

        # Run in a daemon thread so it doesn't block the caller
        threading.Thread(
            target=self._show_notification,
            args=(title, message),
            daemon=True
        ).start()
            
        return True

    def _show_notification(self, title: str, message: str):
        if self._windows_toasts is not None:
            self._show_windows_toast(title, message)
        elif self._plyer is not None:
            self._show_plyer_notification(title, message)

    def _show_windows_toast(self, title: str, message: str):
        try:
            toaster = self._windows_toasts.WindowsToaster("AntiGravity Agent")
            new_toast = self._windows_toasts.ToastText1()
            new_toast.SetBody(f"{title}\n{message}")
            new_toast.duration = self._windows_toasts.ToastDuration.Short
            toaster.show_toast(new_toast)
        except Exception as e:
            logger.error(f"Failed to show Windows toast: {e}")

    def _show_plyer_notification(self, title: str, message: str):
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
            logger.error(f"Failed to display desktop notification using plyer: {e}")
