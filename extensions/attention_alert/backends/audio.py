import os
import platform
import threading
import logging
from . import AlertBackend

logger = logging.getLogger(__name__)

class AudioBackend(AlertBackend):
    """Plays an audio alert using the OS native sound system."""

    def __init__(self, config: dict = None):
        self._config = config or {}
        # We don't need any complex setup here, just check enablement.
        self._enabled = self._config.get("enabled", True)

    def dispatch(self, title: str, message: str) -> bool:
        if not self._enabled:
            return False

        return self._play_sound()

    def _play_sound(self) -> bool:
        """Play sound based on the operating system."""
        try:
            sys_platform = platform.system()
            if sys_platform == "Windows":
                import winsound
                # SND_ASYNC: non-blocking at OS level but stays in-process
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
                logger.info("Audio alert dispatched (SystemExclamation)")
                return True

            elif sys_platform == "Darwin":
                os.system("afplay /System/Library/Sounds/Glass.aiff")
                return True

            else:
                if os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga > /dev/null 2>&1") != 0:
                    os.system("beep > /dev/null 2>&1")
                return True
        except Exception as e:
            logger.error(f"Failed to play audio alert: {e}")
            return False
