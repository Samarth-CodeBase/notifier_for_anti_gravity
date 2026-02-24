import plyer
import traceback

print("Testing plyer notification...")
try:
    plyer.notification.notify(
        title="Test Title",
        message="Test Message",
        app_name="Test App",
        timeout=10
    )
    print("Notification call completed.")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
