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
        self._use_tkinter = False
        self._plyer = None
        
        sys_platform = platform.system()
        
        if sys_platform == "Windows":
            try:
                import tkinter as tk
                self._tk = tk
                self._use_tkinter = True
            except ImportError:
                logger.warning("tkinter not installed, falling back to plyer on Windows.")
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

        if self._use_tkinter:
            # Tkinter uses subprocess.Popen internally, which is already non-blocking.
            # No need for a daemon thread, which might die before Popen completes.
            self._show_tkinter_toast(title, message)
        elif self._plyer is not None:
            # Run in a daemon thread because plyer notifications can sometimes block
            threading.Thread(
                target=self._show_plyer_notification,
                args=(title, message),
                daemon=True
            ).start()
            
        return True

    def _show_notification(self, title: str, message: str):
        if self._use_tkinter:
            self._show_tkinter_toast(title, message)
        elif self._plyer is not None:
            self._show_plyer_notification(title, message)

    def _show_tkinter_toast(self, title: str, message: str, duration_ms: int = 5000):
        try:
            import sys
            import os
            import tempfile
            from ..subprocess_patch import _ORIGINAL_POPEN
            
            # Write the toast script to a temp file to avoid shell escaping issues
            script_content = f'''import tkinter as tk
import os

title = {repr(title)}
message = {repr(message)}
duration_ms = {duration_ms}

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

# Modern UI Colors - High Visibility Alert
bg_color = "#FF4B4B" # Vibrant red/coral
fg_color = "#FFFFFF" # White text
border_color = "#B33030" # Darker red border

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = 380
window_height = 90

x_pos = screen_width - window_width - 30
y_pos = screen_height - window_height - 70

root.geometry(f"{{window_width}}x{{window_height}}+{{x_pos}}+{{y_pos}}")
root.configure(bg=border_color) # The root acts as a border

# Inner frame for padding
inner_frame = tk.Frame(root, bg=bg_color, highlightthickness=0)
# Add a 2px margin around the edges so the root color shows through as a border
inner_frame.pack(fill="both", expand=True, padx=2, pady=2)

# Left side indicator stripe (like many modern notifications)
stripe = tk.Frame(inner_frame, bg="#FFFFFF", width=6)
stripe.pack(side="left", fill="y")

# Content container
content = tk.Frame(inner_frame, bg=bg_color)
content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# Icon (text based since we don't have images guaranteed)
icon_label = tk.Label(content, text="\u26A0", font=("Segoe UI Emoji", 24), bg=bg_color, fg=fg_color)
icon_label.pack(side="left", padx=(0,10))

# Text container
text_frame = tk.Frame(content, bg=bg_color)
text_frame.pack(side="left", fill="both", expand=True)

lbl_title = tk.Label(text_frame, text=title.upper(), font=("Segoe UI", 11, "bold"), bg=bg_color, fg=fg_color, anchor="w")
lbl_title.pack(fill="x", pady=(0, 2))

lbl_msg = tk.Label(text_frame, text=message, font=("Segoe UI", 10), bg=bg_color, fg="#FFE0E0", anchor="nw", justify="left", wraplength=window_width-90)
lbl_msg.pack(fill="both", expand=True)

current_x = screen_width

def slide_in():
    global current_x
    if current_x > x_pos:
        current_x -= 30
        if current_x < x_pos:
            current_x = x_pos
        root.geometry(f"{{window_width}}x{{window_height}}+{{current_x}}+{{y_pos}}")
        root.after(15, slide_in)
        
def slide_out():
    global current_x
    if current_x < screen_width:
        current_x += 30
        root.geometry(f"{{window_width}}x{{window_height}}+{{current_x}}+{{y_pos}}")
        root.after(15, slide_out)
    else:
        root.destroy()
        try:
            os.unlink(__file__)
        except Exception:
            pass

def schedule_cleanup():
    slide_out()

root.geometry(f"{{window_width}}x{{window_height}}+{{current_x}}+{{y_pos}}")
slide_in()

root.after(duration_ms, schedule_cleanup)
root.mainloop()
'''
            # Write to a temp .pyw file
            fd, script_path = tempfile.mkstemp(suffix=".pyw", prefix="ag_toast_")
            with os.fdopen(fd, "w") as f:
                f.write(script_content)
            
            # Use pythonw.exe for windowless execution
            exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(exe):
                exe = sys.executable
            
            CREATE_NO_WINDOW = 0x08000000
            
            logger.debug(f"Spawning tkinter toast with cmd: {[exe, script_path]}")
            # Use the ORIGINAL unpatched Popen to avoid ObservablePopen interference
            proc = _ORIGINAL_POPEN(
                [exe, script_path],
                creationflags=CREATE_NO_WINDOW
            )
            logger.debug(f"Successfully spawned tkinter toast with PID: {proc.pid}")
        except Exception as e:
            logger.error(f"Failed to spawn custom tkinter toast: {e}")

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
