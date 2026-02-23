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
            
        threading.Thread(target=self._play_sound, daemon=True).start()
        return True

    def _play_sound(self):
        """Play sound based on the operating system."""
        try:
            sys_platform = platform.system()
            if sys_platform == "Windows":
                import winsound
                # Play the default Windows notification sound asynchronously
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)

            elif sys_platform == "Darwin":
                # macOS default alert sound
                os.system("afplay /System/Library/Sounds/Glass.aiff")

            else:
                # Assuming Linux Desktop
                # paplay is for PulseAudio, aplay for ALSA
                if os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga > /dev/null 2>&1") != 0:
                    # Fallback to beep if paplay fails or isn't installed
                    os.system("beep > /dev/null 2>&1")
        except Exception as e:
            logger.error(f"Failed to play audio alert: {e}")
