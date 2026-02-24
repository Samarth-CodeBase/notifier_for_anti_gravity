import sys
import tkinter as tk

def main():
    if len(sys.argv) < 3:
        print("Usage: popup_ui.py <title> <message> [urgency]")
        sys.exit(1)
        
    title = sys.argv[1]
    message = sys.argv[2]
    urgency = sys.argv[3] if len(sys.argv) > 3 else "info"

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    
    if urgency in ("critical", "stalled"):
        bg_color = "#FF4B4B"
        border_color = "#B33030"
        icon_char = "\u26A0"
    elif urgency == "warning":
        bg_color = "#FFA500"
        border_color = "#CC8400"
        icon_char = "\u26A0"
    else:
        bg_color = "#4cc9f0"
        border_color = "#3a9ac0"
        icon_char = "\u2139"

    fg_color = "#FFFFFF"
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    window_width = 400
    window_height = 120
    
    x_pos = screen_width - window_width - 30
    y_pos = screen_height - window_height - 70

    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")
    root.configure(bg=border_color)

    inner_frame = tk.Frame(root, bg=bg_color, highlightthickness=0)
    inner_frame.pack(fill="both", expand=True, padx=2, pady=2)
    
    stripe = tk.Frame(inner_frame, bg="#FFFFFF", width=6)
    stripe.pack(side="left", fill="y")
    
    content = tk.Frame(inner_frame, bg=bg_color)
    content.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    
    icon_label = tk.Label(content, text=icon_char, font=("Segoe UI Emoji", 24), bg=bg_color, fg=fg_color)
    icon_label.pack(side="left", padx=(0,10))
    
    text_frame = tk.Frame(content, bg=bg_color)
    text_frame.pack(side="left", fill="both", expand=True)

    lbl_title = tk.Label(text_frame, text=title.upper(), font=("Segoe UI", 11, "bold"), bg=bg_color, fg=fg_color, anchor="w")
    lbl_title.pack(fill="x", pady=(0, 2))
    
    lbl_msg = tk.Label(text_frame, text=message, font=("Segoe UI", 10), bg=bg_color, fg="#FFFFFF", anchor="nw", justify="left", wraplength=260)
    lbl_msg.pack(fill="both", expand=True)

    btn_frame = tk.Frame(inner_frame, bg=bg_color)
    btn_frame.pack(side="right", fill="y", padx=5, pady=5)

    current_x = screen_width
    def slide_in():
        nonlocal current_x
        if current_x > x_pos:
            current_x -= 30
            if current_x < x_pos:
                current_x = x_pos
            root.geometry(f"{window_width}x{window_height}+{current_x}+{y_pos}")
            root.after(10, slide_in)
            
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

    dismiss_btn = tk.Button(btn_frame, text="Dismiss", font=("Segoe UI", 9, "bold"), bg=border_color, fg=fg_color, bd=0, cursor="hand2", command=schedule_cleanup, padx=15, pady=8)
    dismiss_btn.pack(side="bottom", pady=5)

    root.geometry(f"{window_width}x{window_height}+{current_x}+{y_pos}")
    slide_in()
    
    # Stay indefinitely until manual close.
    root.mainloop()

if __name__ == "__main__":
    main()
