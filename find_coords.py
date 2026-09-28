"""Coordinate finder: hover over each button and read its position here.

Run this, then move your mouse over the rock/paper/scissors buttons in
turn (no need to click). The live x,y prints continuously; Ctrl+C to stop.
Copy the values into config.py's BUTTONS dict.

Do this AFTER arranging your browser/game window exactly how it'll sit
for the whole soak-test session -- see the note in config.py about window
size, position, and zoom level affecting these coordinates.
"""

import time

import pyautogui


def main():
    width, height = pyautogui.size()
    print(f"Screen size: {width}x{height} -> SCREEN_MAX = ({width - 1}, {height - 1})")
    print("Hover over each button; position prints below. Ctrl+C to stop.\n")
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rx={x:5d}  y={y:5d}", end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
