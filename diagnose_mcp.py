"""
Diagnostic script to test attention-alert-mcp backends directly.
Run with: python diagnose_mcp.py
"""
import sys
import os
import subprocess
import platform
import time

print("=" * 60)
print("ATTENTION-ALERT-MCP DIAGNOSTIC")
print("=" * 60)
print(f"Python executable: {sys.executable}")
print(f"Platform: {platform.system()}")
print(f"CWD: {os.getcwd()}")
print()

# --- Test 1: winsound directly ---
print("[TEST 1] Direct winsound test...")
try:
    import winsound
    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
    print("  RESULT: winsound.PlaySound completed (did you hear it?)")
except Exception as e:
    print(f"  RESULT: FAILED - {e}")
print()

time.sleep(1)

# --- Test 2: Audio backend via class ---
print("[TEST 2] AudioBackend.dispatch() test...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from extensions.attention_alert.backends.audio import AudioBackend
    ab = AudioBackend()
    result = ab.dispatch("Test Title", "Test Message")
    print(f"  dispatch returned: {result}")
    print("  Waiting 3s for daemon thread to finish...")
    time.sleep(3)
    print("  RESULT: dispatch completed (did you hear it?)")
except Exception as e:
    print(f"  RESULT: FAILED - {e}")
    import traceback
    traceback.print_exc()
print()

# --- Test 3: Tkinter popup subprocess ---
print("[TEST 3] Tkinter popup subprocess test...")
try:
    popup_script = r'''
import tkinter as tk
import sys

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.95)

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
root.geometry(f"370x90+{sw - 390}+{sh - 150}")
root.configure(bg="#1a1a2e")

tk.Label(root, text="DIAGNOSTIC TEST", font=("Segoe UI", 11, "bold"),
         bg="#1a1a2e", fg="#4cc9f0").pack(fill="x", padx=10, pady=5)
tk.Label(root, text="If you see this popup, desktop backend works!",
         font=("Segoe UI", 10), bg="#1a1a2e", fg="#e0e0e0").pack(fill="x", padx=10)

root.after(5000, root.destroy)
root.mainloop()
'''
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        [sys.executable, "-c", popup_script],
        **kwargs,
    )
    stdout, stderr = proc.communicate(timeout=10)
    print(f"  Return code: {proc.returncode}")
    if stderr:
        print(f"  Stderr: {stderr.decode(errors='replace')}")
    else:
        print("  Stderr: (empty)")
    print("  RESULT: subprocess completed (did you see the popup?)")
except Exception as e:
    print(f"  RESULT: FAILED - {e}")
    import traceback
    traceback.print_exc()
print()

# --- Test 4: DesktopBackend.dispatch() test ---
print("[TEST 4] DesktopBackend.dispatch() test...")
try:
    from extensions.attention_alert.backends.desktop import DesktopBackend
    db = DesktopBackend()
    result = db.dispatch("Diagnostic Alert", "Testing desktop backend!", urgency="warning")
    print(f"  dispatch returned: {result}")
    print("  Waiting 8s for popup to show and close...")
    time.sleep(8)
    print("  RESULT: dispatch completed (did you see the amber popup?)")
except Exception as e:
    print(f"  RESULT: FAILED - {e}")
    import traceback
    traceback.print_exc()
print()

# --- Test 5: Full trigger_notification (simulating MCP tool) ---
print("[TEST 5] Full trigger_notification (simulates MCP notify_user call)...")
try:
    from extensions.attention_alert.server import trigger_notification
    result = trigger_notification("Full MCP test! Sound + popup expected.", "critical")
    print(f"  trigger_notification returned: {result}")
    print("  Waiting 8s...")
    time.sleep(8)
    print("  RESULT: Did you hear sound AND see a red popup?")
except Exception as e:
    print(f"  RESULT: FAILED - {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
