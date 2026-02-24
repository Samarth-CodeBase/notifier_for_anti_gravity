import platform
import subprocess
import sys
import os
import shutil
import tempfile
import threading
import logging
from . import AlertBackend

logger = logging.getLogger(__name__)

import platform
import subprocess
import sys
import os
import shutil
import tempfile
import threading
import logging
from . import AlertBackend

logger = logging.getLogger(__name__)

# Fallback basic text or command options if needed for other platforms
# For Windows, we will rely on windows-toasts.

class DesktopBackend(AlertBackend):
    """Displays a desktop popup using native toast notifications (on Windows) or fallback methods."""

    def __init__(self, config: dict = None):
        self._config = config or {}
        self._enabled = self._config.get("enabled", True)
        self._duration_ms = self._config.get("duration_ms", 7000)
        self._platform = platform.system()
        
        if self._platform == "Windows":
            self._has_windows_toasts = True # Reused flag to signify we can do Windows notifications via Tkinter
            logger.info("DesktopBackend initialized for Windows (using Tkinter popup).")
        else:
            self._has_windows_toasts = False
            logger.info(f"DesktopBackend initialized for non-Windows platform: {self._platform}")

    def dispatch(self, title: str, message: str, urgency: str = "info") -> bool:
        if not self._enabled:
            return False

        # Fire and forget in a background thread to prevent blocking
        threading.Thread(
            target=self._show_popup,
            args=(title, message, urgency),
            daemon=True
        ).start()
        return True

    def _show_popup(self, title: str, message: str, urgency: str):
        """Show the desktop notification using the best available method for the OS."""
        try:
            if self._platform == "Windows":
                self._show_windows_toast(title, message, urgency)
            elif self._platform == "Darwin":
                self._show_mac_notification(title, message)
            else:
                self._show_linux_notification(title, message, urgency)
        except Exception as e:
            logger.error(f"Failed to dispatch desktop notification: {e}", exc_info=True)

    def _show_windows_toast(self, title: str, message: str, urgency: str):
        """Show a standalone Tkinter popup notification on Windows."""
        try:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "popup_ui.py")
            kwargs = {}
            if platform.system() == "Windows":
                # DETACHED_PROCESS (0x00000008) ensures the child process is not attached to 
                # the console of the parent. CREATE_NEW_PROCESS_GROUP (0x00000200) creates
                # a new process group. Together with CREATE_NO_WINDOW (0x08000000) this prevents
                # the child from dying if the parent restarts or loses its console.
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | 0x00000008 | 0x00000200
                
            # Redirect streams to DEVNULL so no broken pipe errors occur on parent exit
            subprocess.Popen(
                [sys.executable, script_path, title, message, urgency], 
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                **kwargs
            )
            logger.info("Dispatched Tkinter popup on Windows (Detached).")
        except Exception as e:
            logger.error(f"Failed to show Tkinter popup: {e}")

    def _show_mac_notification(self, title: str, message: str):
        """Show a macOS notification using osascript."""
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], check=False)

    def _show_linux_notification(self, title: str, message: str, urgency: str):
        """Show a Linux notification using notify-send."""
        if shutil.which("notify-send"):
            urgency_map = {"info": "normal", "warning": "critical", "critical": "critical", "stalled": "critical"}
            level = urgency_map.get(urgency, "normal")
            cmd = ["notify-send", "-u", level, "-t", str(self._duration_ms), title, message]
            subprocess.run(cmd, check=False)
        else:
            logger.warning("notify-send not found, cannot show Linux notification")

