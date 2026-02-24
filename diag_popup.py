"""
Quick diagnostic:
1. Check which python / pythonw is available
2. Verify the popup script exists and runs
3. Try to launch it directly
"""
import sys, os, shutil, subprocess, platform, tempfile

print("=== Python Interpreter Info ===")
print(f"  sys.executable : {sys.executable}")
parent = os.path.dirname(sys.executable)
pythonw = os.path.join(parent, "pythonw.exe")
print(f"  pythonw.exe    : exists={os.path.isfile(pythonw)} -> {pythonw}")
print(f"  shutil.which('pythonw') : {shutil.which('pythonw')}")
print(f"  shutil.which('python')  : {shutil.which('python')}")
print(f"  platform.system()       : {platform.system()}")

# Check the popup script
popup_script = os.path.join(tempfile.gettempdir(), "antigravity_popup_script.pyw")
print(f"\n=== Popup Script ===")
print(f"  Path   : {popup_script}")
print(f"  Exists : {os.path.isfile(popup_script)}")
if os.path.isfile(popup_script):
    with open(popup_script, "r") as f:
        content = f.read()
    print(f"  Size   : {len(content)} chars")
    print(f"  First line: {content.splitlines()[0] if content else 'EMPTY'}")

# Try to launch the popup script manually with python.exe (NOT pythonw)
# so we can see any errors in the console
print("\n=== Launching popup with python.exe (console visible) ===")
exe = sys.executable
cmd = [exe, popup_script, "Test Title", "Test message from diagnostic", "0", "info"]
print(f"  Command: {cmd}")
print("  Launching...")
try:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait briefly for errors
    import time
    time.sleep(2.0)
    rc = proc.poll()
    if rc is None:
        print(f"  Process still running (pid={proc.pid}) — popup should be visible!")
        print("  (Close the popup manually to continue)")
        stdout, stderr = proc.communicate(timeout=30)
    else:
        stdout, stderr = proc.communicate()
    
    print(f"  Exit code: {proc.returncode}")
    if stderr:
        print(f"  STDERR: {stderr.decode(errors='replace')}")
    if stdout:
        print(f"  STDOUT: {stdout.decode(errors='replace')}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\nDone.")
