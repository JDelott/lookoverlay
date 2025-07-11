import os
from dotenv import load_dotenv
import anthropic
from PIL import Image
import io
import base64

# Load environment variables from .env file
load_dotenv()

os.environ["TK_SILENCE_DEPRECATION"] = "1"

import tkinter as tk
from datetime import datetime
from mss import mss
import time
import sys
from PIL import ImageGrab
import tkinter.ttk as ttk


class TransparentCaptureWindow:
    def __init__(self):
        # Initialize root window
        self.root = tk.Tk()
        self.root.title("Screen Capture")

        # Check for API key
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not found in .env file")
            popup = tk.Toplevel(self.root)
            popup.title("API Key Required")
            msg = """
Anthropic API key is required.

Please:
1. Create a .env file in the project directory
2. Add your API key: ANTHROPIC_API_KEY=your-key-here
3. Restart the application
            """
            label = tk.Label(popup, text=msg, padx=20, pady=20)
            label.pack()
            button = tk.Button(popup, text="OK", command=popup.destroy)
            button.pack(pady=10)
        else:
            # Initialize Claude client
            self.claude = anthropic.Anthropic(api_key=self.api_key)

        # Set window attributes for visibility
        self.root.attributes("-alpha", 0.8)  # Less transparent for better visibility
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#2C2C2C")  # Dark background for contrast

        # Create a container frame with a visible border
        self.container = tk.Frame(
            self.root,
            bg="#FF5500",  # Bright orange border
            padx=5,
            pady=5,
        )
        self.container.pack(fill="both", expand=True)

        # Create the main frame inside the container
        self.frame = tk.Frame(
            self.container,
            bg="#202020",
            relief="ridge",
            borderwidth=2,
        )
        self.frame.pack(fill="both", expand=True)

        # Add the draggable label
        self.drag_label = tk.Label(
            self.frame,
            text="← Drag to move → (ESC to quit)",
            bg="#202020",
            fg="#FFFFFF",
            font=("Arial", 12, "bold"),
        )
        self.drag_label.pack(pady=20)

        # Create button container
        self.button_frame = tk.Frame(
            self.frame,
            bg="#202020",
        )
        self.button_frame.pack(side="bottom", pady=10)

        # Button styling
        button_style = {
            "bg": "#FF5500",  # Match border color
            "fg": "white",
            "relief": "raised",
            "padx": 20,
            "pady": 5,
            "font": ("Arial", 12, "bold"),
        }

        # Add capture button
        self.capture_btn = tk.Button(
            self.button_frame,
            text="Capture",
            command=self.capture_screen,
            **button_style,
        )
        self.capture_btn.pack(side="left", padx=5)

        # Add quit button
        self.quit_btn = tk.Button(
            self.button_frame,
            text="Quit",
            command=self.quit_app,
            **button_style,
        )
        self.quit_btn.pack(side="left", padx=5)

        # Initialize position variables
        self.x = 0
        self.y = 0

        # Bind mouse events for dragging
        self.frame.bind("<Button-1>", self.start_move)
        self.frame.bind("<B1-Motion>", self.on_move)

        # Bind Escape key to quit
        self.root.bind("<Escape>", lambda e: self.quit_app())

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def analyze_with_claude(self, image_path):
        if not hasattr(self, "claude"):
            print("Claude client not initialized.")
            return None

        try:
            # Open and prepare the image
            with open(image_path, "rb") as img_file:
                # Create a message with the image
                message = self.claude.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Please analyze this screenshot and describe what you see.",
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": base64.b64encode(
                                            img_file.read()
                                        ).decode(),
                                    },
                                },
                            ],
                        }
                    ],
                )

                # Get Claude's response
                response = message.content[0].text
                print("\nClaude's analysis:")
                print(response)

                return response

        except Exception as e:
            print(f"Error analyzing with Claude: {str(e)}")
            return None

    def capture_screen(self):
        try:
            print("\nStarting new capture process...")

            # Ensure screenshots directory exists
            screenshots_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)

            # Get window position and size
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            width = self.root.winfo_width()
            height = self.root.winfo_height()

            print(f"Capture area: x={x}, y={y}, width={width}, height={height}")

            # Hide window
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

                        # Add Claude analysis after successful capture
                        self.analyze_with_claude(filepath)
                    else:
                        print("Failed to save screenshot - file not created")

            finally:
                # Show window again
                print("Restoring window...")
                self.root.deiconify()  # This brings the window back
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
