import subprocess
import sys
import os

# 1. Check python executable paths
print(f"sys.executable: {sys.executable}")
pythonw = sys.executable.replace("python.exe", "pythonw.exe")
print(f"pythonw path: {pythonw}")
print(f"pythonw exists: {os.path.exists(pythonw)}")
print(f"python exists: {os.path.exists(sys.executable)}")

# 2. Try spawning with python.exe directly (not pythonw)
script = '''
import tkinter as tk
import sys

title = sys.argv[1]
message = sys.argv[2]
duration_ms = int(sys.argv[3])

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

bg_color = "#2E2E2E"
fg_color = "#FFFFFF"

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = 350
window_height = 80

x_pos = screen_width - window_width - 20
y_pos = screen_height - window_height - 60

root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
root.configure(bg=bg_color)

lbl_title = tk.Label(root, text=title, font=("Helvetica", 11, "bold"), bg=bg_color, fg=fg_color, anchor="w")
lbl_title.pack(fill="x", padx=15, pady=(10, 2))

lbl_msg = tk.Label(root, text=message, font=("Helvetica", 10), bg=bg_color, fg="#CCCCCC", anchor="w", justify="left")
lbl_msg.pack(fill="both", expand=True, padx=15, pady=(0, 10))

root.after(duration_ms, root.destroy)
root.mainloop()
'''

print("\n--- Test 1: Spawning with python.exe (visible console) ---")
proc = subprocess.Popen(
    [sys.executable, "-c", script, "Test Title", "Hello from subprocess!", "5000"],
)
print(f"PID: {proc.pid}")
print("Waiting for process to finish...")
ret = proc.wait()
print(f"Return code: {ret}")
