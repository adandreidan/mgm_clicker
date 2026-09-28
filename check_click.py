"""Click-registration check (README step 6).

Moves to the center of one configured button and clicks it once, so you
can confirm the game reacts before starting a long run.

    python3 check_click.py rock
"""

import argparse

import pyautogui
from humancursor import SystemCursor

import config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("button", choices=sorted(config.BUTTONS))
    args = parser.parse_args()

    pyautogui.FAILSAFE = True
    x, y = config.BUTTONS[args.button]["center"]
    SystemCursor().move_to([x, y])
    pyautogui.click(x, y)
    print(f"Clicked {args.button} at ({x}, {y}). Check that the game registered it.")


if __name__ == "__main__":
    main()
