"""
main.py  — FreeDBC Editor & Previewer entry point.

Run directly:   python src/main.py
Or as a module: python -m src.main
"""

import os
import sys

# Make sure `src/` is always importable regardless of how we are launched
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import customtkinter as ctk
from ui.app_window import AppWindow


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    # Attempt to set a window icon (gracefully ignore if the file is missing)
    icon_path = os.path.join(os.path.dirname(_HERE), "assets", "icon.ico")
    if os.path.isfile(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception:
            pass

    AppWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
