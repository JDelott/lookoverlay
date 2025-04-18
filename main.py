import os

os.environ["TK_SILENCE_DEPRECATION"] = "1"

import tkinter as tk
from datetime import datetime
from mss import mss
import time
import sys
from PIL import Image
from PIL import ImageGrab


class TransparentCaptureWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Capture")

        # Check for screen recording permission
        try:
            with mss() as sct:
                test = sct.grab(sct.monitors[0])
                print("Screen recording permission granted")
        except Exception as e:
            print("Screen recording permission needed")
            popup = tk.Toplevel(self.root)
            popup.title("Permission Required")
            msg = """
Screen recording permission is required.

Please follow these steps:
1. Open System Settings
2. Go to Privacy & Security
3. Scroll to Screen Recording
4. Enable permission for Terminal or VS Code
5. Restart the application
            """
            label = tk.Label(popup, text=msg, padx=20, pady=20)
            label.pack()
            button = tk.Button(popup, text="OK", command=popup.destroy)
            button.pack(pady=10)

        # Create screenshots directory at startup
        try:
            os.makedirs("screenshots", exist_ok=True)
            print(f"Screenshots will be saved to: {os.path.abspath('screenshots')}")
        except Exception as e:
            print(f"Error creating screenshots directory: {e}")

        # Make window transparent and set minimum size
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.minsize(300, 200)

        # Bind Escape key to quit
        self.root.bind("<Escape>", lambda e: self.quit_app())

        # Create main container with padding
        self.container = tk.Frame(
            self.root,
            padx=10,
            pady=10,
        )
        self.container.pack(fill="both", expand=True)

        # Create capture frame with visible styling
        self.frame = tk.Frame(
            self.container,
            highlightbackground="#FF0000",
            highlightthickness=3,
            relief="ridge",
            borderwidth=2,
            bg="#202020",
        )
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create button container
        self.button_frame = tk.Frame(self.container)
        self.button_frame.pack(side="bottom", pady=10)

        # Add capture button
        self.capture_btn = tk.Button(
            self.button_frame,
            text="Capture",
            command=self.capture_screen,
            bg="#404040",
            fg="white",
            relief="raised",
            padx=20,
            pady=5,
            font=("Arial", 12, "bold"),
        )
        self.capture_btn.pack(side="left", padx=5)

        # Add quit button
        self.quit_btn = tk.Button(
            self.button_frame,
            text="Quit",
            command=self.quit_app,
            bg="#404040",
            fg="white",
            relief="raised",
            padx=20,
            pady=5,
            font=("Arial", 12, "bold"),
        )
        self.quit_btn.pack(side="left", padx=5)

        # Add a label to show it's draggable
        self.drag_label = tk.Label(
            self.frame,
            text="← Drag to move → (ESC to quit)",
            bg="#202020",
            fg="#808080",
            font=("Arial", 10),
        )
        self.drag_label.pack(pady=20)

        # Initialize screen capture
        self.sct = mss()

        # Initialize position variables
        self.x = 0
        self.y = 0

        # Bind mouse events for dragging
        self.frame.bind("<Button-1>", self.start_move)
        self.frame.bind("<B1-Motion>", self.on_move)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def capture_screen(self):
        try:
            print("\nStarting new capture process...")

            # Ensure screenshots directory exists
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            print("Screenshots directory confirmed")

            # Get window position and size
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            width = self.root.winfo_width()
            height = self.root.winfo_height()

            print(f"Capture area: x={x}, y={y}, width={width}, height={height}")

            # Withdraw window instead of changing alpha
            print("Hiding window...")
            self.root.withdraw()  # This hides the window completely
            self.root.update()

            try:
                # Take the screenshot
                print("Initializing screenshot capture...")
                with mss() as sct:
                    # Adjust for macOS menu bar height
                    monitor = {
                        "top": y + 25,  # Adjust for menu bar
                        "left": x,
                        "width": width,
                        "height": height - 25,  # Adjust height accordingly
                    }
                    print(f"Monitor settings: {monitor}")

                    # Capture and get raw pixels
                    print("Taking screenshot...")
                    screenshot = sct.grab(monitor)
                    print("Screenshot captured")

                    # Create filename with full path
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"screen_{timestamp}.png"
                    filepath = os.path.join(screenshots_dir, filename)

                    print(f"Attempting to save to: {filepath}")

                    # Save using PIL
                    print("Converting to PIL Image...")
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    print("Saving image...")
                    img.save(filepath)

                    if os.path.exists(filepath):
                        print(f"Screenshot saved successfully to: {filepath}")
                        # Visual feedback
                        self.frame.configure(bg="green")
                        self.root.after(200, lambda: self.frame.configure(bg="#202020"))
                    else:
                        print("Failed to save screenshot - file not created")

            finally:
                # Show window again
                print("Restoring window...")
                self.root.deiconify()  # This brings the window back
                self.root.attributes("-alpha", 0.3)  # Restore transparency
                self.root.update()

        except Exception as e:
            print(f"Error during capture: {str(e)}")
            import traceback

            traceback.print_exc()

    def quit_app(self):
        self.root.quit()
        self.root.destroy()
        sys.exit()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TransparentCaptureWindow()
    app.run()
