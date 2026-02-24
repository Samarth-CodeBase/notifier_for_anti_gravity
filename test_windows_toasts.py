from windows_toasts import Toast, WindowsToaster
import traceback

print("Testing windows-toasts notification...")
try:
    toaster = WindowsToaster("AntiGravity Agent")
    newToast = Toast()
    newToast.text_fields = ["Test Title", "Test Message"]
    toaster.show_toast(newToast)
    print("Notification call completed.")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
