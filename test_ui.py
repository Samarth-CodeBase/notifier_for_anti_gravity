import tkinter as tk

def test_new_ui(title, message, duration_ms=5000):
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

    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
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

    lbl_title = tk.Label(text_frame, text=title.upper(), font=("Segoe UI", 12, "bold"), bg=bg_color, fg=fg_color, anchor="w")
    lbl_title.pack(fill="x", pady=(0, 2))
    
    lbl_msg = tk.Label(text_frame, text=message, font=("Segoe UI", 10), bg=bg_color, fg="#FFE0E0", anchor="nw", justify="left")
    lbl_msg.pack(fill="both", expand=True)

    # Slide-in animation
    current_x = screen_width
    def slide_in():
        nonlocal current_x
        if current_x > x_pos:
            current_x -= 30
            # Ensure we don't overshoot
            if current_x < x_pos:
                current_x = x_pos
            root.geometry(f"{window_width}x{window_height}+{current_x}+{y_pos}")
            root.after(10, slide_in)
            
    # Slide-out animation
    def slide_out():
        nonlocal current_x
        if current_x < screen_width:
            current_x += 30
            root.geometry(f"{window_width}x{window_height}+{current_x}+{y_pos}")
            root.after(10, slide_out)
        else:
            root.destroy()

    def schedule_cleanup():
        slide_out()

    root.geometry(f"{window_width}x{window_height}+{current_x}+{y_pos}")
    slide_in()
    
    root.after(duration_ms, schedule_cleanup)
    root.mainloop()

if __name__ == "__main__":
    test_new_ui("Attention Required", "Your AI Agent is waiting for your input to continue execution.", 5000)
