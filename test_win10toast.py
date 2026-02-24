import win10toast
import traceback

print("Testing win10toast notification...")
try:
    toaster = win10toast.ToastNotifier()
    toaster.show_toast(
        title="Test Title",
        msg="Test Message",
        icon_path=None,
        duration=5,
        threaded=True
    )
    print("Notification call completed.")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
