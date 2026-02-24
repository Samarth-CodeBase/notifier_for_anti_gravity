import tkinter as tk
import time

def show_custom_toast(title, message, duration_ms=5000):
    root = tk.Tk()
    root.overrideredirect(True) # Remove borders
    root.attributes("-topmost", True) # Keep on top
    
    # Configure colors
    bg_color = "#2E2E2E"
    fg_color = "#FFFFFF"
    
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Window dimensions
    window_width = 350
    window_height = 80
    
    # Position: Bottom right with a small margin
    x_pos = screen_width - window_width - 20
    # Add a bit more margin from the bottom to avoid typical taskbars
    y_pos = screen_height - window_height - 60 
    
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    root.configure(bg=bg_color)
    
    # Add Title
    lbl_title = tk.Label(root, text=title, font=("Helvetica", 11, "bold"), bg=bg_color, fg=fg_color, anchor="w")
    lbl_title.pack(fill="x", padx=15, pady=(10, 2))
    
    # Add Message
    lbl_msg = tk.Label(root, text=message, font=("Helvetica", 10), bg=bg_color, fg="#CCCCCC", anchor="w", justify="left")
    lbl_msg.pack(fill="both", expand=True, padx=15, pady=(0, 10))
    
    # Auto-destroy
    root.after(duration_ms, root.destroy)
    
    print("Toast displayed, waiting for destruction...")
    root.mainloop()
    print("Toast destroyed.")

if __name__ == "__main__":
    print("Testing custom Tkinter toast...")
    show_custom_toast("AntiGravity Agent", "Your agent needs attention right now!")
